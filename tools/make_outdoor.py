"""Bake free_pack_-_tree.glb and simple_street_light.glb into one small outdoor.glb.

Trees: palette-atlas texture sampled into vertex colours (no texture). Street light: material colours
baked into vertex colours, the ground plane dropped, pole and lamp kept as separate meshes.
Everything in metres, y-up, each object's base at the origin. The lamp arm points +z.
Usage: python make_outdoor.py <model dir> <out.glb>
"""
import io, json, struct, sys
import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]


def read_glb(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n])
    return j, b[20 + n + 8:]


def accessor(j, binc, i):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    size = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride')
    item = np.dtype(comp).itemsize * size
    if stride and stride != item:
        raw = np.frombuffer(binc, np.uint8, a['count'] * stride, off).reshape(a['count'], stride)[:, :item]
        return np.frombuffer(raw.tobytes(), comp).reshape(a['count'], size)
    return np.frombuffer(binc, comp, a['count'] * size, off).reshape(a['count'], size) if size > 1 \
        else np.frombuffer(binc, comp, a['count'], off)


def node_matrix(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=np.float64).reshape(4, 4).T
    m = np.eye(4)
    if 'scale' in n:
        m = np.diag(list(n['scale']) + [1]) @ m
    if 'rotation' in n:
        x, y, z, w = n['rotation']
        r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        rm = np.eye(4); rm[:3, :3] = r
        m = rm @ m
    if 'translation' in n:
        t = np.eye(4); t[:3, 3] = n['translation']
        m = t @ m
    return m


def walk(j):
    """Yield (node, world matrix) for every node with a mesh."""
    def rec(i, parent):
        n = j['nodes'][i]
        m = parent @ node_matrix(n)
        if 'mesh' in n:
            yield n, m
        for c in n.get('children', []):
            yield from rec(c, m)
    for r in j['scenes'][j.get('scene', 0)]['nodes']:
        yield from rec(r, np.eye(4))


def prim_data(j, binc, prim, m):
    p = accessor(j, binc, prim['attributes']['POSITION']).astype(np.float64)
    nrm = accessor(j, binc, prim['attributes']['NORMAL']).astype(np.float64)
    p = (np.c_[p, np.ones(len(p))] @ m.T)[:, :3]
    nm = np.linalg.inv(m[:3, :3]).T
    nrm = nrm @ nm.T
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    idx = accessor(j, binc, prim['indices']).astype(np.uint32) if 'indices' in prim else np.arange(len(p), dtype=np.uint32)
    if np.linalg.det(m[:3, :3]) < 0:  # mirrored: keep front faces outward
        idx = idx.reshape(-1, 3)[:, ::-1].ravel()
    return p, nrm, idx


meshes = []  # (name, pos, normal, colour rgba float 0..1, indices, material name)

# ---- trees ----
j, binc = read_glb(src + '/free_pack_-_tree.glb')
bv = j['bufferViews'][j['images'][0]['bufferView']]
img = np.asarray(Image.open(io.BytesIO(binc[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])).convert('RGB'))
H, W = img.shape[:2]
trees = []
for n, m in walk(j):
    prim = j['meshes'][n['mesh']]['primitives'][0]
    p, nrm, idx = prim_data(j, binc, prim, m)
    uv = accessor(j, binc, prim['attributes']['TEXCOORD_0']).astype(np.float64)
    px = np.clip(((uv[:, 0] % 1) * W).astype(int), 0, W - 1)
    py = np.clip(((uv[:, 1] % 1) * H).astype(int), 0, H - 1)
    srgb = img[py, px] / 255.0
    lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)  # glTF vertex colours are linear
    col = np.c_[lin, np.ones(len(p))]
    base = p[p[:, 1] < p[:, 1].min() + 0.3]
    p -= [base[:, 0].mean(), p[:, 1].min(), base[:, 2].mean()]
    trees.append((n['name'].split('_Free')[0], p, nrm, col, idx))
trees.sort(key=lambda t: t[0])
for i, (name, p, nrm, col, idx) in enumerate(trees):
    meshes.append(('Tree_%02d' % (i + 1), p, nrm, col, idx, 'Tree'))

# ---- street light ----
j, binc = read_glb(src + '/simple_street_light.glb')
parts = {'pole': [], 'lamp': []}
for n, m in walk(j):
    if n['name'].startswith('Plane'):
        continue
    prim = j['meshes'][n['mesh']]['primitives'][0]
    mat = j['materials'][prim['material']]
    p, nrm, idx = prim_data(j, binc, prim, m)
    c = mat['pbrMetallicRoughness'].get('baseColorFactor', [1, 1, 1, 1])
    col = np.tile(c, (len(p), 1))
    parts['lamp' if mat['name'] == 'Light' else 'pole'].append((p, nrm, col, idx))


