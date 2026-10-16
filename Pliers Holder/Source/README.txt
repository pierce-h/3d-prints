PLIERS HOLDER — CURRENT v02 UPRIGHT DIVIDER TRAY

Original CAD inspired by the user's red-rack photo: tools rest on a closed
floor between tall fins. v01's hanging comb is superseded and preserved.
Installed axes: X along wall, Y up, Z toward user; units millimetres.

CURRENT FILES AND DEPENDENCIES
build_tray_v02.py holds dimensions and creates the full two-tray plate, single
tray and shallow fit tray. It imports geometry/export/settings helpers from
build_holder.py, so retain that v01 source. Its settings dependency is:
../../Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf
Only settings are reused; no caliper mesh is copied.
render_tray_v02.py uses the preview helpers in render_previews.py to render
actual meshes. Keep both scripts. validate_tray_v02.py uses isolated Bambu CLI
profiles, archives slice evidence, and embeds previews plus archive hashes.

Python: /tmp/screwdriver-holder-venv/bin/python
Packages: numpy, trimesh, manifold3d, Pillow; see requirements.txt.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio
Render fonts: macOS /System/Library/Fonts/Supplemental/Arial*.ttf
Current output: ../Revisions/v02-upright-divider-tray/
Temporary slices: /tmp/pliers-v02/{full,section,sample}/

REBUILD v02
Preserve published files as a new revision before changing design/settings.
Run with the Python environment above:
1. build_tray_v02.py
2. render_tray_v02.py
3. validate_tray_v02.py --slice all
4. validate_tray_v02.py --finalize
Inspect the actual-CAD previews, geometry and support placement before publishing.
The full/single trays print upright, floor-down, with tree supports at rear
cleats; the shallow sample has no cleat. Verify saved PLA/left-nozzle mapping.
The finalize step embeds previews and hashes after successful slices. No step
sends a print or changes the current Bambu Studio GUI project.

PRESERVED v01 HANGING COMB
Output: ../Revisions/v01-16-slot/. This is the earlier open-slot design that
held tools by their heads, superseded after the user clarified the tray concept.
Its source/notes/validation remain intact. Rebuild only for historical work:
build_holder.py, render_previews.py, validate_and_finalize.py --slice all,
then validate_and_finalize.py --finalize. Temporary output: /tmp/pliers-v01/.
That revision prints shelf-on-bed without supports and has a handheld slot gauge.

Each current project uses provisional capacities, not measured tool dimensions.
The shallow fit tray cannot establish tall-tool stability, cleat fit or load
capacity. Geometry and slicing success do not establish those physical results.
