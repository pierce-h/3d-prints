"""Reproducible orthographic previews rasterized from the final STL triangles.

No modeled geometry is changed. Installed axes are X along wall, Y up,
Z toward the user. Render colors are illustrative; all openings and ribs
are the actual model surfaces. Requires numpy, trimesh and Pillow.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Revisions/v01-16-slot'
BG = '#f2f4f6'
INK = '#183543'
MUTED = '#536875'
ACCENT = '#467c91'
FONT_ROOT = Path('/System/Library/Fonts/Supplemental')


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_ROOT / ('Arial Bold.ttf' if bold else 'Arial.ttf')), size)


def normalized(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def render(mesh, size, eye=(.24, 1., 1.4), margin=15):
    """Orthographic, back-face culled, depth-buffered, 2x antialiased mesh."""
    ss = 2
    width, height = [int(x * ss) for x in size]
    toward_eye = normalized(eye)
    right = normalized(np.cross((0, 1, 0), toward_eye))
    up = normalized(np.cross(toward_eye, right))
    basis = np.column_stack((right, up, toward_eye))
    projected = mesh.vertices @ basis
    lo, hi = projected[:, :2].min(0), projected[:, :2].max(0)
    scale = min((width - 2 * margin * ss) / (hi[0] - lo[0]),
                (height - 2 * margin * ss) / (hi[1] - lo[1]))
    projected[:, 0] = width / 2 + (projected[:, 0] - (lo[0] + hi[0]) / 2) * scale
    projected[:, 1] = height / 2 - (projected[:, 1] - (lo[1] + hi[1]) / 2) * scale
    triangles = projected[mesh.faces]
    normals = mesh.face_normals
    depth = np.full((height, width), -np.inf)
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    key, fill = normalized((-.55, 1., 1.2)), normalized((.8, .1, -.4))
    base = np.array((118., 157., 175.))
    for tri, normal in zip(triangles, normals):
        if np.dot(normal, toward_eye) <= 1e-7:
            continue
        x0, y0 = np.maximum(np.floor(tri[:, :2].min(0)), 0).astype(int)
        x1, y1 = np.minimum(np.ceil(tri[:, :2].max(0)), (width-1, height-1)).astype(int)
        if x1 < x0 or y1 < y0:
            continue
        xx, yy = np.meshgrid(np.arange(x0, x1+1)+.5, np.arange(y0, y1+1)+.5)
        a, b, c = tri
        den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-9:
            continue
        wa = ((b[1]-c[1])*(xx-c[0]) + (c[0]-b[0])*(yy-c[1])) / den
        wb = ((c[1]-a[1])*(xx-c[0]) + (a[0]-c[0])*(yy-c[1])) / den
        wc = 1-wa-wb
        zz = wa*a[2]+wb*b[2]+wc*c[2]
        zslice = depth[y0:y1+1, x0:x1+1]
        take = (wa >= -1e-7) & (wb >= -1e-7) & (wc >= -1e-7) & (zz >= zslice)
        if not take.any():
            continue
        brightness = .44 + .50*max(0, normal@key) + .14*max(0, normal@fill)
        color = np.r_[np.clip(base*brightness, 0, 255).astype(np.uint8), 255]
        zslice[take] = zz[take]
        rgba[y0:y1+1, x0:x1+1][take] = color
    return Image.fromarray(rgba).resize(size, Image.Resampling.LANCZOS)


def paste_mesh(canvas, mesh, box, eye=(.24, 1., 1.4)):
    x, y, w, h = box
    im = render(mesh, (w, h), eye)
    # A faint screen-space shadow separates the model from the page only.
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    shadow.putalpha(im.getchannel('A').point(lambda a: int(a*.11)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(shadow, (x+3, y+10), shadow)
    canvas.paste(im, (x, y), im)


def page(title, subtitle, size=(1800, 1180)):
    im = Image.new('RGB', size, BG)
    d = ImageDraw.Draw(im)
    d.text((65, 42), title, font=font(49, True), fill=INK)
    d.text((67, 107), subtitle, font=font(27), fill=MUTED)
    return im, d


def panel(draw, box, title):
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x+w, y+h), 22, fill='white')
    draw.text((x+28, y+22), title, font=font(27, True), fill=INK)


def main():
    info = json.loads((OUT/'Validation/geometry.json').read_text())
    params = info['parameters_mm']
    module = trimesh.load(OUT/'Validation/Module_Installed.stl', force='mesh')
    sample = trimesh.load(OUT/'Validation/Fit_Sample_Installed.stl', force='mesh')
    second = module.copy()
    second.apply_translation((info['module']['width'] + info['parameters_mm']['wall_gap_between_modules'], 0, 0))
    pair = trimesh.util.concatenate((module, second))

    total_width = 2 * info['module']['width'] + params['wall_gap_between_modules']
    slot_labels = '  ·  '.join(str(int(w)) for w in info['module']['slot_widths']) + ' mm'
    slot_range = f"{min(info['module']['slot_widths']):g}–{max(info['module']['slot_widths']):g} mm"
    im, d = page('16-slot French cleat pliers rack',
                 f"Two separate 8-slot sections  /  {total_width:g} mm overall with a {params['wall_gap_between_modules']:g} mm gap")
    panel(d, (55, 170, 1690, 490), 'Installed arrangement')
    paste_mesh(im, pair, (85, 240, 1630, 315), eye=(.16, 1.15, 1.4))
    d.text((95, 595), slot_labels, font=font(26, True), fill=ACCENT)
    d.text((930, 595), slot_labels, font=font(26, True), fill=ACCENT)
    panel(d, (55, 690, 1020, 365), 'Underside of one section')
    paste_mesh(im, module, (80, 753, 970, 265), eye=(.28, -.8, 1.5))
    panel(d, (1105, 690, 640, 365), 'Sized for a mixed collection')
    d.text((1135, 760), slot_range + ' open-front slots', font=font(29, True), fill=INK)
    d.text((1135, 812), f"{params['shelf_thickness']:g} mm shelf with a rib under each finger", font=font(25), fill=MUTED)
    d.text((1135, 861), 'Each section has its own rear cleat hooks', font=font(25), fill=MUTED)
    d.text((1135, 910), f'{module.extents[0]:g} mm wide × {module.extents[1]:g} mm high', font=font(25), fill=MUTED)
    d.text((1135, 956), f'{module.extents[2]:g} mm total depth, including cleat', font=font(25), fill=MUTED)
    d.text((65, 1095), 'Prototype v01 · Actual CAD geometry · Physical tool fit, cleat fit and loaded use untested',
           font=font(24), fill=MUTED)
    im.save(OUT/'Mounted_Preview.png')

    im, d = page('One 8-slot section',
                 f'{slot_range} slot widths  /  Independent French cleat mounting', (1600, 1040))
    panel(d, (55, 170, 1490, 700), 'Actual CAD geometry')
    paste_mesh(im, module, (90, 245, 1420, 525), eye=(.24, 1., 1.4))
    d.text((95, 805), slot_labels, font=font(31, True), fill=ACCENT)
    d.text((65, 920), f'{module.extents[0]:g} mm wide × {module.extents[1]:g} mm high × {module.extents[2]:g} mm total depth', font=font(29), fill=INK)
    d.text((65, 988), 'Prototype v01 · Physical tool fit, cleat fit and loaded use untested', font=font(23), fill=MUTED)
    im.save(OUT/'Section_Preview.png')

    im, d = page('Try the fit before printing the full rack',
                 'Handheld fit gauge  /  Three representative slot widths from the full shelf', (1600, 1050))
    panel(d, (55, 170, 1490, 660), '3-slot fit sample — no wall mount')
    paste_mesh(im, sample, (160, 255, 1280, 495), eye=(.24, 1., 1.4))
    d.text((92, 769), '12 mm narrow  /  20 mm medium  /  26 mm wide', font=font(30, True), fill=ACCENT)
    d.text((65, 870), 'Check that each tool rests on its joint/head and can lift out freely.', font=font(29), fill=INK)
    d.text((65, 920), 'This thin sample checks tool fit; it does not test the wall mounting or strength.', font=font(27), fill=MUTED)
    d.text((65, 984), 'Prototype v01 · Actual CAD geometry · Physical tool fit untested', font=font(23), fill=MUTED)
    im.save(OUT/'Fit_Sample_Preview.png')

    printing = trimesh.load(OUT/'Pliers_Rack_v01_16_Slots_PLA_Left_TEST_FIT.stl', force='mesh')
    # Rigid conversion from print XYZ to this renderer's X/right,Y/up,Z/front.
    printing.vertices = printing.vertices @ np.array([[1,0,0],[0,0,1],[0,-1,0]], float).T
    im, d = page('Two sections on one print plate',
                 'Shelf faces down  /  PLA Basic  /  Left nozzle  /  Supports disabled', (1600, 1150))
    panel(d, (55, 170, 1490, 800), 'Actual print orientation')
    paste_mesh(im, printing, (110, 250, 1380, 655), eye=(.55, 1.3, 1.3))
    d.text((65, 1013), 'Print both sections together, or use the separate one-section project.', font=font(29), fill=INK)
    d.text((65, 1085), 'Prototype v01 · Actual CAD geometry · Physical tool fit, cleat fit and loaded use untested', font=font(23), fill=MUTED)
    im.save(OUT/'Print_Preview.png')
    print('\n'.join(str(OUT/name) for name in ('Mounted_Preview.png','Section_Preview.png','Fit_Sample_Preview.png','Print_Preview.png')))


if __name__ == '__main__':
    main()
