FESTOOL DOUBLE-HOLDER SOURCE

Python dependencies: requirements.txt.
The build reads ../Original/Festool_RO150_Holder_3MF.3mf without changing it.
It uses manifold3d Boolean solids and exports a full holder plus an exact cleat
cross-section sample, each as STL and a Bambu 3MF project.

Run in order:
  python build_double_holder.py
  python finalize_projects.py
  python render_preview.py

The finalizer requires Bambu Studio at:
  /Applications/BambuStudio.app/Contents/MacOS/BambuStudio
Preview color/orientation changes affect temporary copies only.

Defaults: gap 20 mm; additional backing 6 mm; cleat projection 17.5 mm;
45-degree bevel. Original pad/cradle shape is preserved. The projection leaves
wall clearance for nominal 18–19.05 mm plywood. It is not an enclosed channel,
so there is no tight width dimension wrapped around the plywood.

For a new revision, use a new --revision value in all three scripts.
The current lighter revision was built using:
  python build_double_holder.py --revision v02-lighter-backing --back-style frame
  python finalize_projects.py --revision v02-lighter-backing
  python render_preview.py --revision v02-lighter-backing
Frame mode follows the original curved rear web and center spokes with a
1 mm rear-only margin, clipped within the old overall bounds. It retains the
whole cleat and continuous backing behind its attachment region. Rectangular
mode remains the default for reproducing v01.
Do not overwrite a revision that has already been printed or approved.

The scripts overwrite their selected output revision. After regeneration,
rerun independent geometry checks and Bambu slicing; old validation/estimate
files and rendered assets may no longer describe the new geometry.

The saved 3MF contains print placement and settings. The STL is also exported
in print orientation. Validation/holder_installed.stl and coupon_installed.stl
are analysis geometry in wall-mounted coordinates, not print projects.

Current status: test-fit prototype. Geometry validation does not establish
physical tool fit, wall fit, load capacity or long-term material performance.
