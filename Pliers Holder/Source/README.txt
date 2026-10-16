PLIERS HOLDER — v01 SOURCE

Original geometry created here: two independent eight-slot sections and a
handheld three-slot gauge. Installed axes: X along wall, Y up, Z toward user;
units millimetres. Design parameters are in build_holder.py. Slot dimensions
are provisional capacities for unmeasured mixed-size tools.

FILES AND DEPENDENCIES
build_holder.py constructs the geometry, saves print-pose 3MF/STLs, and records
geometry checks. It reads existing Bambu settings from:
../../Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf
That file is a settings dependency only; no caliper mesh is reused.
render_previews.py rasterizes actual STL triangles into the four previews.
validate_and_finalize.py slices in isolated Bambu CLI profiles, verifies PLA on
the left extruder with no support toolpaths/warnings, archives slice evidence,
and embeds previews plus final archive hashes.

Python environment used: /tmp/screwdriver-holder-venv/bin/python
Packages: numpy, trimesh, manifold3d, Pillow; see requirements.txt.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio
Render fonts: macOS /System/Library/Fonts/Supplemental/Arial*.ttf
Output: ../Revisions/v01-16-slot/
Temporary slice output: /tmp/pliers-v01/{full,section,sample}/

REBUILD
Preserve published files as a new numbered revision before changing dimensions
or settings. Run these with the Python environment above:
1. build_holder.py
2. render_previews.py
3. validate_and_finalize.py --slice all
4. validate_and_finalize.py --finalize
Inspect all previews and slice results before publishing the revision. The
finalize step adds thumbnails and hashes after the successful slices. Keep
geometry/independent-review reports and per-project slice records together.
No step sends a print job or changes the current Bambu Studio GUI project.

The full plate holds two independent sections; the section and gauge projects
are separate alternatives. Preserve their shelf-on-bed print poses. The gauge
has no wall cleat and checks slot fit only. Geometry and slicing checks do not
establish physical tool fit, cleat fit or a load rating.
