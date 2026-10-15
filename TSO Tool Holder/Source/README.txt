TSO TOOL HOLDER — PLAIN FRONT

Original TSO Square Holder by dave3ddiy, source license BY-NC-SA.
Unmodified source archived in ../Original/TSO_Square_Holder.3mf.
Original metadata preserved in Original_Metadata.json.

flatten_front.py fills the circular maker recess to the original front plane.
Source coordinate Z=6.27499962 is the surrounding front; the recess floor is
Z=5.77499962. A rectangular union patch inside the panel fills only this recess.
The original wall, tool slot, rounded edges, cleat and printer placement remain.
The final model is one watertight solid with 140 triangles. Process settings
are preserved byte-for-byte from the original 3MF.

Python environment: /tmp/screwdriver-holder-venv/bin/python
Dependencies: numpy, trimesh, manifold3d, Pillow (versions in requirements.txt).

Rebuild:
1. Run flatten_front.py.
2. Create /tmp/tso-plain/slice and /tmp/tso-plain/render.
3. Slice with Bambu Studio CLI using a separate temporary profile:
   BambuStudio --datadir /tmp/tso-plain/slice-profile --debug 1
     --arrange 0 --orient 0 --slice 1 --export-3mf sliced.3mf
     --outputdir /tmp/tso-plain/slice <generated 3MF>
   Save console output in /tmp/tso-plain/slice.log.
4. Render separately (--export-png cannot be combined with --slice):
   BambuStudio --datadir /tmp/tso-plain/render-profile --debug 1
     --arrange 0 --orient 0 --export-png 1 --camera-view 10
     --outputdir /tmp/tso-plain/render <generated 3MF or display copy>
   Save console output in /tmp/tso-plain/render.log.
   A display copy with filament_colour set to #8BBAD2 makes the front visible;
   do not change the actual print project settings when preparing the preview.
5. Run finalize_project.py to refresh thumbnails and collect slice validation.

The ASCII STL preserves source precision. Preview files show the print pose.
Physical fit, print quality and loaded performance have not been tested.
