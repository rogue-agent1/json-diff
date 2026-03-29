#!/usr/bin/env python3
"""json_diff - Compare JSON structures."""
import sys, argparse, json

def diff(a, b, path=""):
    diffs = []
    if type(a) != type(b):
        diffs.append({"path": path or "$", "type": "type_change", "old": type(a).__name__, "new": type(b).__name__})
        return diffs
    if isinstance(a, dict):
        for k in set(list(a.keys()) + list(b.keys())):
            p = f"{path}.{k}" if path else k
            if k not in a: diffs.append({"path": p, "type": "added", "value": b[k]})
            elif k not in b: diffs.append({"path": p, "type": "removed", "value": a[k]})
            else: diffs.extend(diff(a[k], b[k], p))
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}[{i}]"
            if i >= len(a): diffs.append({"path": p, "type": "added", "value": b[i]})
            elif i >= len(b): diffs.append({"path": p, "type": "removed", "value": a[i]})
            else: diffs.extend(diff(a[i], b[i], p))
    elif a != b:
        diffs.append({"path": path or "$", "type": "changed", "old": a, "new": b})
    return diffs

def main():
    p = argparse.ArgumentParser(description="JSON diff")
    p.add_argument("file1"); p.add_argument("file2")
    p.add_argument("--stats", action="store_true")
    args = p.parse_args()
    with open(args.file1) as f: a = json.load(f)
    with open(args.file2) as f: b = json.load(f)
    diffs = diff(a, b)
    if args.stats:
        from collections import Counter
        types = Counter(d["type"] for d in diffs)
        print(json.dumps({"total_changes": len(diffs), "by_type": dict(types)}, indent=2))
    else:
        print(json.dumps({"changes": len(diffs), "diffs": diffs}, indent=2))

if __name__ == "__main__": main()
