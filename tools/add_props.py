"""Add showcase props to xcamp-fl20.glb (run it on the original file from git).

- SLP_DG_01, smart light post (Devices_Lights): Showcase Gallery, in the gap between the east display
  counter and the end of the slat wall, its lamp head reaching out into the gallery.
- KSK_RC_01, room booking kiosk (Devices_Panels): Reception, against the west wall next to the two
  waiting chairs, a tablet on a black post facing into the room.
- Back panels: some TVs' screen boxes run through the whole TV, so the screen also shows on the back.
  A black panel (<TV>__back) is added just behind each listed screen, on the side away from the room.
- Rebuilt: PC_16 (reception monitor) sat at normal-desk height inside the 1.05 m counter, turned sideways.
  It now stands on the counter facing the receptionist's chair (+z), screen only on its front face.
- Moved: CCTV_02 (Makerspace camera 1) hung outside the Makerspace's south wall, looking into the corridor.
  It now sits in the room's south-west corner, mirroring camera 2 (CCTV_07) in the north-west one, lens into the room.
- LCK_01, locker bank (Devices_Lockers): in the corridor outside the Workshop, against its west wall, in place of
  the grey block that stood there. 3 rows of 6 doors (01-06 bottom, 13-18 top), numbered at each door's top left;
  the doors, gaps and numbers are one picture on the front (lck_01_doors).
- LCK_02, locker bank (Devices_Lockers): Makerspace, centred on its west wall facing the tables. Blue, 3 rows of
  8 doors (01-08 bottom, 17-24 top), white numbers at each door's top left.
The widget skips unknown device kinds (SLP, KSK, LCK), so they show as plain objects until it learns them.
Reuses the file's own materials. Re-running on its own output replaces them (the old bytes stay, unused).
Usage: python add_props.py <in.glb> <out.glb>
"""
import json, math, struct, sys
import numpy as np

src, out = sys.argv[1], sys.argv[2]


