SHARK ACCESSORY MOUNT — v02 ONE-PIECE CABINET MOUNT

Builds one shared cabinet backplate with two copies of the measured
right-hand receiver in ../Original/vacuumattach_r.3mf. The original declares
METERS: its importer explicitly multiplies coordinates by 1000 before
millimeter CAD operations. Other downloaded originals are unused references.
The v01 builders and outputs remain available for the separate-holder design.

COORDINATES AND CONSTRUCTION
Installed axes: X across the cabinet, Y up, Z away from the cabinet.
Crop the source to Z >= 0 and discard only its zero-volume clamp remnant.
Duplicate the receiver with a 100 mm X shift. Add one 171 x 51.17871 x 6.5 mm
rounded backing at Z=-6..0.5, with two 4.8 mm screw holes and 9.5 mm,
90-degree countersinks, 153 mm apart. The backing spans X=-12..159 mm.
The final mount must be one watertight connected body, with the original
receiver surfaces preserved ahead of the backing overlap.
For printing, installed +Y becomes print +Z, with both receivers and backing
bottoms on the bed. Fixed 100 mm spacing is untested against tool bodies.

DEPENDENCIES
Library .venv Python: numpy, manifold3d, trimesh and Pillow.
Original receiver/profile helpers: build_mount_v01.py
Geometry/archive helpers: ../../Pliers Holder/Source/build_holder.py
Raster preview helpers: ../../Pliers Holder/Source/render_previews.py
Preserved profile input (settings only):
../../Cabinet Knob Jig/Revisions/v02-claybourne-rail-aligned/Cabinet_Knob_Jig_v02_Claybourne_Pair_3-16in_PLA_Left_TEST_FIT.3mf
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio

REBUILD v02 FROM THE 3D PRINTS LIBRARY ROOT
1. .venv/bin/python "Shark Accessory Mount/Source/build_mount_v02.py"
2. .venv/bin/python "Shark Accessory Mount/Source/render_mount_v02.py" --embed
3. .venv/bin/python "Shark Accessory Mount/Source/validate_mount_v02.py" --slice
4. .venv/bin/python "Shark Accessory Mount/Source/validate_mount_v02.py" --finalize

Output: ../Revisions/v02-single-piece/
The saved 3MF is a project, not a queued print job. The scripts do not send
anything to the printer. Keep previous revisions when changing geometry.
To reproduce archived v01, use the matching build/render/validate_mount_v01.py
commands; they write ../Revisions/v01-cabinet-sockets/.

ATTRIBUTION AND MODIFICATIONS
Receiver by jverlenich:
https://www.printables.com/model/1421739-shark-powerdetect-vacuum-ip1251-attachment-holder
Cabinet remix by Pierce project, November 18, 2026: wand clamp removed;
right receiver duplicated; shared rounded backing and countersunk screw
holes added; print orientation/profile supplied. Original socket surfaces
retained. v01 used separate backplates; v02 joins them into one printed body.
This derivative design and modeling source are licensed CC BY-NC-SA 4.0:
https://creativecommons.org/licenses/by-nc-sa/4.0/
See ../Original/Attribution.txt for original files and full provenance.

IP3251 compatibility is inferred from Shark's shared accessory part numbers.
Source-model dimensions are not manufacturer specifications. Physical socket
fit, clearance between tool bodies and installed use remain untested.
