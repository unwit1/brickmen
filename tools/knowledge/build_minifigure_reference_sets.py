#!/usr/bin/env python3
"""Rank provenance-backed evidence without treating unknown views as front views.

Supports complete minifigures and standalone parts. Missing identifiers are
errors. Conflicted evidence is retained for review but cannot win a slot.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

VERSION = 'minifigure-reference-set/v2'
AUTHORITY = {
    'lego_primary': 100, 'rights_holder_primary': 95, 'developer_primary': 95,
    'official_film_local_copy': 90, 'licensed_game_primary': 90,
    'structured_catalog': 80, 'structured_catalog_secondary': 72,
    'official_ecosystem_reference': 70, 'community_structured': 62,
    'secondary_structured_vector': 62, 'secondary_research': 45, 'secondary_discovery': 25,
}
VIEW_ALIASES = {'back': 'rear', 'front_right_3q': 'front_3q_right',
                'front_left_3q': 'front_3q_left', 'rear_right_3q': 'rear_3q_right',
                'rear_left_3q': 'rear_3q_left'}


def numeric(record, name, default=0, maximum=None):
    quality = record.get('quality') or {}
    value = record.get(name)
    if value is None:
        value = quality.get(name)
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError(f'{name} must be numeric')
    value = float(value)
    if not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f'Invalid {name}: {value}')
    return value


def score(record):
    width, height = numeric(record, 'width'), numeric(record, 'height')
    resolution = min(15, math.sqrt(width) * math.sqrt(height) / 100) if width and height else 0
    return (AUTHORITY.get(record.get('authority'), 0)
            + 20 * numeric(record, 'identity_confidence', maximum=1)
            + 10 * numeric(record, 'view_confidence', maximum=1)
            + 8 * numeric(record, 'segmentation_confidence', maximum=1) + resolution
            - 10 * numeric(record, 'blur_score', maximum=1)
            - 15 * numeric(record, 'occlusion_score', maximum=1))


def role(record, target_kind='minifigure'):
    component = str(record.get('component_type') or '').lower()
    raw_view = str(record.get('view') or 'unknown').lower()
    view = VIEW_ALIASES.get(raw_view, raw_view)
    medium = str(record.get('medium') or '').lower()
    for match, slot in [('game_texture', 'game_texture'), ('game_model', 'game_model_render'),
                        ('film', 'film_expression_states'), ('pattern', 'structured_component_pattern'),
                        ('geometry', 'structured_geometry')]:
        if match in medium:
            return slot
    if target_kind == 'part':
        return 'part_' + view
    if component in {'head', 'face', 'torso', 'hips', 'leg', 'legs', 'hips_legs'}:
        prefix = 'head' if component in {'head', 'face'} else 'torso' if component == 'torso' else 'hips_legs'
        return prefix + '_' + ('reverse' if prefix == 'head' and view == 'rear' else view)
    if component in {'arm_left', 'left_arm'}:
        return 'arm_left'
    if component in {'arm_right', 'right_arm'}:
        return 'arm_right'
    if component in {'helmet', 'mask', 'headgear', 'helmet_or_mask'}:
        return 'mask_or_headgear_' + ('side' if view in {'left', 'right'} else view)
    if component.startswith('accessory'):
        return 'accessory_primary'
    if view in {'front_3q_left', 'front_3q_right'}:
        return 'full_front_3q'
    return 'full_' + view if view in {'front', 'rear', 'left', 'right'} else 'other'


def build_reference_sets(records, target_kind='minifigure', alternates=5):
    if target_kind not in {'minifigure', 'part'} or alternates < 0:
        raise ValueError('Invalid target kind or alternate count')
    by_sample, seen = defaultdict(list), {}
    for record in records:
        for key in ('sample_id', 'derived_asset_id', 'source_reference_asset_id'):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError(f'Missing {key}')
        asset = record['derived_asset_id']
        if asset in seen:
            if record != seen[asset]:
                raise ValueError(f'Conflicting duplicate derived_asset_id: {asset}')
            continue
        seen[asset] = record
        score(record)
        by_sample[record['sample_id']].append(record)
    output = []
    for sample_id, sample in sorted(by_sample.items()):
        slots, conflicts = defaultdict(list), []
        for record in sample:
            if record.get('unresolved_conflicts'):
                conflicts.append({'asset_id': record['derived_asset_id'], 'conflicts': record['unresolved_conflicts']})
            else:
                slots[role(record, target_kind)].append(record)
        resolved = {}
        for slot, candidates in sorted(slots.items()):
            candidates.sort(key=lambda r: (-score(r), r['derived_asset_id']))
            unique, hashes = [], set()
            for candidate in candidates:
                key = candidate.get('sha256') or candidate['derived_asset_id']
                if key not in hashes:
                    hashes.add(key)
                    unique.append(candidate)
            resolved[slot] = {
                'preferred_asset_id': unique[0]['derived_asset_id'],
                'source_reference_asset_id': unique[0]['source_reference_asset_id'],
                'preferred_score': round(score(unique[0]), 3),
                'alternate_asset_ids': [r['derived_asset_id'] for r in unique[1:1 + alternates]],
                'occurrence_asset_ids': sorted(r['derived_asset_id'] for r in candidates),
            }
        required = (['part_front', 'part_rear', 'part_left', 'part_right'] if target_kind == 'part'
                    else ['full_front', 'full_rear', 'full_left', 'full_right', 'head_front', 'torso_front', 'hips_legs_front'])
        output.append({
            'reference_set_id': 'refset-' + hashlib.sha256(f'{sample_id}|{target_kind}|{VERSION}'.encode()).hexdigest()[:24],
            'sample_id': sample_id, 'target_kind': target_kind, 'slots': resolved,
            'completeness': {slot: slot in resolved for slot in required},
            'missing_roles': [slot for slot in required if slot not in resolved],
            'unresolved_conflicts': conflicts, 'asset_count': len(sample), 'version': VERSION,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-kind', choices=['minifigure', 'part'], default='minifigure')
    parser.add_argument('--alternates', type=int, default=5)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('Input and output must differ')
    try:
        with args.input.open(encoding='utf-8-sig') as handle:
            records = [json.loads(line) for line in handle if line.strip()]
        output = build_reference_sets(records, args.target_kind, args.alternates)
    except (ValueError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in output), encoding='utf-8')
    print(json.dumps({'reference_sets': len(output), 'version': VERSION, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
