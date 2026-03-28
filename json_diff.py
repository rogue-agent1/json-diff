#!/usr/bin/env python3
"""json_diff — Deep diff two JSON files/values with path-aware output.

Usage:
    json_diff.py diff a.json b.json
    json_diff.py diff a.json b.json --ignore-order
    echo '{"a":1}' | json_diff.py diff - b.json
    json_diff.py patch a.json changes.json
    json_diff.py merge a.json b.json
"""

import sys
import json
import argparse
from typing import Any


def deep_diff(a: Any, b: Any, path: str = '$', ignore_order: bool = False) -> list:
    """Compute deep diff between two values. Returns list of changes."""
    changes = []
    
    if type(a) != type(b):
        changes.append({'op': 'replace', 'path': path, 'old': a, 'new': b})
        return changes
    
    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for key in sorted(all_keys):
            child_path = f'{path}.{key}'
            if key not in a:
                changes.append({'op': 'add', 'path': child_path, 'value': b[key]})
            elif key not in b:
                changes.append({'op': 'remove', 'path': child_path, 'value': a[key]})
            else:
                changes.extend(deep_diff(a[key], b[key], child_path, ignore_order))
    
    elif isinstance(a, list):
        if ignore_order and all(not isinstance(x, (dict, list)) for x in a + b):
            sa, sb = sorted(str(x) for x in a), sorted(str(x) for x in b)
            if sa != sb:
                added = [x for x in b if x not in a]
                removed = [x for x in a if x not in b]
                if added:
                    changes.append({'op': 'add_items', 'path': path, 'values': added})
                if removed:
                    changes.append({'op': 'remove_items', 'path': path, 'values': removed})
        else:
            max_len = max(len(a), len(b))
            for i in range(max_len):
                child_path = f'{path}[{i}]'
                if i >= len(a):
                    changes.append({'op': 'add', 'path': child_path, 'value': b[i]})
                elif i >= len(b):
                    changes.append({'op': 'remove', 'path': child_path, 'value': a[i]})
                else:
                    changes.extend(deep_diff(a[i], b[i], child_path, ignore_order))
    
    elif a != b:
        changes.append({'op': 'replace', 'path': path, 'old': a, 'new': b})
    
    return changes


def load_json(path: str) -> Any:
    if path == '-':
        return json.load(sys.stdin)
    with open(path) as f:
        return json.load(f)


def format_value(v: Any, max_len: int = 60) -> str:
    s = json.dumps(v)
    return s if len(s) <= max_len else s[:max_len-3] + '...'


def cmd_diff(args):
    a = load_json(args.file_a)
    b = load_json(args.file_b)
    
    changes = deep_diff(a, b, ignore_order=args.ignore_order)
    
    if args.json:
        print(json.dumps(changes, indent=2))
        return
    
    if not changes:
        print('✅ No differences')
        return
    
    stats = {'add': 0, 'remove': 0, 'replace': 0, 'add_items': 0, 'remove_items': 0}
    
    for c in changes:
        op = c['op']
        stats[op] = stats.get(op, 0) + 1
        
        if op == 'add':
            print(f'  \033[32m+ {c["path"]}: {format_value(c["value"])}\033[0m')
        elif op == 'remove':
            print(f'  \033[31m- {c["path"]}: {format_value(c["value"])}\033[0m')
        elif op == 'replace':
            print(f'  \033[33m~ {c["path"]}: {format_value(c["old"])} → {format_value(c["new"])}\033[0m')
        elif op == 'add_items':
            print(f'  \033[32m+ {c["path"]}: added {format_value(c["values"])}\033[0m')
        elif op == 'remove_items':
            print(f'  \033[31m- {c["path"]}: removed {format_value(c["values"])}\033[0m')
    
    total = sum(stats.values())
    parts = []
    if stats['add']: parts.append(f'+{stats["add"]}')
    if stats['remove']: parts.append(f'-{stats["remove"]}')
    if stats['replace']: parts.append(f'~{stats["replace"]}')
    print(f'\n{total} changes ({", ".join(parts)})')


def apply_patch(obj: Any, changes: list) -> Any:
    """Apply a list of changes to an object (simple implementation)."""
    import copy
    result = copy.deepcopy(obj)
    
    for change in changes:
        path_parts = []
        path = change['path']
        # Parse path like $.foo.bar[0].baz
        for part in path.replace('[', '.[').split('.'):
            if not part or part == '$':
                continue
            if part.startswith('[') and part.endswith(']'):
                path_parts.append(int(part[1:-1]))
            else:
                path_parts.append(part)
        
        # Navigate to parent
        current = result
        for p in path_parts[:-1]:
            current = current[p]
        
        key = path_parts[-1] if path_parts else None
        op = change['op']
        
        if key is None:
            if op == 'replace':
                result = change['new']
        elif op == 'add' or op == 'replace':
            val = change.get('value', change.get('new'))
            if isinstance(current, list) and isinstance(key, int):
                if key >= len(current):
                    current.append(val)
                else:
                    current[key] = val
            else:
                current[key] = val
        elif op == 'remove':
            if isinstance(current, list) and isinstance(key, int):
                if key < len(current):
                    current.pop(key)
            elif isinstance(current, dict):
                current.pop(key, None)
    
    return result


def cmd_patch(args):
    obj = load_json(args.file)
    changes = load_json(args.changes)
    result = apply_patch(obj, changes)
    print(json.dumps(result, indent=2))


def cmd_merge(args):
    """Deep merge two JSON objects (b overrides a)."""
    a = load_json(args.file_a)
    b = load_json(args.file_b)
    
    def merge(x, y):
        if isinstance(x, dict) and isinstance(y, dict):
            result = dict(x)
            for k, v in y.items():
                if k in result:
                    result[k] = merge(result[k], v)
                else:
                    result[k] = v
            return result
        return y
    
    print(json.dumps(merge(a, b), indent=2))


def main():
    p = argparse.ArgumentParser(description='Deep JSON diff tool')
    p.add_argument('--json', action='store_true')
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('diff', help='Diff two JSON files')
    s.add_argument('file_a')
    s.add_argument('file_b')
    s.add_argument('--ignore-order', action='store_true', help='Ignore array order')
    s.set_defaults(func=cmd_diff)

    s = sub.add_parser('patch', help='Apply diff changes to JSON')
    s.add_argument('file')
    s.add_argument('changes', help='JSON file with changes array')
    s.set_defaults(func=cmd_patch)

    s = sub.add_parser('merge', help='Deep merge two JSON objects')
    s.add_argument('file_a')
    s.add_argument('file_b')
    s.set_defaults(func=cmd_merge)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