def merge(lst):
    ps, ns, cs, ids, off = [], [], [], [], 0
    for p, nrm, col, idx in lst:
        ps.append(p); ns.append(nrm); cs.append(col); ids.append(idx + off); off += len(p)
    return np.vstack(ps), np.vstack(ns), np.vstack(cs), np.concatenate(ids).astype(np.uint32)


pole, lamp = merge(parts['pole']), merge(parts['lamp'])
allp = np.vstack([pole[0], lamp[0]])
y0 = allp[:, 1].min()
base = pole[0][pole[0][:, 1] < y0 + 0.3]
o = np.array([base[:, 0].mean(), y0, base[:, 2].mean()])
lc = lamp[0].mean(axis=0) - o
ang = np.arctan2(lc[0], lc[2])  # rotate about y so the lamp sits on +z
c, s_ = np.cos(-ang), np.sin(-ang)
R = np.array([[c, 0, s_], [0, 1, 0], [-s_, 0, c]])
for name, (p, nrm, col, idx) in (('StreetLight_Pole', pole), ('StreetLight_Lamp', lamp)):
    meshes.append((name, (p - o) @ R.T, nrm @ R.T, col, idx, 'Lamp' if 'Lamp' in name else 'Pole'))

# ---- write ----
mats = {'Tree': {'name': 'Tree', 'pbrMetallicRoughness': {'metallicFactor': 0, 'roughnessFactor': 0.9}, 'doubleSided': True},
        'Pole': {'name': 'Pole', 'pbrMetallicRoughness': {'metallicFactor': 0.5, 'roughnessFactor': 0.5}},
        'Lamp': {'name': 'Lamp', 'pbrMetallicRoughness': {'metallicFactor': 0, 'roughnessFactor': 0.7}, 'emissiveFactor': [1, 0.85, 0.6]}}
mat_ids = {k: i for i, k in enumerate(mats)}
g = {'asset': {'version': '2.0', 'generator': 'make_outdoor.py'}, 'scene': 0, 'scenes': [{'nodes': []}],
     'nodes': [], 'meshes': [], 'accessors': [], 'bufferViews': [], 'buffers': [], 'materials': list(mats.values())}
blob = bytearray()


def add(arr, ctype, typ, target, normalized=False, minmax=False):
    while len(blob) % 4:
        blob.append(0)
    g['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': arr.nbytes, 'target': target})
    blob.extend(arr.tobytes())
    a = {'bufferView': len(g['bufferViews']) - 1, 'componentType': ctype, 'count': len(arr), 'type': typ}
    if normalized:
        a['normalized'] = True
    if minmax:
        a['min'] = arr.min(axis=0).tolist(); a['max'] = arr.max(axis=0).tolist()
    g['accessors'].append(a)
    return len(g['accessors']) - 1


for name, p, nrm, col, idx, mat in meshes:
    attrs = {'POSITION': add(p.astype(np.float32), 5126, 'VEC3', 34962, minmax=True),
             'NORMAL': add(nrm.astype(np.float32), 5126, 'VEC3', 34962),
             'COLOR_0': add(np.round(np.clip(col, 0, 1) * 65535).astype(np.uint16), 5123, 'VEC4', 34962, normalized=True)}
    ind = add(idx.astype(np.uint16 if idx.max() < 65536 else np.uint32), 5123 if idx.max() < 65536 else 5125, 'SCALAR', 34963)
    g['meshes'].append({'name': name, 'primitives': [{'attributes': attrs, 'indices': ind, 'material': mat_ids[mat]}]})
    g['nodes'].append({'name': name, 'mesh': len(g['meshes']) - 1})
    g['scenes'][0]['nodes'].append(len(g['nodes']) - 1)
    lo, hi = p.min(axis=0), p.max(axis=0)
    print('%-18s verts %6d tris %6d  size %s' % (name, len(p), len(idx) // 3, np.round(hi - lo, 2)))
while len(blob) % 4:
    blob.append(0)
g['buffers'].append({'byteLength': len(blob)})
js = json.dumps(g, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)) + \
    struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(blob), 0x004E4942) + bytes(blob)
open(out, 'wb').write(glb)
print('wrote', out, len(glb) // 1024, 'KB')
