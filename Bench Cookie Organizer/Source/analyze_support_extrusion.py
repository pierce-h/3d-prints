import sys, json, math, re
from collections import defaultdict
from pathlib import Path

def parse(path):
    feats=defaultdict(lambda: {'length_mm':0.,'moves':0,'min_xyz':[float('inf')]*3,'max_xyz':[float('-inf')]*3})
    bins=defaultdict(lambda:defaultdict(float))
    relative_e=False; relative_xyz=False; current=[0.,0.,0.]; last_e=0.; feature='Custom'; layer_z=0.; layers=0
    density=1.26; diameter=1.75; total_header=None; layers_mode=set()
    for line in open(path):
        if line.startswith(';'):
            if line.startswith('; FEATURE: '): feature=line[11:].strip()
            elif line.startswith('; Z_HEIGHT: '): layer_z=float(line[12:]); layers+=1
            elif line.startswith('; filament_density: '): density=float(line.split(': ')[1].split(',')[0])
            elif line.startswith('; filament_diameter: '): diameter=float(line.split(': ')[1].split(',')[0])
            elif line.startswith('; total filament weight [g]'): total_header=float(line.split(': ')[1])
            continue
        if not (line.startswith('G') or line.startswith('M')): continue
        code=line.split(';',1)[0].strip().split()
        if not code: continue
        command=code[0]
        if command=='M83': relative_e=True; continue
        if command=='M82': relative_e=False; continue
        if command=='G90': relative_xyz=False; continue
        if command=='G91': relative_xyz=True; continue
        if command not in ('G0','G1','G2','G3','G92'): continue
        vals={}
        for tok in code[1:]:
            if tok[0] in 'XYZE':
                try: vals[tok[0]]=float(tok[1:])
                except ValueError: pass
        if command=='G92':
            for i,k in enumerate('XYZ'):
                if k in vals: current[i]=vals[k]
            if 'E' in vals: last_e=vals['E']
            continue
        new=[current[i]+vals[k] if relative_xyz else vals[k] for i,k in enumerate('XYZ') if k in vals]
        previous=current.copy()
        for i,k in enumerate('XYZ'):
            if k in vals: current[i]=(current[i] if relative_xyz else 0)+vals[k]
        if 'E' not in vals: continue
        e=vals['E'] if relative_e else vals['E']-last_e
        last_e=last_e+vals['E'] if relative_e else vals['E']
        if e<=0 or feature=='Custom' or not ('X' in vals or 'Y' in vals): continue
        if command in ('G0','G1') and current[0]==previous[0] and current[1]==previous[1]: continue
        d=feats[feature]; d['length_mm']+=e; d['moves']+=1
        for i in range(3):
            d['min_xyz'][i]=min(d['min_xyz'][i],current[i],previous[i]);d['max_xyz'][i]=max(d['max_xyz'][i],current[i],previous[i])
        bins[feature][str(round(math.floor((layer_z+1e-6)/10)*10))]+=e
        layers_mode.add(('relative' if relative_e else 'absolute'))
    grams_per_mm=math.pi*(diameter/2)**2*density/1000
    for feat,d in feats.items():
        d['grams']=d['length_mm']*grams_per_mm
        d['z_bin_grams']={k:v*grams_per_mm for k,v in bins[feat].items()}
    support=sum(d['grams'] for k,d in feats.items() if k.startswith('Support'))
    total=sum(d['grams'] for d in feats.values())
    return {'file':str(path),'density_g_cm3':density,'filament_diameter_mm':diameter,'header_grams':total_header,'parsed_feature_grams':total,'support_grams':support,'support_pct':support/total*100,'non_support_grams':total-support,'relative_modes':sorted(layers_mode),'features':dict(feats),'layer_count':layers}

for name in sys.argv[1:]:
    label=Path(name).parent.name
    result=parse(name)
    (Path('/tmp/bench-support-review')/(label+'.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='features'},indent=2),flush=True)
