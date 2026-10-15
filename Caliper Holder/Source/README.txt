CALIPER HOLDER — CENTER-OPENING MODIFICATION

Original model: Caliper Holder for French Cleat by 3D-Therapy, CC0.
Source: ../Original/Caliper_Holder_for_French_Cleat_saved_2026-10-14_0948.3mf
Original_Metadata.json retains source attribution and project metadata.
The library-root original is retained separately and is not modified.

widen_center.py trims only the inner front support tips to a 32 mm opening,
keeping the original opening center. It preserves the backplate, French cleat,
outer dimensions, print placement and slicer settings. Outputs:
../Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf
../Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.stl
Validation/ includes before/after meshes, removed material and geometry checks.

Units are millimetres. Local X projects forward, Y is installed height, and
Z runs across the holder. The exported STL uses the original 3MF print pose.

REBUILD
Use Python with numpy, trimesh and manifold3d. The environment used is
/tmp/screwdriver-holder-venv/bin/python. Run widen_center.py; preserve published
outputs as a new revision before changing geometry.
Slice the revised 3MF with Bambu Studio into /tmp/caliper-edit/slice using a
private data folder, --arrange 0 --orient 0 --slice 1 and --export-3mf sliced.3mf.
Do not combine PNG export with slicing. render_and_finalize.py handles the
preview images and retained slice records after successful slicing.

The main project retains its original H2D / black PLA Basic settings. A separate
project's PETG or extruder choices do not apply to this caliper holder.
Digital checks do not establish physical fit; record print feedback in Print Notes.txt.
