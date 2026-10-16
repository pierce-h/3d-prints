"""Render the actual v03 upright divider tray STL geometry without edits.

Reuses the depth-buffered, antialiased renderer from v01; v01 files are
unchanged. All dimensions and displayed geometry come from v03 exports.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from render_previews import page, panel, paste_mesh, font, INK, MUTED, ACCENT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v03-24mm-max-slots'


def footer(draw, y):
    draw.text((65, y), 'Prototype v03 · Original CAD geometry · Physical fit and loaded use untested',
              font=font(24), fill=MUTED)


def main():
    info = json.loads((OUT/'Validation/geometry.json').read_text())
    p = info['parameters_mm']
    module = trimesh.load(OUT/'Validation/Module_Installed.stl', force='mesh')
    sample = trimesh.load(OUT/'Validation/Fit_Sample_Installed.stl', force='mesh')
    second = module.copy()
    second.apply_translation((info['module']['width']+p['module_gap'], 0, 0))
    pair = trimesh.util.concatenate((module, second))
    rear = module.copy()
    # Turn the model under the renderer's light for a clearly lit rear view.
    # This rigid display rotation does not change the source geometry.
    rear.apply_transform(np.diag((-1., 1., -1., 1.)))
    total_width = 2*info['module']['width']+p['module_gap']
    labels = '  ·  '.join(str(int(w)) for w in p['bay_widths']) + ' mm'

    im, d = page('16-bay upright pliers tray',
                 f"Tall dividers, closed floor and front lip  /  {total_width:g} mm overall with a {p['module_gap']:g} mm gap",
                 (1800, 1430))
    panel(d, (55, 170, 1690, 730), 'Two separate 8-bay sections')
    paste_mesh(im, pair, (85, 245, 1630, 555), eye=(.25, .5, 1.5))
    d.text((290, 838), 'Each section: ' + labels, font=font(30, True), fill=ACCENT)
    panel(d, (55, 930, 1020, 370), 'Rear French cleat hooks — one section')
    paste_mesh(im, rear, (100, 997, 930, 270), eye=(.45, -.45, 1.4))
    panel(d, (1105, 930, 640, 370), 'Tools rest on the floor')
    d.text((1135, 999), '16–24 mm clear bay widths', font=font(29, True), fill=INK)
    d.text((1135, 1052), f"{p['height']:g} mm high / {p['depth']:g} mm floor depth", font=font(25), fill=MUTED)
    d.text((1135, 1102), 'Each tray mounts independently', font=font(25), fill=MUTED)
    d.text((1135, 1152), f"{module.extents[0]:g} mm wide per section", font=font(25), fill=MUTED)
    d.text((1135, 1202), f"{module.extents[2]:g} mm total depth, including cleat", font=font(25), fill=MUTED)
    footer(d, 1350)
    im.save(OUT/'Mounted_Preview.png')
    print(OUT/'Mounted_Preview.png', flush=True)

    im, d = page('One 8-bay upright tray',
                 'Closed floor  /  Tall dividers  /  Front retaining lip  /  French cleat hooks',
                 (1600, 1150))
    panel(d, (55, 170, 1490, 780), 'Actual CAD geometry')
    paste_mesh(im, module, (100, 240, 1400, 615), eye=(.4, .62, 1.5))
    d.text((95, 886), labels, font=font(31, True), fill=ACCENT)
    d.text((65, 995), f'{module.extents[0]:g} mm wide × {module.extents[1]:g} mm high × {module.extents[2]:g} mm total depth',
           font=font(29), fill=INK)
    footer(d, 1080)
    im.save(OUT/'Section_Preview.png')

    im, d = page('Check tool fit with a small tray',
                 'Three bay widths: 16, 20 and 24 mm  /  Shallow fit sample without a wall mount',
                 (1600, 1120))
    panel(d, (55, 170, 1490, 730), '3-bay sample — closed floor and front lip')
    paste_mesh(im, sample, (130, 245, 1340, 545), eye=(.3, 1., 1.5))
    d.text((95, 836), '16 mm  /  20 mm  /  24 mm clear openings', font=font(31, True), fill=ACCENT)
    d.text((65, 944), 'Check tool width and seating. This shallow sample does not test wall mounting.', font=font(27), fill=INK)
    d.text((65, 992), f'{sample.extents[0]:g} mm wide × {sample.extents[2]:g} mm deep × {sample.extents[1]:g} mm high', font=font(26), fill=MUTED)
    footer(d, 1059)
    im.save(OUT/'Fit_Sample_Preview.png')

    printing = trimesh.load(OUT/(info['projects']['full']['stem']+'.stl'), force='mesh')
    printing.vertices = printing.vertices @ np.array([[1,0,0],[0,0,1],[0,-1,0]], float).T
    im, d = page('Two trays on one print plate',
                 'Upright, floor down  /  PLA Basic  /  Left nozzle  /  Supports required behind the cleat hooks',
                 (1800, 1280))
    panel(d, (55, 170, 1690, 880), 'Actual print orientation — support material omitted from this CAD view')
    paste_mesh(im, printing, (105, 255, 1590, 725), eye=(.65, 1.5, 1.35))
    d.text((65, 1100), 'Print both sections together, or use the separate one-section project.', font=font(29), fill=INK)
    footer(d, 1195)
    im.save(OUT/'Print_Preview.png')
    for name in ('Section_Preview.png','Fit_Sample_Preview.png','Print_Preview.png'):
        print(OUT/name)


if __name__ == '__main__':
    main()
