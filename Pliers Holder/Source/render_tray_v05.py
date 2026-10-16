"""Actual-STL previews for the single-piece 16-bay v05 pliers tray.

The print view uses the exported placement and the verified bed bounds in
geometry.json. Display rotations do not change printable model geometry.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from PIL import ImageDraw
from render_previews import page, panel, paste_mesh, render, normalized, font, INK, MUTED, ACCENT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v05-wide-left'
PRINT_TO_RENDER = np.array([[1,0,0],[0,0,1],[0,-1,0]], float)


def footer(draw, y):
    draw.text((65, y), 'Prototype v05 · Actual CAD geometry · Physical fit and loaded use untested',
              font=font(24), fill=MUTED)


def rectangle(bounds):
    (x0, y0), (x1, y1) = np.asarray(bounds, float)
    return np.array([(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)], float)


def plate_view(canvas, printing, box, bed_bounds, left_bounds, exclusion_bounds, eye):
    """Render placed triangles over an exact, same-scale bed/grid projection."""
    x, y, w, h = box
    corners = rectangle(bed_bounds) @ PRINT_TO_RENDER.T
    placed = printing.copy()
    placed.vertices = placed.vertices @ PRINT_TO_RENDER.T
    # Unreferenced bed corners extend framing only, without adding surfaces.
    framed = trimesh.Trimesh(np.vstack((placed.vertices, corners)), placed.faces, process=False)
    toward = normalized(eye)
    right = normalized(np.cross((0,1,0), toward))
    up = normalized(np.cross(toward, right))
    basis = np.column_stack((right, up, toward))
    projected = framed.vertices @ basis
    lo, hi = projected[:, :2].min(0), projected[:, :2].max(0)
    scale = min((w-30)/(hi[0]-lo[0]), (h-30)/(hi[1]-lo[1]))

    def points(print_xyz):
        p = np.asarray(print_xyz, float) @ PRINT_TO_RENDER.T @ basis
        return [(x+w/2+(v[0]-(lo[0]+hi[0])/2)*scale,
                 y+h/2-(v[1]-(lo[1]+hi[1])/2)*scale) for v in p]

    d = ImageDraw.Draw(canvas)
    plate = points(rectangle(bed_bounds))
    d.polygon(plate, fill='#e9edef')
    d.line(plate+[plate[0]], fill='#7e939e', width=3)
    (x0,y0), (x1,y1) = np.asarray(bed_bounds, float)
    for gx in np.arange(np.ceil(x0/25)*25, x1, 25):
        d.line(points([(gx,y0,0),(gx,y1,0)]), fill='#d2dce1', width=1)
    for gy in np.arange(np.ceil(y0/25)*25, y1, 25):
        d.line(points([(x0,gy,0),(x1,gy,0)]), fill='#d2dce1', width=1)
    ex = np.asarray(exclusion_bounds, float).copy()
    ex[0] = np.maximum(ex[0], (x0,y0))
    ex[1] = np.minimum(ex[1], (x1,y1))
    forbidden = points(rectangle(ex))
    d.polygon(forbidden, fill='#e6c6c2')
    d.line(forbidden+[forbidden[0]], fill='#a56f66', width=2)
    usable = points(rectangle(left_bounds))
    for a,b in zip(usable,usable[1:]+usable[:1]):
        a,b=np.asarray(a),np.asarray(b)
        steps=max(1,int(np.linalg.norm(b-a)/10))
        for i in range(0,steps,2):
            d.line([tuple(a+(b-a)*i/steps),tuple(a+(b-a)*min(i+1,steps)/steps)],fill=ACCENT,width=3)
    actual = render(framed, (w,h), eye=eye)
    canvas.paste(actual,(x,y),actual)


def main():
    info = json.loads((OUT/'Validation/geometry.json').read_text())
    p = info['parameters_mm']
    module = trimesh.load(OUT/'Validation/Tray_Installed.stl', force='mesh')
    rear = module.copy()
    rear.apply_transform(np.diag((-1.,1.,-1.,1.)))
    labels = '2 × 24 mm  /  2 × 22 mm  /  4 × 20 mm  /  4 × 18 mm  /  4 × 16 mm'

    im,d=page('One-piece, 16-bay pliers holder',
              f'{module.extents[0]:g} mm wide  /  {module.extents[1]:g} mm tall  /  {p["depth"]:g} mm tray depth',
              (1800,1430))
    panel(d,(55,170,1690,730),'Widest slots on the left — narrowest on the right')
    paste_mesh(im,module,(85,245,1630,555),eye=(.25,.5,1.5))
    d.text((195,838),labels,font=font(29,True),fill=ACCENT)
    panel(d,(55,930,1020,370),'Three rear French cleat hooks')
    paste_mesh(im,rear,(100,997,930,270),eye=(.45,-.45,1.4))
    panel(d,(1105,930,640,370),'16 tool bays, up to 24 mm wide')
    d.text((1135,999),'Tall dividers and closed floor',font=font(29,True),fill=INK)
    d.text((1135,1052),f'{p["height"]:g} mm high / {p["depth"]:g} mm floor depth',font=font(25),fill=MUTED)
    d.text((1135,1102),f'{p["front_lip_height"]:g} mm front retaining lip',font=font(25),fill=MUTED)
    d.text((1135,1152),'Diagonal placement on the print bed',font=font(25),fill=MUTED)
    d.text((1135,1202),f'{module.extents[2]:g} mm total depth, including cleat',font=font(25),fill=MUTED)
    footer(d,1350)
    im.save(OUT/'Mounted_Preview.png')
    print(OUT/'Mounted_Preview.png',flush=True)

    # The root build records these verified printer bounds explicitly.
    bed=info['bed']['plate_xy']
    left=info['bed']['left_nozzle_xy']
    exclusion=info['bed']['wrapping_exclusion_xy']
    stem=info['projects']['full']['stem']
    printing=trimesh.load(OUT/(stem+'.stl'),force='mesh')
    im,d=page('One continuous holder, placed diagonally',
              'Actual exported print placement  /  PLA Basic  /  Left nozzle  /  Upright, floor down',
              (1800,1280))
    panel(d,(55,170,820,800),'Top view — bed and model footprint')
    plate_view(im,printing,(90,245,750,655),bed,left,exclusion,(0,1,1e-7))
    panel(d,(905,170,840,800),'Three-quarter view')
    plate_view(im,printing,(935,245,780,655),bed,left,exclusion,(.55,1.5,1.35))
    d.text((65,1010),'Solid: print bed   /   Dashed: left-nozzle boundary   /   Shaded: exclusion area',font=font(29),fill=INK)
    d.text((65,1065),'Rear-cleat supports and brim are omitted from these CAD views.',font=font(27),fill=MUTED)
    d.text((65,1117),'350 × 320 mm bed, shown to scale with the model.',font=font(27),fill=MUTED)
    footer(d,1195)
    im.save(OUT/'Print_Preview.png')
    print(OUT/'Print_Preview.png')


if __name__ == '__main__':
    main()
