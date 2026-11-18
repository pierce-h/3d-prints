"""Clear PETG/right-nozzle settings variant of the unchanged one-piece v02.

Receiver/remix CC BY-NC-SA 4.0; see ../Original/Attribution.txt.
Only saved settings and descriptive metadata change. No printer job is sent.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from build_mount_v02 import OUT as PREVIOUS, STEM as PREVIOUS_STEM, ROOT, common

OUT=ROOT/'Revisions/v03-clear-petg-right'
STEM='Shark_Accessory_Mount_v03_One_Piece_Clear_PETG_Right_TEST_FIT'
SOURCE=PREVIOUS/(PREVIOUS_STEM+'.3mf')
PRESET='Bambu PETG Translucent @BBL H2D 0.4 nozzle'
META={'type','name','inherits','from','setting_id','instantiation','include','filament_id','description','compatible_printers'}


def build(preset_dir):
    # Bambu's importer expects the core namespace as the XML default.
    ET.register_namespace('',common.CORE)
    inputs={}
    def resolve(name):
        path=preset_dir/(name+'.json');raw=path.read_bytes()
        inputs[path.name]=hashlib.sha256(raw).hexdigest()
        data=json.loads(raw)
        result=resolve(data['inherits']) if data.get('inherits') else {}
        for include in data.get('include',[]):result.update(resolve(include))
        result.update({k:v for k,v in data.items() if k not in META})
        return result
    material=resolve(PRESET)
    with ZipFile(SOURCE) as z:entries={n:z.read(n) for n in z.namelist()}
    original=json.loads(entries['Metadata/project_settings.config'])
    settings=original.copy()
    applied={k:v for k,v in material.items() if k in original}
    settings.update(applied)
    settings.update(filament_settings_id=[PRESET],default_filament_profile=[PRESET],
        filament_ids=['GFG01'],filament_colour=['#FFFFFF00'],filament_multi_colour=['#FFFFFF00'],
        filament_colour_type=['0'],filament_map=['2'],filament_map_mode='Manual',master_extruder_id='2')
    process_keys=['layer_height','initial_layer_print_height','wall_loops','sparse_infill_density',
        'sparse_infill_pattern','top_shell_layers','bottom_shell_layers','brim_type','brim_width',
        'brim_object_gap','enable_support','enable_prime_tower','outer_wall_speed']
    assert all(settings[k]==original[k] for k in process_keys)
    assert settings['filament_type']==['PETG'] and settings['wall_loops']=='5'
    entries['Metadata/project_settings.config']=(json.dumps(settings,indent=2)+'\n').encode()
    config=ET.fromstring(entries['Metadata/model_settings.config'])
    config.find("plate/metadata[@key='filament_maps']").set('value','2')
    config.find("plate/metadata[@key='plater_name']").set('value',STEM)
    assert [n.get('value') for n in config.findall("object/metadata[@key='extruder']")]==['1']
    entries['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
    model=ET.fromstring(entries['3D/3dmodel.model'])
    geometry_tags=[f'{{{common.CORE}}}resources',f'{{{common.CORE}}}build']
    geometry_before={tag:ET.tostring(model.find(tag)) for tag in geometry_tags}
    for n in model.findall(f'{{{common.CORE}}}metadata'):
        if n.get('name')=='Title':n.text=STEM
        elif n.get('name')=='ProfileTitle':n.text='H2D clear PETG right | 0.20 mm | 5 walls | 25% gyroid | one-piece mount'
        elif n.get('name')=='Description':n.text+=' v03 changes material to clear PETG/right nozzle; v02 geometry and placement retained.'
    entries['3D/3dmodel.model']=ET.tostring(model,encoding='utf-8',xml_declaration=True)
    assert geometry_before=={tag:ET.tostring(model.find(tag)) for tag in geometry_tags}
    val=OUT/'Validation';val.mkdir(parents=True,exist_ok=True)
    target=OUT/(STEM+'.3mf')
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for n,b in entries.items():z.writestr(n,b)
    report=dict(project=target.name,source_project=str(SOURCE.relative_to(ROOT)),
        geometry_and_placement_unchanged=True,
        geometry_section_sha256={tag:hashlib.sha256(raw).hexdigest() for tag,raw in geometry_before.items()},
        filament_preset=PRESET,preset_input_sha256=inputs,supported_material_keys_applied=len(applied),
        material='Bambu PETG Translucent, clear',physical_nozzle='right / 2',project_filament_index=1,
        color_rgba='#FFFFFF00',ams_slot='Clear PETG previously used in A3; verify live slot at send time.',
        nozzle_temperature=settings['nozzle_temperature'],nozzle_temperature_initial_layer=settings['nozzle_temperature_initial_layer'],
        textured_plate_temp=settings['textured_plate_temp'],filament_max_volumetric_speed=settings['filament_max_volumetric_speed'],
        process_settings={k:settings[k] for k in process_keys},
        physical_fit='Socket fit and simultaneous accessory clearance untested.',print_status='Prepared only; no print sent.')
    (val/'profile_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preset-dir',type=Path,default=Path.home()/'Library/Application Support/BambuStudio/system/BBL/filament')
    build(parser.parse_args().preset_dir)
