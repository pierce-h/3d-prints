CABINET KNOB JIG — v01 SOURCE

Original fixed-offset drilling jig; mirrored A/B pair for all four door corners.
The guide centers are 31.75 mm from the side and 63.5 mm from the end. A uses a
left-edge stop in modeling coordinates, B its mirror. The exposed drill face
is Z=0; the door-contact face is Z=10. From the exposed face, A fits
top-left/bottom-right and B fits top-right/bottom-left. One/two grooves identify
A/B; these are not hinge-hand labels. The 5.05 mm CAD bore is a provisional fit for a 3/16-inch bit.

DEPENDENCIES
Python: workspace .venv/bin/python (from the 3D Prints library root).
Packages: numpy, trimesh, manifold3d and Pillow; mesh checks also use scipy,
shapely and rtree. Versions are recorded in requirements.txt.
The builder imports mesh/export/settings helpers from
../../Pliers Holder/Source/build_holder.py. Retain that source and its settings
input, ../../Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf.
Only helper code/settings are reused; no other project's geometry is copied.
The renderer may reuse ../../Pliers Holder/Source/render_previews.py.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio

REBUILD
Run from the 3D Prints library root:
1. .venv/bin/python "Cabinet Knob Jig/Source/build_jig_v01.py"
2. .venv/bin/python "Cabinet Knob Jig/Source/render_jig_v01.py"
3. .venv/bin/python "Cabinet Knob Jig/Source/validate_jig_v01.py" --slice full
4. .venv/bin/python "Cabinet Knob Jig/Source/validate_jig_v01.py" --finalize

Preview.png renders the actual parts; Placement_Diagram.png shows corner use.
Validation/geometry.json records dimensions and print transforms. The separate
independent_review.json records checks of exported meshes.
Preserve published files in a new revision before changing measurements.
Inspect exported dimensions, bore positions from the stop datums, A/B corner
mapping, and support-free print pose. Confirm saved PLA/left-nozzle mapping.
Successful digital checks do not verify actual door fit or guide wear.

CURRENT OUTPUT
../Revisions/v01-corner-jig/
The main 3MF keeps both jigs on one plate with print settings. Main STL is the
print pose; installed-coordinate validation meshes are inspection artifacts.
No source script sends a print job or changes the Bambu Studio GUI project.
