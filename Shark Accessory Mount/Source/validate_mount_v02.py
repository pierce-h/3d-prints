"""Slice the one-piece cabinet mount with the existing checked CLI workflow."""
from pathlib import Path
import argparse
import hashlib
import json
import validate_mount_v01 as base
from build_mount_v02 import OUT,STEM


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--slice',action='store_true')
    parser.add_argument('--finalize',action='store_true')
    args=parser.parse_args()
    base.OUT=OUT
    base.TEMP=Path('/tmp/shark-accessory-v02')
    if args.slice:base.slice_project('full',STEM,1)
    if args.finalize:
        assert json.loads((OUT/'Validation/full/summary.json').read_text())['return_code']==0
        hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT.iterdir() if p.suffix in ('.3mf','.stl','.png')}
        (OUT/'Validation/archive_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')


if __name__=='__main__':main()
