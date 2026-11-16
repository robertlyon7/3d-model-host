# Digital Twin 3D Assets

3D models loaded by the FlexIoT digital twin dashboard widgets.

| File | Size | Use |
|---|---|---|
| `office_building.glb` | ~4 MB | Office building exterior (Office Building 3D widget) |
| `smart-office.glb` | ~2 MB | Office floor interior with named IoT devices (Office Building 3D widget) |
| `outdoor.glb` | ~620 KB | Trees and a street light around the building (Office Building 3D widget). Built by `tools/make_outdoor.py` |

Load URL (jsDelivr, CORS-enabled):
`https://cdn.jsdelivr.net/gh/robertlyon7/3d-model-host@main/office_building.glb`

## Credits

`office_building.glb` is a modified version of
"[FREE] Atlanta, Corperate Office Building" by 99.Miles
(https://sketchfab.com/3d-models/free-atlanta-corperate-office-building-d96380fb001345cca9a9be121f3e43d5),
licensed under CC BY 4.0 (http://creativecommons.org/licenses/by/4.0/).
Changes: textures converted to WebP and resized to max 2048 px, geometry optimized with glTF-Transform.

`outdoor.glb` combines two models, both licensed under CC BY 4.0 (http://creativecommons.org/licenses/by/4.0/):

- "Free Pack - Tree" by PolyOne Studio
  (https://sketchfab.com/3d-models/free-pack-tree-196525a9936a40c1ba7e74ce5c071d59)
- "Simple Street Light" by 碧 (https://sketchfab.com/LK_7)
  (https://sketchfab.com/3d-models/simple-street-light-127d854caca141bca50eb14f035d617b)

Changes: the tree texture is baked into vertex colours and dropped. The street light's materials are baked into vertex colours, and its ground plane is removed. Both are rescaled to metres with the base at the origin. Sources: `free_pack_-_tree.glb`, `simple_street_light.glb`; rebuild with
`python tools/make_outdoor.py . outdoor.glb`.
