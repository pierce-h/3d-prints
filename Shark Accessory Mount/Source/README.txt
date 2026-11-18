SHARK ACCESSORY MOUNT — v01 CABINET SOCKETS

Builds two independent cabinet mounts from the measured right-hand receiver
in ../Original/vacuumattach_r.3mf. The original declares METERS: the importer
explicitly multiplies coordinates by 1000 before millimeter CAD operations.
The other downloaded originals are comparison references and are not used.

COORDINATES AND CONSTRUCTION
Installed axes: X across the cabinet, Y up, Z away from the cabinet.
Crop the source to Z >= 0 and discard only its zero-volume clamp remnant.
Add a 71 x 51.17871 x 6.5 mm rounded backing at Z=-6..0.5, with two
4.8 mm screw holes and 9.5 mm, 90-degree countersinks, 53 mm apart.
The builder verifies source geometry ahead of Z=0.501 is preserved exactly
by solid differences. Each finished holder must be one watertight body.
For printing, installed +Y becomes print +Z, with both receiver and backing
bottoms on the bed. The pair and single use the same geometry and orientation.

DEPENDENCIES
Library .venv Python: numpy, manifold3d, trimesh and Pillow.
Geometry/archive helpers: ../../Pliers Holder/Source/build_holder.py
Raster preview helpers: ../../Pliers Holder/Source/render_previews.py
Preserved profile input (settings only):
../../Cabinet Knob Jig/Revisions/v02-claybourne-rail-aligned/Cabinet_Knob_Jig_v02_Claybourne_Pair_3-16in_PLA_Left_TEST_FIT.3mf
Bambu CLI: /Applications/BambuStudio.app/Contents/MacOS/BambuStudio

REBUILD FROM THE 3D PRINTS LIBRARY ROOT
1. .venv/bin/python "Shark Accessory Mount/Source/build_mount_v01.py"
2. .venv/bin/python "Shark Accessory Mount/Source/render_mount_v01.py" --embed
3. .venv/bin/python "Shark Accessory Mount/Source/validate_mount_v01.py" --slice
4. .venv/bin/python "Shark Accessory Mount/Source/validate_mount_v01.py" --finalize

Output: ../Revisions/v01-cabinet-sockets/
The saved 3MFs are projects, not queued print jobs. The scripts do not send
anything to the printer. Keep previous revisions when changing geometry.

ATTRIBUTION AND MODIFICATIONS
Receiver by jverlenich:
https://www.printables.com/model/1421739-shark-powerdetect-vacuum-ip1251-attachment-holder
Cabinet remix by Pierce project, November 18, 2026: wand clamp removed;
rounded backing and countersunk screw holes added; print orientation/profile
and separate single/pair projects supplied. Original socket surfaces retained.
This derivative design and modeling source are licensed CC BY-NC-SA 4.0:
https://creativecommons.org/licenses/by-nc-sa/4.0/
See ../Original/Attribution.txt for original files and full provenance.

The IP3251 compatibility claim is an inference from Shark's shared accessory
part numbers. Source-model dimensions are not manufacturer specifications.
The first physical fit check remains pending.
