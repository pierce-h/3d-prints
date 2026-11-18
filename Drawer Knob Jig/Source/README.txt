DRAWER KNOB JIG — v01 SINGLE TOP-EDGE STOP

User-confirmed 63.5 mm top rail; guide center is 31.75 mm below the top edge.
The single stop permits horizontal sliding to a separately marked midpoint.
Engraved centerline and V sight notch share the bore center X=40 mm.

COORDINATES
X across drawer, Y down from top datum Y=0, Z into drawer. Exposed drill face
Z=0 prints on the bed; drawer-contact face Z=10; stop extends to Z=20.
Local mesh x=0..80, y=-4..55. Print project centers the part at X=170,Y=160.

DEPENDENCIES
Use the library .venv Python with numpy, manifold3d, trimesh, shapely and Pillow.
Geometry/archive helpers: ../../Pliers Holder/Source/build_holder.py.
Raster render helpers: ../../Pliers Holder/Source/render_previews.py.
Saved material/process input (preserve it):
../../Cabinet Knob Jig/Revisions/v03-clear-petg-right/Cabinet_Knob_Jig_v03_Claybourne_Pair_Clear_PETG_Right_TEST_FIT.3mf
The generator uses the input's settings only; new drawer geometry is generated.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio.

REBUILD FROM THE 3D PRINTS LIBRARY ROOT
1. .venv/bin/python "Drawer Knob Jig/Source/build_jig_v01.py"
2. .venv/bin/python "Drawer Knob Jig/Source/render_jig_v01.py" --embed
3. .venv/bin/python "Drawer Knob Jig/Source/validate_jig_v01.py" --slice
4. .venv/bin/python "Drawer Knob Jig/Source/review_jig_v01.py"
5. .venv/bin/python "Drawer Knob Jig/Source/validate_jig_v01.py" --finalize

Output: ../Revisions/v01-single-edge/. Temporary slice: /tmp/drawer-knob-jig-v01/.
Preview/diagram and independent review are checked before final archive hashes.
The 3MF is a saved project, not a queued printer job. No script sends a print.
Preserve previous revisions when changing dimensions or material settings.
