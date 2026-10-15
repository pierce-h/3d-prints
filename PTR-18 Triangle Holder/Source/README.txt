PTR-18 PLUS FRENCH-CLEAT HOLDER — PARAMETRIC MODELS

CURRENT: v06 essential storage
build_holder_v06.py builds only the main hanger: two tall-pin, two short-pin
and six screw-head pockets, plus one Allen-key through-hole. All spare pockets
and their underside bosses are removed. Retained pocket dimensions are unchanged;
reuse the v04 fit-check plate and standalone attachment/key samples.

The builder imports build_holder_v04.py and build_holder.py, and reads settings
from Revisions/v05-no-top-tray/PTR18_Hanger_v05_No_Top_Tray_TEST_FIT.3mf.
Retain those dependencies. render_mounted_v06.py renders mounting views;
finalize_projects_v06.py adds the main preview and preserves slicing records.
Current output: Revisions/v06-essential-storage/
Temporary slicing/rendering output: /tmp/ptr18-v06/

Installed axes: X along wall, Y up, Z toward user; units millimetres. Main
project and STL use the saved side print pose. Installed STL in Validation
is for inspection. Parameters/assumptions are inherited from v04; geometry.json
records the v06 layout and removed spares. Dependencies are recorded in requirements.txt.
Python environment used: /tmp/screwdriver-holder-venv/bin/python

REBUILD v06
1. Run build_holder_v06.py. Preserve published files as a new revision before
   changing geometry or settings.
2. Create /tmp/ptr18-v06/main and slice the main project with Bambu Studio:
   BambuStudio --datadir /tmp/ptr18-v06/main-profile --debug 1
     --arrange 0 --orient 0 --slice 1 --export-3mf sliced.3mf
     --outputdir /tmp/ptr18-v06/main <absolute main project path>
   Save the log to /tmp/ptr18-v06/main.log.
3. Render separately with --export-png 1 --camera-view 11 and output folder
   /tmp/ptr18-v06/render-main. Do not combine PNG export and slicing. Use a
   temporary display copy with filament_colour #8BBAD2 for readable previews.
4. Run render_mounted_v06.py, then finalize_projects_v06.py after the successful
   slice and renders. Inspect the ten-pocket layout and retained fit features.
   Do not regenerate or re-slice unchanged v04 samples for this revision.

PRESERVED v05
build_holder_v05.py, render_mounted_v05.py and finalize_projects_v05.py reproduce
Revisions/v05-no-top-tray/ using /tmp/ptr18-v05/. This main-only revision retains
its Print Notes.txt and six spare pockets. Its fit samples are also v04.

PRESERVED v04 / CURRENT FIT SAMPLES
build_holder_v04.py, render_mounted_v04.py and finalize_projects_v04.py reproduce
Revisions/v04-round-key-hole/. This retains its Print Notes.txt. Fit samples
from this revision are also the current v06 fit samples.
To rebuild v04, use /tmp/ptr18-v04/{main,samples,pockets,key} for independent
slice outputs and /tmp/ptr18-v04/<name>.log for each log. Render each separately
with camera 11 into /tmp/ptr18-v04/render-<name>, then run the v04 render and
finalization scripts. The four projects are the main hanger, five-piece sample
plate, standalone attachment-pocket sample and standalone Allen-key sample.

PRESERVED v03
build_holder_v03.py, render_mounted_v03.py and finalize_projects_v03.py
reproduce Revisions/v03-measured-attachments/ using /tmp/ptr18-v03/.
That revision retains its Print Notes.txt and the former closed Allen-key slot.

PRESERVED v02
build_holder_v02.py, render_mounted_v02.py and finalize_projects_v02.py
reproduce Revisions/v02-cutout-hook-and-storage/ using /tmp/ptr18-v02/.
That revision retains its Print Notes.txt. It has no standalone pocket project.

PRESERVED v01
build_holder.py, render_mounted.py and finalize_projects.py reproduce the
original peg-based model in Revisions/v01-test-fit/. Their temporary output is
/tmp/ptr18-build/. Follow the same sequence above using the v01 script names
and temporary path. The v01 revision retains its original Print Notes.txt.

The superseded interim peg holder with key storage is retained under
Source/Drafts/Unpublished_peg_holder_with_key_slot/ and marked NOT FOR PRINTING.
Use the v06-essential-storage main hanger and v04 fit projects linked in the library.

Saved 3MFs contain geometry and print settings, not a sent printer job.
Meshes were unioned with manifold3d and independently checked. Physical fit
and loaded strength remain unverified until actual print feedback is recorded.
