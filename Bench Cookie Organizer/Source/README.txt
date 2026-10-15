BENCH COOKIE ORGANIZER — EDITABLE SOURCE

Original models by alejepa; original license and attribution retained.
Original files are preserved in ../Original; their full metadata is archived
in Original_Metadata.json. This is a local personal-use modification.

build_welded_holder.py builds one connected solid from the two main models.
The accessory's locating joint is seated 1 mm into the cookie holder.
Only the internal assembly clearance is filled; tool slots and cleat are unchanged.
Installed coordinates: X towards user, Y across wall, Z upwards.
Overall size: 222 mm wide x 116 mm deep x 201 mm high.

Dependencies: Python, numpy, trimesh, manifold3d (versions in requirements.txt).
Current environment: /tmp/screwdriver-holder-venv/bin/python

1. Run build_welded_holder.py.
2. Slice each generated 3MF using Bambu Studio. To collect CLI validation:
   Create /tmp/bench-weld-slice and /tmp/bench-spacers-slice first.
   BambuStudio --datadir <separate temporary profile directory> --debug 1
     --arrange 0 --orient 0 --slice 1 --export-3mf sliced.3mf
     --outputdir <output directory> <project.3mf>
   Use only a filename for --export-3mf, since it is relative to --outputdir.
   Main output directory: /tmp/bench-weld-slice
   Spacer output directory: /tmp/bench-spacers-slice
3. Run finalize_projects.py to refresh previews and collect successful results.

The main print is upright. Centre X is 175 mm, in the H2D nozzles' shared area;
tree supports extend beyond the model. Keep room for supports when rearranging.
The supplied upper holder's PLA Basic / H2D / 0.20 mm / 3-wall / 12% gyroid
settings are retained. Original support-enforcer and stale per-object overrides
were not transferred. The accessory's old 3% local infill override is superseded
by the unified 12% global setting.

ASCII STL intentionally preserves precision at the finely tessellated joint.
Binary float32 STL collapsed several nearby vertices during validation.

Rear_Spacers_4x_v01.3mf contains four unmodified, optional rear distance blocks.
They are not part of the welded holder: attachment depends on wall rail spacing.
Physical fit, print quality and loaded performance have not been tested.

V02 — SIDE PRINT
prepare_side_print.py creates the current v02-side-print revision from v01.
It changes only the build placement, labels and thumbnails; the 3MF mesh and
process settings are preserved exactly. The left/hole-bank end rests on the bed.
Its 222 mm print height and 201 x 116 mm footprint fit the H2D shared nozzle area.
The script uses orientation trials in /tmp/bench-orientation-comparison:
  y0-down:   rotation rows [0,0,1], [1,0,0], [0,1,0]; translation [200.5,115,0].
  y222-down: rotation rows [0,0,-1], [1,0,0], [0,-1,0]; translation [149.5,115,222].
Slice both with the same settings and CLI procedure above. Preview camera 11
shows the selected placement clearly. Successful slice reports and comparison
are retained under Revisions/v02-side-print/Validation.
Recommended left-end-down slice: 21h57m, 644 g total, about 83 g of support.
Retain supports/brim. This orientation has not been physically printed yet.
