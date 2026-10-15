# 3D Print Library

A personal collection of workshop organizers, French cleat holders, and fit-test parts. This repository keeps original designs, modeling sources, Bambu Studio projects, previews, and print feedback together so each change can be traced and earlier versions recovered.

Start with the models below. [Library.txt](Library.txt) is the detailed catalog; each project's **Print Notes** records dimensions, revision history, and actual fit results.

## Current models

| Project | Current Bambu Studio project | Status | Details |
| --- | --- | --- | --- |
| Screwdriver holder | [v02 — eight left-side openings at ⅝ inch](Screwdriver%20Holder/Revisions/v02-left-holes-5-8-inch/Screwdriver_Holder_v02_5-8in_Holes.3mf) | Geometry and slicing checked; physical fit pending. | [Print Notes](Screwdriver%20Holder/Print%20Notes.txt) |
| Festool double sander holder | [v02 — lighter backing and French cleat](Festool%20Sander%20Holder/Revisions/v02-lighter-backing/Festool_Double_Holder_v02_TEST_FIT.3mf) | Prototype for side-by-side RO 150 and ETS EC 150 storage; fit checks pending. | [Print Notes](Festool%20Sander%20Holder/Print%20Notes.txt) |
| Bench Cookie organizer | [v02 — joined holder and accessory storage](Bench%20Cookie%20Organizer/Revisions/v02-side-print/Bench_Cookie_Organizer_v02_Side_Print.3mf) | Sliced on its side to reduce supports; physical fit pending. | [Print Notes](Bench%20Cookie%20Organizer/Print%20Notes.txt) |
| TSO tool holder | [v01 — plain front](TSO%20Tool%20Holder/Revisions/v01-plain-front/TSO_Tool_Holder_v01_Plain_Front.3mf) | Maker emblem filled flush; geometry and slicing checked. Physical fit pending. | [Print Notes](TSO%20Tool%20Holder/Print%20Notes.txt) |
| PTR-18+ triangle holder | [v10 — PLA Basic, right nozzle](PTR-18%20Triangle%20Holder/Revisions/v10-pla-right-nozzle/PTR18_Hanger_v10_PLA_Basic_Right_TEST_FIT.3mf); [v09 PETG alternative](PTR-18%20Triangle%20Holder/Revisions/v09-enlarged-deeper-pockets/PTR18_Hanger_v09_Enlarged_Deeper_Pockets_PETG_Right_TEST_FIT.3mf) | Same enlarged pockets and 6 mm screw depth. PLA Basic is the assumed profile; actual spool and full PLA fit/finish remain unconfirmed. | [Print Notes](PTR-18%20Triangle%20Holder/Print%20Notes.txt) |
| Caliper holder | [v01 — 32 mm center opening](Caliper%20Holder/Revisions/v01-32mm-center/Caliper_Holder_v01_32mm_Center.3mf) | Widened for an approximately 30 mm caliper body; revised physical fit pending. | [Print Notes](Caliper%20Holder/Print%20Notes.txt) |

Status reflects recorded feedback as of October 15, 2026. A successful geometry check or slice does not establish physical fit or load capacity.

## Fit samples first

The [PTR-18 v08 clearance-test project](PTR-18%20Triangle%20Holder/Revisions/v08-clearance-test/PTR18_Attachment_Clearance_Test_v08_PETG_Right.3mf) compares two pocket sizes while preserving the full holder's horizontal-hole print orientation:

| Sample | Pin pockets | Small screw pocket | Identification |
| --- | --- | --- | --- |
| **2** — diameters increased by 2 mm | 11.8 mm | 8.8 mm | Raised **2**, one corner notch |
| **3** — diameters increased by 3 mm | 12.8 mm | 9.8 mm | Raised **3**, two corner notches |

