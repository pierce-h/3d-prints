PTR-18 PLUS FRENCH-CLEAT HOLDER — PARAMETRIC MODELS

CURRENT PRINT SETUP: v11 PLA Basic / left external feed
prepare_pla_v11.py copies v10 and maps PLA filament 1 to LEFT extruder 1, matching
the black Bambu PLA Basic external feed confirmed in the device UI. Project and
plate use Manual filament grouping. Its --slice option validates a separate
CLI slice while preserving geometry, placement, process and existing calibration.
Output: Revisions/v11-pla-left-external/. Actual print start was confirmed on
October 15; consult Print Notes for status rather than inferring completion.

PRESERVED PRINT SETUP: v10 PLA Basic / right nozzle
prepare_pla_v10.py copies the checked v09 3MF geometry and placement unchanged,
selects the existing Bambu PLA Basic profile in filament slot 1 and maps it to
the RIGHT extruder. The v09 STL is copied identically. Existing PLA temperature,
cooling, flow and pressure-advance values are preserved; no new calibration is
performed. Actual PLA spool type is unconfirmed, so check it before printing.
Output: Revisions/v10-pla-right-nozzle/. The v09 PETG project is preserved.

REBUILD v10
1. Preserve published revisions, then run prepare_pla_v10.py.
2. Create /tmp/ptr18-v10/main and slice the v10 project separately:
   BambuStudio --datadir /tmp/ptr18-v10/main-profile --debug 1
     --arrange 0 --orient 0 --slice 1 --export-3mf sliced.3mf
     --outputdir /tmp/ptr18-v10/main <absolute v10 main project path>
   Save the log to /tmp/ptr18-v10/main.log.
3. Run finalize_pla_v10.py after the successful slice. Verify active filament 1,
   right extruder 2, unchanged geometry/placement and final archive hashes.
   The reused CAD preview is valid because geometry and pose are unchanged.

CURRENT GEOMETRY / PRESERVED PETG SETUP: v09 enlarged and deeper pockets
build_holder_v09.py applies the accepted one-notch v08 clearance to the full
holder: four 11.8 mm pin pockets, still 8/16 mm deep, and six 8.8 mm screw pockets,
now 6 mm deep. The measured 4 mm screw heads sit 2 mm below the shelf for thread
retrieval. Underside bosses preserve nominal 3 mm radial walls, 3 mm pin floors
and 3.5 mm screw floors. All other fit features and overall bounds are unchanged.

The builder imports build_holder_v06.py for the original solid, build_holder.py
for geometry/export helpers and build_clearance_test_v08.py for native project
metadata patching. Keep their transitive dependencies, including build_holder_v04.py.
Geometry is checked against the preserved v06 3MF; saved settings and filament
extras are copied from the current native v08 clearance-test 3MF. Keep both
reference files. The full holder uses black Bambu PETG Matte, project filament 4,
RIGHT nozzle, with the v08 outer-wall limit of 100 mm/s.
Geometry/PETG output: Revisions/v09-enlarged-deeper-pockets/
Temporary slicing/rendering output: /tmp/ptr18-v09/
Python environment used: /tmp/screwdriver-holder-venv/bin/python
Dependencies: requirements.txt. Installed axes: X along wall, Y up, Z toward user;
units millimetres. The main project and STL use the side print pose. The installed
STL in Validation is for inspection.

REBUILD v09
1. Preserve published files in a new revision before changing geometry/settings.
   Run build_holder_v09.py to build the main project and geometry validation.
2. Create /tmp/ptr18-v09/main and slice separately with Bambu Studio:
   BambuStudio --datadir /tmp/ptr18-v09/main-profile --debug 1
     --arrange 0 --orient 0 --slice 1 --export-3mf sliced.3mf
     --outputdir /tmp/ptr18-v09/main <absolute v09 main project path>
   Save the log to /tmp/ptr18-v09/main.log.
3. Run render_and_finalize_v09.py for actual-CAD previews and archived slice
   records after the successful slice. Inspect Mounted_Preview.png and
   Print_Preview.png. Keep the current side print pose and do not re-slice
   unchanged historical sample projects as part of this revision.
4. Verify the final 3MF, pocket dimensions and retained fit features, update
   notes with the checked slice result, and record new physical feedback separately.

PRESERVED v08 — clearance comparison
build_clearance_test_v08.py and finalize_clearance_test_v08.py reproduce the
UNLABELED samples. The later native Bambu 3MF includes editable text 2 and 3,
which these scripts and STL exports do not reproduce. Preserve that native 3MF.
The one-notch / +2 mm sample was accepted as slightly loose but suitable. Its
2.5 mm screw pocket does not test the new v09 6 mm depth. Keep pre-label and
labeled validation records separate.

PRESERVED v07 — PETG print setup
The native v07 project retains v06 geometry and the first full-print setup.
Its surface and undersized-pocket feedback are recorded in ../Print Notes.txt.
The latest settings come from the saved v08 project, not v07.

PRESERVED v06 — essential storage
build_holder_v06.py builds only the main hanger: two tall-pin, two short-pin
and six screw-head pockets, plus one Allen-key through-hole. All spare pockets
and their underside bosses are removed. Retained pocket dimensions are unchanged;
reuse the v04 fit-check plate and standalone attachment/key samples.

The builder imports build_holder_v04.py and build_holder.py, and reads settings
from Revisions/v05-no-top-tray/PTR18_Hanger_v05_No_Top_Tray_TEST_FIT.3mf.
Retain those dependencies. render_mounted_v06.py renders mounting views;
finalize_projects_v06.py adds the main preview and preserves slicing records.
Preserved output: Revisions/v06-essential-storage/
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

PRESERVED v04 / UNCHANGED CLEAT, HOOK, FENCE AND KEY SAMPLES
build_holder_v04.py, render_mounted_v04.py and finalize_projects_v04.py reproduce
Revisions/v04-round-key-hole/. This retains its Print Notes.txt. Fit samples
remain applicable to the unchanged cleat, hook, fence and key geometry. The
attachment sample has the original smaller pockets; v09 uses the v08 selection.
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
Use the v11 left-external PLA project; v10 right-nozzle PLA and v09 PETG remain
separate alternatives linked in the library.

Saved 3MFs contain geometry and print settings, not a sent printer job.
Meshes were unioned with manifold3d and independently checked. Physical fit
of the new 6 mm pocket depth and loaded strength remain unverified. The v08
one-notch sample diameters were physically accepted for storage.