def box(x0, y0, z0, x1, y1, z1):
    v = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], np.float32)
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
         (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v, np.array(f, np.uint32)


def cylinder(cx, cz, r, y0, y1, n=12):
    ring = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    v = np.array([[x, y, z] for y in (y0, y1) for x, z in ring] + [[cx, y0, cz], [cx, y1, cz]], np.float32)
    f = []
    for i in range(n):
        k = (i + 1) % n
        f += [(i, n + k, k), (i, n + i, n + k), (2 * n, i, k), (2 * n + 1, n + k, n + i)]
    return v, np.array(f, np.uint32)


def pipe_x(x0, x1, y, z, r, n=12):  # a cylinder along x
    v, f = cylinder(0, 0, r, x0, x1, n)
    return v[:, [1, 0, 2]] + np.array([0, y, z], np.float32), f[:, ::-1].copy()  # swap x/y; keep faces outward


def light_post(X, Z):  # plinth centre on the floor plan (scene metres)
    TOP, HEAD_Y = 1.0, 2.2  # plinth top, underside of the lamp head
    return {
        'white': [box(X - 0.2, 0, Z - 0.2, X + 0.2, TOP, Z + 0.2)],
        'black': [box(X - 0.04, TOP, Z - 0.1, X + 0.04, TOP + 0.09, Z - 0.02)],          # gateway on the plinth
        'metal': [cylinder(X, Z - 0.08, 0.035, TOP, HEAD_Y + 0.12),                       # pole
                  box(X - 0.025, HEAD_Y + 0.06, Z - 0.08, X + 0.025, HEAD_Y + 0.12, Z + 0.4)],  # arm
        'lightgrey': [box(X - 0.14, HEAD_Y + 0.01, Z + 0.3, X + 0.14, HEAD_Y + 0.11, Z + 0.88)],  # lamp housing
        'led': [box(X - 0.11, HEAD_Y, Z + 0.34, X + 0.11, HEAD_Y + 0.01, Z + 0.84)],      # glowing underside
    }


def kiosk(X, Z):  # back of the post against the wall at X (screen faces +x), centred on Z
    return {
        'black': [box(X, 0, Z - 0.2, X + 0.32, 0.04, Z + 0.2),                    # floor frame
                  box(X + 0.06, 0.04, Z - 0.17, X + 0.1, 1.05, Z - 0.13),         # two uprights
                  box(X + 0.06, 0.04, Z + 0.13, X + 0.1, 1.05, Z + 0.17),
                  box(X + 0.065, 0.1, Z - 0.13, X + 0.085, 1.05, Z + 0.13),      # panel between them
                  box(X + 0.085, 0.55, Z - 0.03, X + 0.11, 0.62, Z + 0.03),      # card reader
                  box(X + 0.02, 1.05, Z - 0.22, X + 0.16, 1.38, Z + 0.22)],      # head box
        'screen': [box(X + 0.16, 1.1, Z - 0.16, X + 0.165, 1.33, Z + 0.16)],    # tablet
    }


PIPE_Y, PIPE_Z = 1.25, -8.47  # just above the cisterns and urinals (visible from above), clear of the outer wall


def flow_meter(X):
    return {
        'black': [box(X - 0.11, PIPE_Y - 0.09, PIPE_Z - 0.07, X + 0.11, PIPE_Y + 0.12, PIPE_Z + 0.08)],  # body
        'screen': [box(X - 0.07, PIPE_Y - 0.02, PIPE_Z + 0.08, X + 0.07, PIPE_Y + 0.08, PIPE_Z + 0.085)],
        'led_green': [box(X + 0.075, PIPE_Y + 0.05, PIPE_Z + 0.08, X + 0.095, PIPE_Y + 0.07, PIPE_Z + 0.086)],
        'orange': [cylinder(X - 0.06, PIPE_Z, 0.012, PIPE_Y + 0.12, PIPE_Y + 0.2, 8),                 # valve stem
                   box(X - 0.06 - 0.09, PIPE_Y + 0.2, PIPE_Z - 0.02, X - 0.06 + 0.09, PIPE_Y + 0.23, PIPE_Z + 0.02)],
    }


PROPS = [('SLP_DG_01', 'Devices_Lights', light_post(-8.62, 3.05)),
         ('KSK_RC_01', 'Devices_Panels', kiosk(-6.32, -0.4)),
         ('FLW_PIPE_01', 'Devices_Water', {'metal': [pipe_x(-14.4, 5.8, PIPE_Y, PIPE_Z, 0.04)]}),
         ('FLW_TM_01', 'Devices_Water', flow_meter(-9.55)),   # men's toilet, above the end urinal
         ('FLW_TW_01', 'Devices_Water', flow_meter(5.68))]    # women's toilet, past the last stall (stall doors hide the rest)

b = open(src, 'rb').read()
jl = struct.unpack('<I', b[12:16])[0]
j = json.loads(b[20:20 + jl])
binc = bytearray(b[20 + jl + 8:20 + jl + 8 + j['buffers'][0]['byteLength']])
if not any(m['name'] == 'tv_back' for m in j['materials']):  # the file's 'black' is a dark grey that reads brown in sunlight
    j['materials'].append({'name': 'tv_back', 'doubleSided': False,
                           'pbrMetallicRoughness': {'baseColorFactor': [0.012, 0.012, 0.014, 1.0], 'roughnessFactor': 0.6, 'metallicFactor': 0.0}})
mat = {m['name']: i for i, m in enumerate(j['materials'])}
def monitor(X, Z, desk_y):  # stand foot centre on the desk; screen faces +z
    y = desk_y + 0.2  # bottom of the panel
    return {
        'black': [box(X - 0.3, y, Z + 0.06, X + 0.3, y + 0.36, Z + 0.1)],
        'screen': [box(X - 0.28, y + 0.02, Z + 0.1, X + 0.28, y + 0.34, Z + 0.105)],
        'metal': [box(X - 0.032, desk_y, Z + 0.02, X + 0.032, y, Z + 0.06),            # neck
                  box(X - 0.12, desk_y, Z - 0.05, X + 0.12, desk_y + 0.012, Z + 0.13)],  # foot
    }


# Existing devices whose parts are replaced: (node, parts)
REBUILD = [('PC_16', monitor(-3.45, 0.0, 1.05))]  # reception counter top is 1.05 m; chair at z 0.6

# TVs whose back shows the screen: (TV node, a floor point in the room the screen faces)
BACK_PANELS = [('DSP_DG_01', (-11, 5)), ('DSP_DG_02', (-11, 5)), ('DSP_DG_03', (-11, 5.8)),  # Showcase Gallery
               ('DSP_MK_01', (19, 4)),                                                       # standing TV, Makerspace
               ('DSP_KT_01', (-6.4, 5))]                                                     # Kitchen (pantry)

# Devices moved as a whole: (node, new centre x, z on the floor plan, turn in degrees about the vertical).
MOVES = [('CCTV_02', 15.4, -2.65, 180)]  # Makerspace SW corner; the turn points its lens (+x, -z) into the room


def accessor_data(i):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC3': 3}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    return np.frombuffer(bytes(binc), dt, a['count'] * n, bv.get('byteOffset', 0) + a.get('byteOffset', 0))         .reshape(-1, n) if n > 1 else np.frombuffer(bytes(binc), dt, a['count'], bv.get('byteOffset', 0) + a.get('byteOffset', 0))


def add_view(data, target):
    while len(binc) % 4:
        binc.append(0)
    j['bufferViews'].append({'buffer': 0, 'byteOffset': len(binc), 'byteLength': len(data), 'target': target})
    binc.extend(data)
    return len(j['bufferViews']) - 1


def join(shapes):  # several (vertices, faces) into one
    vs, fs, off = [], [], 0
    for v, f in shapes:
        vs.append(v); fs.append(f + off); off += len(v)
    return np.vstack(vs), np.concatenate(fs)


def add_mesh(name, v, f, material, uv=None):
    v = np.ascontiguousarray(v, np.float32)  # glTF positions are 32-bit floats
    j['accessors'].append({'bufferView': add_view(v.tobytes(), 34962), 'componentType': 5126, 'count': len(v),
                           'type': 'VEC3', 'min': v.min(0).tolist(), 'max': v.max(0).tolist()})
    attrs = {'POSITION': len(j['accessors']) - 1}
    if uv is not None:
        j['accessors'].append({'bufferView': add_view(np.asarray(uv, np.float32).tobytes(), 34962), 'componentType': 5126,
                               'count': len(uv), 'type': 'VEC2'})
        attrs['TEXCOORD_0'] = len(j['accessors']) - 1
    j['accessors'].append({'bufferView': add_view(f.astype(np.uint32).tobytes(), 34963), 'componentType': 5125,
                           'count': int(f.size), 'type': 'SCALAR'})
    j['meshes'].append({'name': name, 'primitives': [
        {'attributes': attrs, 'indices': len(j['accessors']) - 1, 'mode': 4, 'material': mat[material]}]})
    j['nodes'].append({'name': name, 'mesh': len(j['meshes']) - 1})
    return len(j['nodes']) - 1


# Locker banks: 3 rows of `cols` doors, each 0.5 m wide and LOCKER_DOOR_H tall, numbered from the bottom left as
# seen from the front (01 bottom left). The front is at x, facing -x (face -1) or +x (face +1); the back stands on
# the wall at `back`; the bank spans z0..z1 (z0 < z1). sRGB colours: door, gap between doors, handle groove, numbers.
LOCKER_DOOR_H, LOCKER_PLINTH, LOCKER_ROWS = 0.85, 0.06, 3
LOCKERS = [
    # Corridor outside the Workshop, on its west wall, in place of a grey block. Grey; dark numbers at the top left.
    dict(name='LCK_01', x=15.48, back=15.94, face=-1, z0=-0.85, z1=2.15, cols=6, corner='left',
         door=(172, 181, 190), gap=(70, 76, 82), groove=(112, 120, 128), ink=(38, 41, 45)),
    # Makerspace, centred on its west wall, facing the tables. Blue; white numbers at the top left.
    dict(name='LCK_02', x=14.36, back=14.3, face=1, z0=-7.4, z1=-3.4, cols=8, corner='left',
         door=(60, 122, 210), gap=(22, 54, 108), groove=(42, 92, 166), ink=(244, 247, 252)),
]


def locker_texture(L, px=256):  # px per door width
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    dw, dh = px, round(px * LOCKER_DOOR_H / 0.5)
    im = Image.new('RGB', (dw * L['cols'], dh * LOCKER_ROWS), L['gap'])
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype('arialbd.ttf', round(dh * 0.1))
    for r in range(LOCKER_ROWS):  # r 0 is the top row
        for c in range(L['cols']):
            x, y = c * dw, r * dh
            d.rectangle([x + 2, y + 2, x + dw - 3, y + dh - 3], fill=L['door'])
            d.rectangle([x + 2, y + dh - 13, x + dw - 3, y + dh - 3], fill=L['groove'])
            n = (LOCKER_ROWS - 1 - r) * L['cols'] + c + 1
            right = L['corner'] == 'right'
            d.text((x + dw * (0.9 if right else 0.1), y + dh * 0.05), '%02d' % n, font=font, fill=L['ink'],
                   anchor='ra' if right else 'la')
    buf = BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def locker(L):
    top = LOCKER_PLINTH + LOCKER_ROWS * LOCKER_DOOR_H
    inward = 1 if L['back'] > L['x'] else -1
    body = sorted([L['x'] + inward * 0.01, L['back']])
    plinth = sorted([L['x'] + inward * 0.04, L['back']])
    return {'darkgrey': [box(plinth[0], 0, L['z0'] + 0.02, plinth[1], LOCKER_PLINTH, L['z1'] - 0.02)],
            L['name'].lower(): [box(body[0], LOCKER_PLINTH, L['z0'], body[1], top + 0.02, L['z1'])]}


for L in LOCKERS:
    m = L['name'].lower()  # body colour; m + '_doors' is the picture of the doors
    if m in mat:
        continue
    lin = [(c / 255) ** 2.2 for c in L['door']] + [1.0]  # glTF colour factors are linear
    j['materials'].append({'name': m, 'pbrMetallicRoughness': {'baseColorFactor': lin, 'roughnessFactor': 0.35, 'metallicFactor': 0.1}})
    view = add_view(locker_texture(L), None)
    del j['bufferViews'][view]['target']  # an image, not vertex data
    j.setdefault('images', []).append({'bufferView': view, 'mimeType': 'image/png'})
    j.setdefault('samplers', []).append({})
    j.setdefault('textures', []).append({'source': len(j['images']) - 1, 'sampler': len(j['samplers']) - 1})
    j['materials'].append({'name': m + '_doors', 'pbrMetallicRoughness': {
        'baseColorTexture': {'index': len(j['textures']) - 1}, 'roughnessFactor': 0.35, 'metallicFactor': 0.1}})
mat = {m['name']: i for i, m in enumerate(j['materials'])}

# The grey block outside the Workshop that LCK_01 replaces (it is this mesh's only shape).
next(n for n in j['nodes'] if n.get('name') == 'Circulation__midgrey').pop('mesh', None)
PROPS += [(L['name'], 'Devices_Lockers', locker(L)) for L in LOCKERS]

for tv, (rx, rz) in BACK_PANELS:
    node = next(n for n in j['nodes'] if n.get('name') == tv)
    node['children'] = [c for c in node['children'] if j['nodes'][c].get('name') != tv + '__back']  # drop an earlier run
    screen = j['nodes'][next(c for c in node['children'] if j['nodes'][c].get('name') == tv + '__screen')]
    prim = j['meshes'][screen['mesh']]['primitives'][0]
    v = accessor_data(prim['attributes']['POSITION']).astype(np.float32)
    # The screen is an 8-corner box (no node transform); its first two corners span its depth.
    depth = v[1] - v[0]
    c = v.mean(0)
    away = np.sign(np.dot(depth[[0, 2]], c[[0, 2]] - np.array([rx, rz]))) or 1.0
    node['children'].append(add_mesh(tv + '__back', v + away * depth * 1.05, accessor_data(prim['indices']).copy(), 'tv_back'))

for name, x, z, turn in MOVES:
    node = next(n for n in j['nodes'] if n.get('name') == name)
    kids = [j['nodes'][c] for c in node['children']]
    parts = [(k['name'], j['meshes'][k['mesh']]['primitives'][0]) for k in kids]
    allv = np.vstack([accessor_data(p['attributes']['POSITION']) for _, p in parts])
    centre = (allv.min(0) + allv.max(0)) / 2
    a = math.radians(turn)
    rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]], np.float32)
    shift = np.array([x, centre[1], z], np.float32)
    node['children'] = [add_mesh(n, (accessor_data(p['attributes']['POSITION']) - centre) @ rot.T + shift,
                                 accessor_data(p['indices']).copy(), j['materials'][p['material']]['name'])
                        for n, p in parts]

