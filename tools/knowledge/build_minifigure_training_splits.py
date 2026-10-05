#!/usr/bin/env python3
"""Create deterministic splits after joining identity and duplicate groups.

Missing group IDs fail unless --allow-fallback is explicitly requested. Byte
hashes, shared source/derived IDs and reviewed duplicate clusters join groups
transitively. Perceptual hashes alone do not confirm duplicate identity.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

VERSION = 'minifigure-grouped-split/v2'
DUPLICATE_FIELDS = ('sha256', 'source_reference_asset_id', 'derived_asset_id', 'duplicate_cluster_id')


def bucket(group, train, validation):
    value = int(hashlib.sha256(group.encode()).hexdigest()[:16], 16) / (16 ** 16)
    return 'train' if value < train else 'validation' if value < train + validation else 'test'


def build_splits(records, group_field='outfit_design_id', train=0.8, validation=0.1, allow_fallback=False):
    if not (0 < train < 1 and 0 <= validation < 1 and train + validation < 1):
        raise ValueError('Invalid split fractions')
    if not isinstance(group_field, str) or not group_field.strip():
        raise ValueError('Group field must be a nonempty string')
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            node, parent[node] = parent[node], root
        return root

    def union(left, right):
        a, b = find(left), find(right)
        parent[max(a, b)] = min(a, b)

    def identifier(value, field):
        if value is None or value == '':
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field} must be a nonempty string')
        return value

    prepared = []
    for record in records:
        record_id = identifier(record.get('derived_asset_id') or record.get('sample_id'), 'record ID')
        if record_id is None:
            raise ValueError('Missing record ID')
        group = identifier(record.get(group_field), group_field)
        fallback = group is None
        if fallback and not allow_fallback:
            raise ValueError(f'Missing {group_field} for {record_id}; resolve identity before splitting')
        group = group or identifier(record.get('sample_id'), 'sample_id') or record_id
        group_node = ('fallback' if fallback else 'group', group)
        find(group_node)
        for field in DUPLICATE_FIELDS:
            value = identifier(record.get(field), field)
            if value is not None:
                union(group_node, (field, value))
        prepared.append((record_id, group, fallback, group_node))
    members = {}
    for node in parent:
        if node[0] in {'group', 'fallback'}:
            members.setdefault(find(node), []).append(node)
    component_ids = {root: hashlib.sha256(json.dumps(sorted(nodes), separators=(',', ':')).encode()).hexdigest()
                     for root, nodes in members.items()}
    output = []
    for record_id, group, fallback, node in prepared:
        component = component_ids[find(node)]
        output.append({'record_id': record_id, 'group_field': group_field, 'group_id': group,
                       'used_fallback': fallback, 'component_id': component,
                       'split': bucket(component, train, validation), 'split_version': VERSION})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--group-field', default='outfit_design_id')
    parser.add_argument('--train', type=float, default=0.8)
    parser.add_argument('--validation', type=float, default=0.1)
    parser.add_argument('--allow-fallback', action='store_true')
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('Input and output must differ')
    try:
        with args.input.open(encoding='utf-8-sig') as handle:
            records = [json.loads(line) for line in handle if line.strip()]
        output = build_splits(records, args.group_field, args.train, args.validation, args.allow_fallback)
    except (ValueError, TypeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in output), encoding='utf-8')
    print(json.dumps({'counts': dict(Counter(r['split'] for r in output)),
                      'fallback_records': sum(r['used_fallback'] for r in output),
                      'components': len({r['component_id'] for r in output}),
                      'version': VERSION, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
