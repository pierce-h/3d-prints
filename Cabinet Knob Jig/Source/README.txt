CABINET KNOB JIG — CURRENT v03 CLEAR PETG / v02 CLAYBOURNE GEOMETRY

Original fixed-offset A/B pair. Guide centers are 31.75 mm from the side and
71.501 mm from the end: 63.5 mm nominal rail + half the published 16.002 mm
Claybourne mounting base. Larger 31.75 mm face overlap is deliberate.
On November 18, 2026, the user reported the last jig printed and was used
successfully: it worked great. Measured accuracy and guide wear were not reported.
v03 changes saved material/nozzle settings only; v02 geometry is unchanged.

COORDINATES AND HANDEDNESS
Exposed drill face Z=0; door-contact face Z=10. A uses a left-edge stop in
modeling coordinates, B its mirror. Viewed from the exposed face, A fits
top-left/bottom-right and B top-right/bottom-left. One/two grooves identify A/B;
these are corner labels, not hinge-hand labels. The nominal 5.05 mm bore is for
a 3/16-inch bit (4.7625 mm).

DEPENDENCIES
Python: workspace .venv/bin/python (from the 3D Prints library root).
Packages and versions: requirements.txt. Mesh checks use numpy, trimesh and
shapely; builder/render tools also use manifold3d and Pillow.
Builder imports ../../Pliers Holder/Source/build_holder.py for helpers/settings;
retain that source and its settings input:
../../Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf
No other project's geometry is reused. Renderer helpers are in
../../Pliers Holder/Source/render_previews.py.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio

CURRENT v03 MATERIAL VARIANT
From the library root:
.venv/bin/python "Cabinet Knob Jig/Source/build_jig_v03.py"
Reads the preserved v02 3MF and the installed Bambu PETG Translucent H2D preset.
Output: ../Revisions/v03-clear-petg-right/ with one clear PETG project filament
mapped to the right nozzle, prime tower off. Validation/profile_geometry.json
checks preset values and byte-identical geometry/build transforms. This script
does not slice or send a print. The saved profile is not a confirmation of the
exact final settings used for the successful print.

PRESERVED v02 GEOMETRY REBUILD
From the 3D Prints library root:
1. .venv/bin/python "Cabinet Knob Jig/Source/build_jig_v02.py"
2. .venv/bin/python "Cabinet Knob Jig/Source/render_jig_v02.py"
3. .venv/bin/python "Cabinet Knob Jig/Source/validate_jig_v02.py" --slice full
4. .venv/bin/python "Cabinet Knob Jig/Source/review_jig_v02.py"
5. .venv/bin/python "Cabinet Knob Jig/Source/validate_jig_v02.py" --finalize

Output: ../Revisions/v02-claybourne-rail-aligned/
Temporary slice: /tmp/cabinet-knob-jig-v02/full/
Preview.png renders actual parts; Placement_Diagram.png shows correct corner use.
Validation/geometry.json records dimensions/poses; independent_review.json checks
exported meshes and the nominal base-to-rail alignment without importing CAD.
The finalize step embeds previews and hashes. Inspect final artifacts before
publishing; use a new revision for future measurement changes.

PRESERVED v01
Output: ../Revisions/v01-corner-jig/. End offset 63.5 mm; side offset 31.75 mm.
Historical rebuild uses build_jig_v01.py, render_jig_v01.py,
validate_jig_v01.py --slice full, review_jig_v01.py, then
validate_jig_v01.py --finalize. Temporary slice: /tmp/cabinet-knob-jig-v01/full/.
Do not overwrite preserved revision artifacts when making current changes.

Main 3MF retains both jigs on one plate and their settings. Main/individual STL
files use the print pose; installed-coordinate validation meshes are inspection
artifacts. No script sends a print job or changes the Bambu Studio GUI project.
