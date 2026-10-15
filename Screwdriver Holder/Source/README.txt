EDITABLE SOURCE — SCREWDRIVER HOLDER

enlarge_screwdriver_holes.py reproduces v01 from the original project.
resize_screwdriver_holes_5_8.py reproduces v02 from the original project.
Keep these scripts together: the v02 script imports helpers from the v01 script.

Input: ../Original/Screwdriver_Holder_FC.3mf
Outputs: the corresponding ../Revisions/ folder, including its Validation/geometry.json.
Python dependencies are recorded in requirements.txt.

The scripts write to their recorded revision folders. Before modifying a design,
copy/update its script for a new numbered revision and change its output folder
and filename. Preserve prior project files, especially any used for a successful
physical print. Use the v02 script without --max-everywhere for the confirmed
eight-hole scope; that optional branch was not used for v02.

Historical independent and slicing validation files were moved intact. Their
embedded filenames/paths reflect the location at the time of validation.
The standalone Preview.png files show each revision. Geometry generation does
not refresh every cached Bambu preview image; refresh previews after rebuilding.
