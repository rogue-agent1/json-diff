#!/usr/bin/env python3
"""JSON Diff - Deep structural comparison of JSON documents."""
import sys, json

class Diff:
    def __init__(self, kind, path, old=None, new=None):
        self.kind = kind; self.path = path; self.old = old; self.new = new
    def __repr__(self):
        if self.kind == "added": return f"+ {self.path}: {json.dumps(self.new)}"
        if self.kind == "removed": return f"- {self.path}: {json.dumps(self.old)}"
        if self.kind == "changed": return f"~ {self.path}: {json.dumps(self.old)} -> {json.dumps(self.new)}"
        if self.kind == "type_changed": return f"! {self.path}: type {type(self.old).__name__} -> {type(self.new).__name__}"
        return f"? {self.path}"

def json_diff(a, b, path=""):
    diffs = []
    if type(a) != type(b):
        diffs.append(Diff("type_changed", path or "/", a, b)); return diffs
    if isinstance(a, dict):
        for key in set(list(a.keys()) + list(b.keys())):
            p = f"{path}/{key}"
            if key not in a: diffs.append(Diff("added", p, new=b[key]))
            elif key not in b: diffs.append(Diff("removed", p, old=a[key]))
            else: diffs.extend(json_diff(a[key], b[key], p))
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}/{i}"
            if i >= len(a): diffs.append(Diff("added", p, new=b[i]))
            elif i >= len(b): diffs.append(Diff("removed", p, old=a[i]))
            else: diffs.extend(json_diff(a[i], b[i], p))
    elif a != b:
        diffs.append(Diff("changed", path or "/", a, b))
    return diffs

def main():
    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f: a = json.load(f)
        with open(sys.argv[2]) as f: b = json.load(f)
    else:
        a = {"name": "App", "version": "1.0", "deps": {"lodash": "4.0", "react": "17"}, "scripts": ["build", "test"]}
        b = {"name": "App", "version": "2.0", "deps": {"lodash": "4.1", "vue": "3"}, "scripts": ["build", "test", "lint"], "type": "module"}
    diffs = json_diff(a, b)
    print(f"=== JSON Diff ({len(diffs)} changes) ===\n")
    for d in diffs: print(f"  {d}")
    added = sum(1 for d in diffs if d.kind == "added")
    removed = sum(1 for d in diffs if d.kind == "removed")
    changed = sum(1 for d in diffs if d.kind in ("changed", "type_changed"))
    print(f"\nSummary: +{added} -{removed} ~{changed}")

if __name__ == "__main__":
    main()
