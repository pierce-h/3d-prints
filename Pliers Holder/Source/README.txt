PLIERS HOLDER — CURRENT v04 MONOLITHIC DIAGONAL TRAY

Original closed-floor CAD with all 16 bays in one continuous piece. Bays range
from 16 to 24 mm; height 177.8 mm, tray depth 63.5 mm, width 356.4 mm. The H2D
project retains its checked diagonal placement. Earlier revisions stay archived.
Installed axes: X along wall, Y up, Z toward user; units millimetres.

CURRENT FILES AND DEPENDENCIES
build_tray_v04.py builds the one-piece tray and saves its 45-degree print pose.
It imports geometry/export/settings helpers from build_holder.py; retain that
source. render_tray_v04.py uses helpers from render_previews.py to render actual
meshes. validate_tray_v04.py archives the isolated CLI slice and embeds previews
and final hashes. The project contains one connected body. Its print bounding
box is centered at X 162.5, Y 155 mm; preserve the saved placement.
The retained Caliper Holder 3MF supplies settings only; no caliper mesh is reused:
../../Caliper Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf

Python: /tmp/screwdriver-holder-venv/bin/python
Packages: numpy, trimesh, manifold3d, Pillow; see requirements.txt.
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio
Render fonts: macOS /System/Library/Fonts/Supplemental/Arial*.ttf
Current output: ../Revisions/v04-monolithic-diagonal/
Temporary slices: /tmp/pliers-v04/full/

REBUILD v04
Preserve published files as a new revision before changing design/settings.
Run with the Python environment above:
1. build_tray_v04.py
2. render_tray_v04.py
3. validate_tray_v04.py --slice full
4. validate_tray_v04.py --finalize
Only one project is produced. The existing v03 shallow fit tray is retained.
Inspect actual-CAD previews and final sliced support/brim placement. The final
minimum bed-edge margin is 1.89 mm including extrusion width. Preserve the saved
45-degree floor-down pose and brim; verify PLA/left-nozzle mapping. No script
sends a print job or changes the Bambu Studio GUI project.

PRESERVED v03 / CURRENT SHALLOW FIT SAMPLE
Output: ../Revisions/v03-24mm-max-slots/. The full holder used two eight-bay
trays; its 16/20/24 mm shallow sample remains suitable for current widths/depth.
It has no cleat and does not test tall-tool stability or mounting.
Historical rebuild: build_tray_v03.py, render_tray_v03.py,
validate_tray_v03.py --slice all, then validate_tray_v03.py --finalize.
Temporary output: /tmp/pliers-v03/.

PRESERVED v02 WIDER-BAY TRAY
Output: ../Revisions/v02-upright-divider-tray/. This upright closed-floor tray
used 24–36 mm bays, 130 mm height and 105 mm tray depth. Its source and records
remain unchanged. Historical rebuild: build_tray_v02.py, render_tray_v02.py,
validate_tray_v02.py --slice all, then validate_tray_v02.py --finalize.
Temporary output: /tmp/pliers-v02/.

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
