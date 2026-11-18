"""Render the exported drawer jig and a dimensioned placement schematic.

The CAD views use the final STL triangles. Blue shading is illustrative; it is
not a prediction of the clear PETG's appearance. The drawer sketch is a usage
diagram, with an illustrative drawer width and the confirmed 63.5 mm top rail.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v01-single-edge'
STEM = 'Drawer_Knob_Jig_v01_Single_Edge_Clear_PETG_Right_TEST_FIT'
sys.path.insert(0, str(ROOT.parent / 'Pliers Holder/Source'))
from render_previews import page, panel, paste_mesh, font, INK, MUTED, ACCENT

RAIL = 63.5
OFFSET = 31.75
WIDTH = 80.0
LENGTH = 55.0
GUIDE = 5.05
WOOD = '#eee4d3'
PANEL = '#faf7f1'
BLUE = '#37697f'
ORANGE = '#b56c28'


def centered(draw, point, text, size=26, bold=False, fill=INK):
    f = font(size, bold)
    box = draw.textbbox((0, 0), text, font=f)
    draw.text((point[0]-(box[2]-box[0])/2, point[1]), text, font=f, fill=fill)


def dashed(draw, a, b, fill=MUTED, width=2, dash=12):
    delta = np.array(b, float) - a
    length = np.linalg.norm(delta)
    if not length:
        return
    unit = delta / length
    for start in np.arange(0, length, dash*2):
        end = min(start+dash, length)
        draw.line([tuple(np.array(a)+unit*start), tuple(np.array(a)+unit*end)], fill=fill, width=width)


def dim(draw, a, b, color=ACCENT, width=3):
    draw.line([a, b], fill=color, width=width)
    direction = np.array(b, float) - a
    direction /= np.linalg.norm(direction)
    side = np.array([-direction[1], direction[0]])
    for point, inward in [(np.array(a), direction), (np.array(b), -direction)]:
        base = point + inward*10
        draw.polygon([tuple(point), tuple(base+side*5), tuple(base-side*5)], fill=color)


def actual_preview(mesh):
    im, draw = page('Drawer knob drilling jig',
                    'One top-edge stop  /  1¼″ hole offset  /  3⁄16″ drill bit',
                    (1800, 1130))
    front = mesh.copy()
    # Rotate, do not reflect: the exposed drill face (local Z=0) faces the eye.
    front.apply_transform(np.diag([1., -1., -1., 1.]))
    back = mesh.copy()
    # Proper in-plane rotation puts the top stop at the back of this view.
    back.apply_transform(np.diag([-1., -1., 1., 1.]))
    panel(draw, (55, 175, 820, 650), 'Drill-entry face')
    panel(draw, (925, 175, 820, 650), 'Back: single straight stop')
    paste_mesh(im, front, (100, 255, 725, 430), eye=(.24, .5, 1.7))
    paste_mesh(im, back, (970, 255, 725, 430), eye=(.3, .65, 1.6))
    draw = ImageDraw.Draw(im)
    centered(draw, (465, 730), 'Centerline + V-shaped sight notch', 27, True, ACCENT)
    centered(draw, (1335, 730), 'Slides left and right along the drawer', 27, True, ACCENT)
    centered(draw, (465, 775), 'Line up with your drawer-center pencil mark.', 22, False, MUTED)
    centered(draw, (1335, 775), 'The stop sets the distance from the top edge.', 22, False, MUTED)
    panel(draw, (55, 850, 1690, 190), 'Sized for the confirmed 2½″ top rail')
    draw.text((90, 913), 'Hole center: 1¼″ / 31.75 mm below the top edge.', font=font(30, True), fill=INK)
    draw.text((90, 964), '80 × 59 × 20 mm overall  ·  Same 5.05 mm printed guide as the successful door jig.',
              font=font(25), fill=MUTED)
    draw.text((65, 1070), 'v01 · Actual CAD geometry · Illustrative color · New drawer jig not yet physically tested',
              font=font(24), fill=MUTED)
    im.save(OUT / 'Preview.png')


def placement_diagram():
    im, draw = page('Center the knob on the drawer’s top rail',
                    'You set the left-to-right center; the jig sets the drilling height.',
                    (1800, 1300))
    panel(draw, (55, 175, 1690, 720), 'Front view — drawer width is illustrative')
    scale = 4.0
    ox, oy, right, bottom = 180, 310, 1120, 790
    middle = (ox+right)/2
    rail_bottom = oy+RAIL*scale
    hole_y = oy+OFFSET*scale
    jig_left = middle-WIDTH*scale/2
    jig_right = middle+WIDTH*scale/2
    jig_bottom = oy+LENGTH*scale
    draw.rectangle((ox, oy, right, bottom), fill=WOOD, outline='#b4a68e', width=3)
    draw.rectangle((ox+100, rail_bottom, right-100, bottom), fill=PANEL, outline='#c8baa2', width=2)
    centered(draw, (middle, 734), 'Drawer panel', 26, False, MUTED)
    draw.text((ox+25, oy+95), 'Top rail', font=font(26, True), fill=MUTED)
    # Pencil datum extends across the rail and below the jig's free edge.
    dashed(draw, (middle, oy-55), (middle, rail_bottom+47), ORANGE, 3, 8)
    # Transparent footprint is schematic; its outline includes the actual notch.
    overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    footprint = [(jig_left, oy), (jig_right, oy), (jig_right, jig_bottom),
                 (middle+1.5*scale, jig_bottom), (middle, oy+52*scale),
                 (middle-1.5*scale, jig_bottom), (jig_left, jig_bottom)]
    od.polygon(footprint, fill=(103, 160, 186, 85), outline=BLUE, width=3)
    im.paste(overlay, (0, 0), overlay)
    draw = ImageDraw.Draw(im)
    draw.rectangle((jig_left, oy-4*scale, jig_right, oy), fill=BLUE)
    # Reproduce the two centerline segments shown on the exposed face.
    draw.line([(middle, oy+4*scale), (middle, oy+27*scale)], fill=BLUE, width=3)
    draw.line([(middle, oy+36.5*scale), (middle, oy+52*scale)], fill=BLUE, width=3)
    r = GUIDE*scale/2
    draw.ellipse((middle-r, hole_y-r, middle+r, hole_y+r), fill=PANEL, outline=BLUE, width=3)
    draw.line([(middle-17, hole_y), (middle+17, hole_y)], fill=BLUE, width=2)
    draw.line([(middle, hole_y-17), (middle, hole_y+17)], fill=BLUE, width=2)
    # Full rail and half rail dimension lines, separated from the alignment mark.
    dx = 123
    for y in [oy, rail_bottom]:
        draw.line([(dx-10, y), (ox-13, y)], fill=ACCENT, width=2)
    dim(draw, (dx, oy), (dx, rail_bottom))
    centered(draw, (123, rail_bottom+22), '2½″', 28, True, ACCENT)
    centered(draw, (123, rail_bottom+59), '63.5 mm', 21, False, MUTED)
    dx2 = jig_right+65
    for y in [oy, hole_y]:
        draw.line([(jig_right+12, y), (dx2+12, y)], fill=ACCENT, width=2)
    dim(draw, (dx2, oy), (dx2, hole_y))
    draw.text((dx2+18, (oy+hole_y)/2-31), '1¼″', font=font(30, True), fill=ACCENT)
    draw.text((dx2+18, (oy+hole_y)/2+10), '31.75 mm', font=font(22), fill=MUTED)
    # Notch alignment leader avoids the measurement arrows.
    draw.line([(middle+8, jig_bottom-3), (858, 623), (950, 623)], fill=ORANGE, width=2)
    draw.text((960, 604), 'Sight notch', font=font(24, True), fill=ORANGE)
    centered(draw, (middle, 834), 'Pencil line at the drawer’s midpoint', 25, True, ORANGE)
    tx = 1190
    draw.text((tx, 295), 'How it registers', font=font(31, True), fill=INK)
    instructions = [
        ('Top stop', 'Rests against the drawer’s', 'outer top edge.'),
        ('Center mark', 'Slide sideways until the notch', 'matches your pencil line.'),
        ('Guide hole', 'Centered vertically on the', 'confirmed 2½″ rail.'),
    ]
    for y, (heading, line1, line2) in zip([366, 500, 634], instructions):
        draw.text((tx, y), heading, font=font(27, True), fill=BLUE)
        draw.text((tx, y+43), line1, font=font(24), fill=MUTED)
        draw.text((tx, y+78), line2, font=font(24), fill=MUTED)
    draw.text((tx, 814), 'Jig footprint shown transparent.', font=font(21), fill=MUTED)
    panel(draw, (55, 925, 1690, 270), 'Simple setup')
    for x, number, title, line in [
        (90, '1', 'Mark the drawer midpoint', 'Draw a short vertical pencil line on the rail.'),
        (650, '2', 'Seat and align the jig', 'Top stop flush; sight notch on the pencil line.'),
        (1210, '3', 'Clamp and drill', 'Use the same 3⁄16″ bit and a scrap backer.'),
    ]:
        draw.ellipse((x, 1001, x+44, 1045), fill=BLUE)
        centered(draw, (x+22, 1006), number, 27, True, 'white')
        draw.text((x, 1065), title, font=font(26, True), fill=INK)
        # Two deliberately short lines avoid crowded columns.
        phrases = {
            '1': ['Draw a vertical pencil line', 'at the rail’s left-to-right center.'],
            '2': ['Top stop flush; sight notch', 'on your pencil line.'],
            '3': ['Use the same 3⁄16″ bit', 'and a scrap backer.'],
        }[number]
        for yy, phrase in zip([1107, 1141], phrases):
            draw.text((x, yy), phrase, font=font(23), fill=MUTED)
    draw.text((65, 1230), 'v01 · Fixed 31.75 mm offset for a 63.5 mm rail · Check seating and center alignment before drilling.',
              font=font(24), fill=MUTED)
    im.save(OUT / 'Placement_Diagram.png')


def embed():
    path = OUT / (STEM + '.3mf')
    with ZipFile(path) as archive:
        data = {name: archive.read(name) for name in archive.namelist()}
    png = (OUT / 'Preview.png').read_bytes()
    for key in ['Metadata/plate_1.png', 'Metadata/plate_no_light_1.png',
                'Metadata/plate_1_small.png', 'Auxiliaries/.thumbnails/thumbnail_3mf.png']:
        data[key] = png
    with ZipFile(path, 'w', ZIP_DEFLATED) as archive:
        for name, value in data.items():
            archive.writestr(name, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--embed', action='store_true', help='Embed preview PNGs in the saved project only.')
    args = parser.parse_args()
    mesh = trimesh.load(OUT / 'Validation/Jig_Local.stl', force='mesh')
    assert np.allclose(mesh.bounds, [[0, -4, 0], [80, 55, 20]], atol=1e-5)
    actual_preview(mesh)
    placement_diagram()
    if args.embed:
        embed()
    print(OUT / 'Preview.png')
    print(OUT / 'Placement_Diagram.png')


if __name__ == '__main__':
    main()
