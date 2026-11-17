"""Render v02 exported jigs and the Claybourne rail-alignment geometry.

CAD previews use the actual exported STL meshes. The placement drawing is a
dimensioned front-view schematic; concentric circles represent the published
knob face/base diameters, not a modeled copy of the knob's sculpted profile.
"""
from pathlib import Path
from fractions import Fraction
import math
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

from build_jig_v02 import OUT, P

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'Pliers Holder/Source'))
from render_previews import page, panel, paste_mesh, font, INK, MUTED, ACCENT
from render_jig_v01 import centered, arrow, dashed, cross

SIDE = P['side_offset']
END = P['end_offset']
FRAME = P['nominal_stile_rail_width']
PLATE_W = P['plate_width']
PLATE_H = P['plate_length']
BORE = P['printed_guide_diameter']
BASE = P['knob_base_diameter']
FACE = P['knob_face_diameter']
WOOD = '#eee4d3'
PANEL = '#faf7f1'
JIG = '#a9c9d6'
JIG_LINE = '#37697f'
ORANGE = '#ad641f'
GHOST = '#7a838d'


def inches(mm):
    """Use an exact common fraction only when the millimetres support it."""
    value = mm / 25.4
    frac = Fraction(value).limit_denominator(64)
    if abs(float(frac) - value) > 1e-5:
        return f'{value:.3f}'.rstrip('0').rstrip('.') + '″'
    whole, num = divmod(frac.numerator, frac.denominator)
    if num == 0:
        return f'{whole}″'
    glyph = {(1, 2): '½', (1, 4): '¼', (3, 4): '¾',
             (1, 8): '⅛', (3, 8): '⅜', (5, 8): '⅝', (7, 8): '⅞'}.get((num, frac.denominator))
    suffix = glyph or f'{num}/{frac.denominator}'
    if whole:
        return f'{whole}{"" if glyph else " "}{suffix}″'
    return suffix + '″'


def mm_label(mm):
    return f'{mm:.2f}'.rstrip('0').rstrip('.') + ' mm'


def dashed_circle(d, center, radius, fill=GHOST, width=3):
    x, y = center
    box = (x-radius, y-radius, x+radius, y+radius)
    for start in range(0, 360, 16):
        d.arc(box, start=start, end=start+9, fill=fill, width=width)


def actual_preview():
    a = trimesh.load(OUT / 'Validation/Jig_A_Installed.stl', force='mesh')
    b = trimesh.load(OUT / 'Validation/Jig_B_Installed.stl', force='mesh')
    # Proper rotation exposes Z=0 without a reflection that reverses handedness.
    front_rotation = np.diag([1., -1., -1., 1.])
    a.apply_transform(front_rotation)
    b.apply_transform(front_rotation)
    im, d = page('Cabinet knob drilling jig — Claybourne',
                 f'{inches(SIDE)} from the side  /  {inches(END)} from the end  /  3⁄16″ drill bit',
                 (1800, 1220))
    for x, mesh, title, uses in [
        (55, a, 'A — one identification groove', 'Top-left or bottom-right corner'),
        (925, b, 'B — two identification grooves', 'Top-right or bottom-left corner')]:
        panel(d, (x, 170, 820, 690), title)
        d.text((x+30, 230), 'Drill-entry side shown', font=font(25), fill=MUTED)
        paste_mesh(im, mesh, (x+60, 280, 700, 450), eye=(.35, .65, 1.7))
        centered(d, (x+410, 765), uses, 27, True, ACCENT)
        centered(d, (x+410, 806), 'The opposite face and edge stops sit against the door.', 21, False, MUTED)
    panel(d, (55, 890, 1690, 235), 'Two mirrored jigs, one print plate')
    d.text((90, 950), f'Hole center: {mm_label(SIDE)} from the side / {mm_label(END)} from the end.',
           font=font(29), fill=INK)
    d.text((90, 1001), 'Placement aligns the Claybourne mounting-base edge with a nominal 2½″ rail.',
           font=font(27), fill=MUTED)
    d.text((90, 1052), 'All-plastic 5.05 mm guide. Confirm drill fit and placement on scrap before use.',
           font=font(27), fill=MUTED)
    d.text((65, 1160), 'v02 · Actual CAD surfaces · PLA / left nozzle · Physical fit untested',
           font=font(24), fill=MUTED)
    im.save(OUT / 'Preview.png')