for name, parts in REBUILD:
    node = next(n for n in j['nodes'] if n.get('name') == name)
    node['children'] = [add_mesh(name + '__' + m, *join(shapes), m) for m, shapes in parts.items()]

for name, group_name, parts in PROPS:
    group = next((n for n in j['nodes'] if n.get('name') == group_name), None)
    if group is None:  # a new device group under Devices
        j['nodes'].append({'name': group_name, 'children': []})
        group = j['nodes'][-1]
        next(n for n in j['nodes'] if n.get('name') == 'Devices')['children'].append(len(j['nodes']) - 1)
    group['children'] = [c for c in group['children'] if j['nodes'][c].get('name') != name]  # drop an earlier run
    children = []
    for m, shapes in parts.items():
        v, f = join(shapes)
        children.append(add_mesh(name + '__' + m, v, f, m))
    j['nodes'].append({'name': name, 'children': children})
    group['children'].append(len(j['nodes']) - 1)

# Each locker's door front: one picture on a quad just in front of the body. Looking at a -x front, +z is to the
# right; at a +x front, -z is. glTF puts uv (0, 0) at the picture's top left.
y0, y1 = LOCKER_PLINTH, LOCKER_PLINTH + LOCKER_ROWS * LOCKER_DOOR_H
for L in LOCKERS:
    zl, zr = (L['z0'], L['z1']) if L['face'] < 0 else (L['z1'], L['z0'])
    front = [[L['x'], y0, zl], [L['x'], y0, zr], [L['x'], y1, zr], [L['x'], y1, zl]]
    [n for n in j['nodes'] if n.get('name') == L['name']][-1]['children'].append(
        add_mesh(L['name'] + '__doors', front, np.array([0, 1, 2, 0, 2, 3]), L['name'].lower() + '_doors',
                 uv=[[0, 1], [1, 1], [1, 0], [0, 0]]))

while len(binc) % 4:
    binc.append(0)
j['buffers'][0]['byteLength'] = len(binc)
js = json.dumps(j, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
glb = struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binc))
glb += struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binc), 0x004E4942) + bytes(binc)
open(out, 'wb').write(glb)
print('wrote', out, len(glb), 'bytes')
