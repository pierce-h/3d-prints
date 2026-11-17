"""Make the material-only clear PETG/right-nozzle variant from the preserved v02.

Uses the installed Bambu preset inheritance and includes. Does not launch Bambu,
slice, select an AMS spool, or send a print. The AMS A3 mapping is a send-time
choice; this project assigns its single filament to physical nozzle 2 (right).
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / 'Revisions/v02-claybourne-rail-aligned/Cabinet_Knob_Jig_v02_Claybourne_Pair_3-16in_PLA_Left_TEST_FIT.3mf'
OUT = PROJECT / 'Revisions/v03-clear-petg-right'
STEM = 'Cabinet_Knob_Jig_v03_Claybourne_Pair_Clear_PETG_Right_TEST_FIT'
PRESET = 'Bambu PETG Translucent @BBL H2D 0.4 nozzle'
META = {'type', 'name', 'inherits', 'from', 'setting_id', 'instantiation',
        'include', 'filament_id', 'description', 'compatible_printers'}


def build(preset_dir):
    inputs = {}

    def resolve(name):
        path = preset_dir / (name + '.json')
        raw = path.read_bytes()
        inputs[path.name] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        result = resolve(data['inherits']) if data.get('inherits') else {}
        for include in data.get('include', []):
            result.update(resolve(include))
        result.update({k: v for k, v in data.items() if k not in META})
        return result

    material = resolve(PRESET)
    with ZipFile(SOURCE) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    original = json.loads(entries['Metadata/project_settings.config'])
    settings = original.copy()
    # Retain only keys supported by this saved project/schema. Five deprecated
    # safety/retraction fields in the system templates are absent from v02.
    applied = {k: v for k, v in material.items() if k in original}
    settings.update(applied)
    settings.update({
        'filament_settings_id': [PRESET],
        'default_filament_profile': [PRESET],
        'filament_ids': ['GFG01'],
        'filament_colour': ['#FFFFFF00'],
        'filament_multi_colour': ['#FFFFFF00'],
        'filament_colour_type': ['0'],
        'filament_map': ['2'],
        'filament_map_mode': 'Manual',
        'master_extruder_id': '2',
        'enable_prime_tower': '0',
    })
    changed_process = set(settings['different_settings_to_system'][0].split(';'))
    changed_process.add('enable_prime_tower')
    settings['different_settings_to_system'][0] = ';'.join(sorted(changed_process))
    model_settings = ET.fromstring(entries['Metadata/model_settings.config'])
    for node in model_settings.findall('plate/metadata'):
        if node.get('key') == 'filament_maps':
            node.set('value', '2')
        elif node.get('key') == 'plater_name':
            node.set('value', STEM)
    # Object extruder=1 is the project filament index, not the physical nozzle.
    assert [n.get('value') for n in model_settings.findall("object/metadata[@key='extruder']")] == ['1', '1']
    entries['Metadata/model_settings.config'] = ET.tostring(model_settings, encoding='utf-8', xml_declaration=True)
    entries['Metadata/project_settings.config'] = (json.dumps(settings, indent=2) + '\n').encode()
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (STEM + '.3mf')
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    with ZipFile(SOURCE) as source, ZipFile(target) as result:
        assert source.read('3D/3dmodel.model') == result.read('3D/3dmodel.model')
        unchanged = [name for name in source.namelist() if source.read(name) == result.read(name)]
    assert settings['filament_type'] == ['PETG']
    assert settings['filament_map'] == ['2']
    assert settings['master_extruder_id'] == '2'
    assert settings['enable_prime_tower'] == '0'
    assert len(settings['filament_settings_id']) == 1
    mismatches = [k for k, v in applied.items() if k != 'filament_settings_id' and settings[k] != v]
    assert not mismatches, mismatches
    report = {
        'project': target.name,
        'source_project': str(SOURCE.relative_to(PROJECT)),
        'geometry_and_build_xml_byte_identical': True,
        'geometry_sha256': hashlib.sha256(entries['3D/3dmodel.model']).hexdigest(),
        'unchanged_archive_entries': unchanged,
        'filament_preset': PRESET,
        'installed_preset_directory': str(preset_dir),
        'preset_input_sha256': inputs,
        'preset_supported_keys_applied': len(applied),
        'preset_value_mismatches': mismatches,
        'filament_count': 1,
        'material': 'PETG',
        'color_rgba': '#FFFFFF00',
        'physical_nozzle': 'right / 2',
        'project_filament_index': 1,
        'ams_slot': 'A3 confirmed in device UI; select/verify at send time',
        'prime_tower_enabled': False,
        'nozzle_temperature': settings['nozzle_temperature'],
        'nozzle_temperature_initial_layer': settings['nozzle_temperature_initial_layer'],
        'textured_plate_temp': settings['textured_plate_temp'],
        'filament_max_volumetric_speed': settings['filament_max_volumetric_speed'],
        'process_geometry_settings': {k: settings[k] for k in [
            'layer_height', 'wall_loops', 'sparse_infill_density',
            'sparse_infill_pattern', 'top_shell_layers', 'bottom_shell_layers',
            'brim_width', 'enable_support']},
        'slice_status': 'Not checked by this material-conversion script.',
        'print_status': 'Not sent by this material-conversion script.',
    }
    (OUT / 'Validation').mkdir(exist_ok=True)
    (OUT / 'Validation/profile_geometry.json').write_text(json.dumps(report, indent=2) + '\n')
    print(target)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset-dir', type=Path, default=Path.home() / 'Library/Application Support/BambuStudio/system/BBL/filament')
    build(parser.parse_args().preset_dir)
