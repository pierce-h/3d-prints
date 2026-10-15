"""Render the actual installed-coordinate mesh and a cleat mating diagram."""
from pathlib import Path
import json
import argparse
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--revision',default='v01-double-holder-test-fit')
args=parser.parse_args()
OUT=ROOT/'Revisions'/args.revision
mesh=trimesh.load(OUT/'Validation'/'holder_installed.stl')
report=json.loads((OUT/'Validation'/'geometry.json').read_text())
fig=plt.figure(figsize=(15,7.5),dpi=160,facecolor='#f4f6f3')
fig.text(.04,.94,'Festool double holder',fontsize=25,weight='bold',color='#243e37')
version=args.revision.split('-')[0]
style=' · Open backing frame' if report.get('back_style')=='frame' else ''
fig.text(.04,.895,f'{version} · Test-fit prototype{style} · RO 150 ROTEX + ETS EC 150/5',fontsize=13,color='#53645e')
for rect,filename,title in [([.035,.40,.46,.43],'Render_Front.png','Front — original cradle shapes'),([.51,.40,.46,.43],'Render_Back.png','Rear — continuous French cleat')]:
    ax=fig.add_axes(rect,facecolor='#f4f6f3')
    ax.imshow(Image.open(OUT/'Validation'/filename))
    ax.set_axis_off(); ax.set_title(title,fontsize=12,color='#243e37',pad=-5)
fig.text(.045,.36,'348 × 82 × 43.5 mm overall  |  20 mm between cradles  |  6 mm rear reinforcement',fontsize=12,color='#243e37')
ax=fig.add_axes([.035,.06,.37,.255],facecolor='#f4f6f3')
profile=np.array(report['cleat_profile_yz_mm'])
# Cross-section is depth horizontal and height vertical.
wall=-16-19.05
ax.add_patch(Rectangle((wall-3,-44),3,92,facecolor='#b9bebb'))
ax.add_patch(Polygon([(wall,-41),(-16,-41),(-16,8),(wall,8-19.05)],facecolor='#dcc199',edgecolor='#a7865f'))
ax.add_patch(Polygon(profile[:,[1,0]],facecolor='#577f96',edgecolor='#355669'))
ax.add_patch(Rectangle((-16,-40.992),6,81.984,facecolor='#8ba8b6',edgecolor='#355669'))
ax.annotate('Printed cleat',xy=(-27,25),xytext=(1,34),fontsize=10,color='#355669',arrowprops={'arrowstyle':'->','color':'#355669'})
ax.annotate('45° contact',xy=(-25,-1),xytext=(1,0),fontsize=10,color='#355669',arrowprops={'arrowstyle':'->','color':'#355669'})
ax.annotate('Wall cleat',xy=(-25,-25),xytext=(1,-30),fontsize=10,color='#8e6e46',arrowprops={'arrowstyle':'->','color':'#8e6e46'})
ax.set_xlim(-44,48);ax.set_ylim(-46,49);ax.set_aspect('equal');ax.axis('off')
ax.set_title('Section through a cradle center rib',fontsize=9,color='#53645e')
fig.text(.405,.27,'Print the small cleat sample first.',fontsize=15,weight='bold',color='#243e37')
fig.text(.405,.215,'Designed for nominal ¾-inch plywood with a 45° bevel.\nThe rear ribs below the bevel rest against the wall cleat’s front face.',fontsize=11,color='#53645e',linespacing=1.6)
fig.text(.405,.10,'Tool clearance, actual wall fit and loaded performance still need a physical test.\nOriginal cradle design: FortuneAU. Wall-rail height in the diagram is illustrative.',fontsize=10,color='#53645e',linespacing=1.6)
fig.savefig(OUT/'Preview.png',facecolor=fig.get_facecolor(),bbox_inches='tight')
print(OUT/'Preview.png')
