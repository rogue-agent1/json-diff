#!/usr/bin/env python3
"""JSON structural diff."""
import sys, json

def diff(a, b, path=''):
    diffs = []
    if type(a) != type(b):
        diffs.append(f"  CHANGED {path or '/'}: {type(a).__name__} → {type(b).__name__}")
        return diffs
    if isinstance(a, dict):
        for k in sorted(set(list(a.keys()) + list(b.keys()))):
            p = f"{path}.{k}"
            if k not in a: diffs.append(f"  + ADDED {p}: {json.dumps(b[k])[:80]}")
            elif k not in b: diffs.append(f"  - REMOVED {p}: {json.dumps(a[k])[:80]}")
            else: diffs.extend(diff(a[k], b[k], p))
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}[{i}]"
            if i >= len(a): diffs.append(f"  + ADDED {p}: {json.dumps(b[i])[:80]}")
            elif i >= len(b): diffs.append(f"  - REMOVED {p}: {json.dumps(a[i])[:80]}")
            else: diffs.extend(diff(a[i], b[i], p))
    elif a != b:
        diffs.append(f"  CHANGED {path}: {json.dumps(a)[:40]} → {json.dumps(b)[:40]}")
    return diffs

if __name__ == '__main__':
    if len(sys.argv) < 3: print("Usage: json_diff.py <file1.json> <file2.json>"); sys.exit(1)
    a = json.load(open(sys.argv[1]))
    b = json.load(open(sys.argv[2]))
    d = diff(a, b)
    if d:
        print(f"{len(d)} difference(s):")
        print('\n'.join(d))
    else:
        print("Identical.")
