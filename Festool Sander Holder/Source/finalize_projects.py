"""Refresh previews and archive thumbnails after build_double_holder.py.

Uses the installed Bambu Studio command-line renderer. Only a temporary copy
gets the upright display orientation and light blue preview color; printable
projects retain their saved ABS profile and top-edge-down placement.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse
import json
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CLI='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def render(source, directory, camera, profile):
    directory.mkdir(parents=True,exist_ok=True)
    command=[CLI,'--datadir',str(profile),'--debug','1','--arrange','0',
             '--orient','0','--export-png','1','--camera-view',str(camera),
             '--outputdir',str(directory),str(source)]
    result=subprocess.run(command,capture_output=True,text=True,check=True)
    (directory/'renderer.log').write_text(result.stdout+result.stderr)
    return (directory/f'plate_1_{camera}.png').read_bytes()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--revision',default='v01-double-holder-test-fit')
    args=ap.parse_args()
    out=ROOT/'Revisions'/args.revision
    report=json.loads((out/'Validation'/'geometry.json').read_text())
    with tempfile.TemporaryDirectory(prefix='festool-preview-') as temporary:
        temp=Path(temporary)
        holder=out/report['parts']['holder']['file']
        mounted=temp/'mounted-preview.3mf'
        ymax=report['parts']['holder']['bounds_installed_mm'][1][1]
        with ZipFile(holder) as source,ZipFile(mounted,'w') as dest:
            for entry in source.infolist():
                content=source.read(entry.filename)
                if entry.filename=='3D/3dmodel.model':
                    text=content.decode()
                    text=re.sub(r'(<item\b[^>]*\btransform=")[^"]*',
                        lambda m:m[1]+f'1 0 0 0 0 1 0 -1 0 175 150 {ymax}',text)
                    content=text.encode()
                elif entry.filename=='Metadata/project_settings.config':
                    settings=json.loads(content)
                    settings['filament_colour']=['#8BBAD2','#FFFFFF']
                    content=json.dumps(settings).encode()
                dest.writestr(entry,content)
        front=render(mounted,temp/'front',12,temp/'profile-front')
        rear=render(mounted,temp/'rear',10,temp/'profile-rear')
        (out/'Validation'/'Render_Front.png').write_bytes(front)
        (out/'Validation'/'Render_Back.png').write_bytes(rear)
        for key,part in report['parts'].items():
            path=out/part['file']
            # Mounted front view makes the holder recognizable in Recent Files.
            png=front if key=='holder' else render(path,temp/'coupon',0,temp/'profile-coupon')
            with ZipFile(path) as source:
                entries=source.infolist()
                content={e.filename:source.read(e.filename) for e in entries}
            content['Metadata/plate_1.png']=png
            content['Metadata/plate_1_small.png']=png
            for name in ('Auxiliaries/.thumbnails/thumbnail_3mf.png',
                         'Auxiliaries/.thumbnails/thumbnail_middle.png',
                         'Auxiliaries/.thumbnails/thumbnail_small.png'):
                if name in content:content[name]=png
            temporary_zip=temp/(key+'.3mf')
            with ZipFile(temporary_zip,'w') as dest:
                for entry in entries:dest.writestr(entry,content[entry.filename])
            path.write_bytes(temporary_zip.read_bytes())
    print('Updated holder and sample thumbnails; printable geometry/settings unchanged.')


if __name__=='__main__':main()