Both samples include short-pin, tall-pin, and screw-head pockets for storage with the bodies down and threads up. On October 15, the user accepted the **one-notch / +2 mm** sample: it has more than enough space and is slightly loose, which is acceptable. The **v09 PETG and v10 PLA full holders** use those diameters and deepen the six screw pockets from **2.5 to 6 mm**, so the 4 mm heads sit 2 mm below the shelf for retrieval by their threads. The new depth still needs a physical check. v10 changes the selected material to PLA while preserving v09 geometry and placement. Verify the actual PLA profile and spool mapping before printing; use PLA in a cool location out of direct sun, and evaluate the finished hanger before loaded use.

The saved project uses black Bambu PETG Matte on the **right nozzle** and slices to approximately **1 hour 42 minutes / 33 g** for both samples. See the [labeled preview](PTR-18%20Triangle%20Holder/Revisions/v08-clearance-test/Labeled_Preview.png) and [revision notes](PTR-18%20Triangle%20Holder/Revisions/v08-clearance-test/Revision%20Notes.txt). The accepted fit result came from the print started before the text labels were added; the corner notch identifies it. The sample is smoother than the first full print, but rough lines and waviness remain near the holes. The cause is unconfirmed.

The Festool holder also has a [small French cleat fit sample](Festool%20Sander%20Holder/Revisions/v02-lighter-backing/French_Cleat_Fit_Sample_v02.3mf) to check against the actual wooden rail before printing the full holder.

## Opening a print

1. Download the selected **3MF** and open it as a project in **Bambu Studio** to retain its saved orientation, objects, and print settings.
2. Read its Print Notes and confirm the printer, nozzle, build plate, material, and actual filament mapping. Profiles differ between projects.
3. Slice and inspect the preview before sending the job. Print any relevant fit samples first.

**STL** files contain mesh geometry without the saved Bambu print setup. Files under `Validation/` may use inspection or wall-mounted coordinates; use the linked project for printing.

## Folder layout

```text
3D Prints/
├── README.md
├── Library.txt                 Detailed model catalog
├── Version Control.txt         Git workflow
└── Project Name/
    ├── Original/               Preserved starting files
    ├── Source/                 Modeling scripts and dependencies
    ├── Revisions/
    │   └── vNN-description/    3MFs, STL exports, previews, and notes
    │       └── Validation/     Geometry and slicing evidence
    └── Print Notes.txt         Revision history and physical feedback
```

Some projects also include reference material, concept images, or session backups. Prefer the catalog links over loose files at the repository root when choosing a current model.

## Making and saving changes

- Preserve originals and earlier revisions. Use a new numbered revision for meaningful geometry or print-setting changes.
- Keep sources, saved projects, previews, and validation records together. Check the result, then update Library.txt and the project's Print Notes.
- Commit each completed change with a clear description, then push it to GitHub. Saving in Bambu Studio does not automatically commit or upload anything.
- Record print and fit feedback separately, including the revision and material used.

Git tracks the library's files and history. Bambu Studio continues to open the same projects; it does not display Git history. Generated G-code, temporary files, and local environments are excluded. See [Version Control.txt](Version%20Control.txt) for commands and backup details.

To rebuild a model, consult its source instructions and revision notes. Several scripts depend on earlier revisions and use local macOS or temporary paths. **The PTR-18 v08 builders and STL exports reproduce the unlabeled base; preserve the native 3MF to keep its editable Bambu text labels.**

## Original designs

The starting files record the following creators and license labels. These are source-file metadata, not a repository-wide license grant.

| Starting design | Creator | Recorded license |
| --- | --- | --- |
| [Screwdriver holder](Screwdriver%20Holder/Original/) | Thomas | MakerWorld Exclusive License |
| [Festool sander cradle](Festool%20Sander%20Holder/Original/) | FortuneAU | Standard Digital File License |
| [Bench Cookie holders](Bench%20Cookie%20Organizer/Original/) | alejepa | Standard Digital File License |
| [TSO square holder](TSO%20Tool%20Holder/Original/) | dave3ddiy | BY-NC-SA |
| [Caliper holder](Caliper%20Holder/Original/) | 3D-Therapy | CC0 |
