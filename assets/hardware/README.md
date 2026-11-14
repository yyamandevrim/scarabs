# ACORN housing CAD

`acorn.obj` and `acorn.mtl` are the supplied Onshape Part Studio 1 / Part 8 export. The material file was renamed alongside the OBJ; its `mtllib` reference was updated accordingly. No geometric edits were made to the source.

The OBJ header explicitly declares **metres**, not millimetres. It contains 7,994 positions, 16,028 triangles and **225** named surface fragments (`mesh0` through `mesh224`), rather than 225 mechanical components. Bounds are approximately 214 × 188 × 153 mm in its original axes. These are export extents, not manufacturing or mass specifications.

A four-view colour render was used to identify six logical assemblies:

| Assembly | Source fragments |
| --- | --- |
| Centre camera and its arm | 0–16 |
| Left camera and its arm | 131–147 |
| Right camera and its arm | 149–165 |
| Top plate, including its tether openings | 189–206 |
| Bottom plate, including its tether openings | 207–224 |
| Housing and retained mounting details | All remaining fragments |

The three circular optical faces are 0, 147 and 165. Rear pod faces 3, 139 and 157 are separate materials. The actual U-shaped arm surfaces (4–16; 131–144 except 139; 149–162 except 157) use opaque secondary plastic. The viewer retains these six logical groups for part selection, without an exploded view: there are no internal electronics to reveal. The paired plate openings are identifiable; no independent tether-eye fitting exists in this export, so none is added. The small internal mounting details remain with the housing: their exact electrical purpose is not established by CAD alone.

The source's threefold geometry is preserved. The Overview follows the owner's updated 360° product model: Camera 1 is the forward pod, Camera 2 approximately +120° and Camera 3 approximately −120°, derived from their CAD normals. Three flat adjoining sectors show the combined observation model without asserting a per-camera lens specification. Older station/planner forward-fan defaults are not presented on the Overview. Procedural rope tubes start at the real top openings (±5.5mm in X, Y=75mm) and the lower opening (X=5.5mm, Y=−75mm). Their continuation beyond the frame is scene context. There is no balloon, ground anchor, solar panel or invented electronic model.

## Rebuild the GLB

Use Node 22+ and a temporary directory outside the repository:

```sh
npm init -y
npm install three@0.187.0 esbuild@0.28.2 @gltf-transform/core@4.5.1 @gltf-transform/extensions@4.5.1 @gltf-transform/functions@4.5.1 three-mesh-bvh@0.9.18 playwright@1.65.1
cp REPO/placement/scripts/convert_hardware.mjs .
node convert_hardware.mjs REPO
```

The script preserves metres, rotates Z-up to Y-up, recentres the housing, merges fragments by the table above, computes 36° creased normals in millimetres (to avoid a coarse metre-scale position hash), welds duplicate vertices, quantizes positions to 14 bits and normals to 10, and writes one quantized GLB without meshopt compression or a WebAssembly decoding dependency. The converter bakes 32 short-range hemisphere rays per vertex and modest contact darkening at actual arm roots, plate junctions and tether openings. Contact darkening is 15% within 3mm and tapers by 8mm. The runtime assigns fine plastic finish, a rear-face parting seam and shallow matching optics inside the existing pod faces. Only the rear rim has a faint finish line; selected parts get a thin interaction outline. A supplied-wordmark decal is printed on the existing top plate. No general technical-drawing edge overlay is used. Nothing from the build toolchain belongs in the repository.