def mini_door(d, box, corner, jig):
    x, y, w, h = box
    scale = .68
    f = FRAME * scale
    d.rounded_rectangle((x, y, x+w, y+h), 6, fill=WOOD, outline='#b4a68e', width=2)
    d.rectangle((x+f, y+f, x+w-f, y+h-f), fill=PANEL, outline='#c8baa2', width=2)
    sx = 1 if 'left' in corner else -1
    sy = 1 if 'top' in corner else -1
    ox = x if sx == 1 else x+w
    oy = y if sy == 1 else y+h
    bx = (ox, ox+sx*PLATE_W*scale)
    by = (oy, oy+sy*PLATE_H*scale)
    d.rectangle((min(bx), min(by), max(bx), max(by)), fill=JIG, outline=JIG_LINE, width=2)
    d.line([(ox-sx*3, oy), (ox-sx*3, oy+sy*PLATE_H*scale)], fill=JIG_LINE, width=5)
    d.line([(ox, oy-sy*3), (ox+sx*PLATE_W*scale, oy-sy*3)], fill=JIG_LINE, width=5)
    cross(d, (ox+sx*SIDE*scale, oy+sy*END*scale), 4)
    centered(d, (x+w/2, y+h+13), f'{jig} · {corner}', 22, True)


def usage_diagram():
    assert abs(END - FRAME - BASE/2) < 1e-6
    im, d = page('Claybourne knob — revised hole position',
                 'Mounting-base edge aligned with the rail  /  Door viewed from the front',
                 (1800, 1510))
    panel(d, (55, 170, 1690, 865), 'Base cabinet: top-left corner, Jig A')
    # Exact 4 pixels per millimetre. The top and left door edges are the datums.
    scale = 4.
    ox, oy = 250, 310
    right, bottom = 1010, 900
    inner_x, rail_y = ox+FRAME*scale, oy+FRAME*scale
    hx, hy = ox+SIDE*scale, oy+END*scale
    rb, rf = BASE*scale/2, FACE*scale/2
    d.rectangle((ox, oy, right, bottom), fill=WOOD, outline='#b4a68e', width=3)
    d.rectangle((inner_x, rail_y, right, bottom), fill=PANEL, outline='#c8baa2', width=2)
    centered(d, ((inner_x+right)/2, 401), 'Top rail', 28, True, MUTED)
    centered(d, (ox+FRAME*scale/2, 401), 'Stile', 28, True, MUTED)
    centered(d, ((inner_x+right)/2, 835), 'Recessed panel', 25, False, MUTED)

    # Light, dimensionally accurate contact footprint of the printed jig.
    overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((ox, oy, ox+PLATE_W*scale, oy+PLATE_H*scale),
                 fill=(90, 145, 170, 30), outline=JIG_LINE, width=2)
    im.paste(overlay, (0, 0), overlay)
    d = ImageDraw.Draw(im)
    d.line([(ox-6, oy+PLATE_H*scale), (ox-6, oy-6), (ox+PLATE_W*scale, oy-6)],
           fill=JIG_LINE, width=9)

    # Extending the inner rail edge makes the tangent relationship explicit.
    dashed(d, (ox+5, rail_y), (inner_x, rail_y), ORANGE, 3, 10)
    d.line([(inner_x, rail_y), (right, rail_y)], fill=ORANGE, width=3)
    d.text((inner_x+26, rail_y-42), 'Inner edge of rail', font=font(25, True), fill=ORANGE)
    dashed_circle(d, (hx, hy), rf)
    d.ellipse((hx-rb, hy-rb, hx+rb, hy+rb), fill='#dbeaf1', outline=JIG_LINE, width=4)
    cross(d, (hx, hy), BORE*scale/2)
    d.ellipse((hx-6, rail_y-6, hx+6, rail_y+6), fill=ORANGE)

    # Separate leaders preserve the distinction between base and knob face.
    by = hy + max(15, rb*.45)
    start = (hx + rb*.86, by)
    d.line([start, (580, hy+15), (630, hy+15)], fill=JIG_LINE, width=2)
    d.text((645, hy-1), f'Mounting base: Ø {inches(BASE)}', font=font(25, True), fill=JIG_LINE)
    d.text((645, hy+34), 'Its top edge meets the rail line.', font=font(23), fill=MUTED)
    fy = hy + max(rf, rb) + 65
    d.line([(hx, hy+rf), (520, fy), (630, fy)], fill=GHOST, width=2)
    d.text((645, fy-15), f'Knob face: Ø {inches(FACE)}', font=font(25), fill=GHOST)

    # Hole offsets are measured to the screw axis from actual door-edge datums.
    dx = 185
    for yy in (oy, hy):
        d.line([(dx-16, yy), (ox-15, yy)], fill=ACCENT, width=2)
    arrow(d, (dx, oy), (dx, hy), both=True)
    centered(d, (121, (oy+hy)/2-36), inches(END), 30, True, ACCENT)
    centered(d, (121, (oy+hy)/2+6), mm_label(END).removesuffix(' mm'), 23, False, MUTED)
    centered(d, (121, (oy+hy)/2+36), 'mm', 22, False, MUTED)
    dashed(d, (hx, hy+12), (hx, 946), ACCENT, 2)
    d.line([(ox, 920), (ox, 972)], fill=ACCENT, width=2)
    arrow(d, (ox, 950), (hx, 950), both=True)
    centered(d, ((ox+hx)/2, 969), f'{inches(SIDE)}  /  {mm_label(SIDE)}', 24, True, ACCENT)

    # Plain-language explanation and a complete calculation beside the drawing.
    tx = 1085
    d.text((tx, 280), 'Screw-center offsets', font=font(31, True), fill=INK)
    d.text((tx, 347), 'From side edge', font=font(25), fill=MUTED)
    d.text((tx, 385), f'{inches(SIDE)}  /  {mm_label(SIDE)}', font=font(34, True), fill=ACCENT)
    d.text((tx, 460), 'From top or bottom edge', font=font(25), fill=MUTED)
    d.text((tx, 498), f'{inches(END)}  /  {mm_label(END)}', font=font(34, True), fill=ACCENT)
    d.text((tx, 573), 'Rail width + half the base diameter', font=font(25, True), fill=INK)
    d.text((tx, 614), f'{mm_label(FRAME)} + {mm_label(BASE/2)} = {mm_label(END)}',
           font=font(25), fill=MUTED)
    d.text((tx, 694), 'The screw center moves past the rail', font=font(25), fill=INK)
    d.text((tx, 731), 'line by the mounting base’s radius.', font=font(25), fill=INK)
    d.text((tx, 803), 'Assumes an actual 2½″ stile and rail.', font=font(24), fill=MUTED)
    d.text((tx, 842), 'Check that frame width on your doors.', font=font(24), fill=MUTED)
    d.text((tx, 916), 'Knob circles are a dimensioned schematic.', font=font(22), fill=MUTED)
    d.text((tx, 949), 'Blue outline shows the jig footprint.', font=font(22), fill=MUTED)

    panel(d, (55, 1055, 1690, 350), 'Use one guide at the corner opposite the hinges')
    centered(d, (480, 1110), 'Base cabinets — top corners', 26, True)
    centered(d, (1320, 1110), 'Upper cabinets — bottom corners', 26, True)
    for x, corner, jig in [(225, 'top-left', 'A'), (600, 'top-right', 'B'),
                           (1065, 'bottom-left', 'B'), (1440, 'bottom-right', 'A')]:
        mini_door(d, (x, 1157, 155, 170), corner, jig)
    d.text((65, 1435), 'v02 · Test the printed guide and placement on scrap. Clamp the jig and a backer before drilling.',
           font=font(25), fill=MUTED)
    im.save(OUT / 'Placement_Diagram.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    actual_preview()
    usage_diagram()
    print(OUT / 'Preview.png')
    print(OUT / 'Placement_Diagram.png')


if __name__ == '__main__':
    main()
