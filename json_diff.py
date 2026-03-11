#!/usr/bin/env python3
"""JSON structural diff — compare two JSON values and produce a patch.

Outputs human-readable diff and RFC 6902 JSON Patch format.

Usage:
    python json_diff.py a.json b.json
    python json_diff.py --test
"""
import json, sys

class Diff:
    def __init__(self, op, path, old=None, new=None):
        self.op=op; self.path=path; self.old=old; self.new=new
    def __repr__(self): return f"{self.op} {self.path}: {self.old} → {self.new}" if self.op=='replace' else f"{self.op} {self.path}: {self.new or self.old}"
    def to_patch(self):
        if self.op == 'add': return {"op":"add","path":self.path,"value":self.new}
        if self.op == 'remove': return {"op":"remove","path":self.path}
        if self.op == 'replace': return {"op":"replace","path":self.path,"value":self.new}

def diff(a, b, path="") -> list:
    """Compute structural diff between two JSON values."""
    diffs = []
    if type(a) != type(b):
        diffs.append(Diff('replace', path or '/', a, b))
    elif isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for key in sorted(all_keys):
            p = f"{path}/{key}"
            if key not in a:
                diffs.append(Diff('add', p, new=b[key]))
            elif key not in b:
                diffs.append(Diff('remove', p, old=a[key]))
            else:
                diffs.extend(diff(a[key], b[key], p))
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}/{i}"
            if i >= len(a):
                diffs.append(Diff('add', p, new=b[i]))
            elif i >= len(b):
                diffs.append(Diff('remove', p, old=a[i]))
            else:
                diffs.extend(diff(a[i], b[i], p))
    elif a != b:
        diffs.append(Diff('replace', path or '/', a, b))
    return diffs

def apply_patch(doc, patch):
    """Apply JSON Patch (RFC 6902) to document."""
    doc = json.loads(json.dumps(doc))  # deep copy
    for op in patch:
        parts = op['path'].strip('/').split('/') if op['path'] != '/' else []
        if op['op'] == 'add':
            _set_path(doc, parts, op['value'])
        elif op['op'] == 'remove':
            _del_path(doc, parts)
        elif op['op'] == 'replace':
            _set_path(doc, parts, op['value'])
    return doc

def _set_path(doc, parts, value):
    if not parts:
        return value  # Can't replace root in-place
    obj = doc
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    key = parts[-1]
    if isinstance(obj, list):
        idx = int(key)
        if idx >= len(obj): obj.append(value)
        else: obj[idx] = value
    else:
        obj[key] = value
    return doc

def _del_path(doc, parts):
    obj = doc
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    key = parts[-1]
    if isinstance(obj, list): obj.pop(int(key))
    else: del obj[key]

def format_diff(diffs, color=False) -> str:
    lines = []
    for d in diffs:
        if d.op == 'add':
            lines.append(f"+ {d.path}: {json.dumps(d.new)}")
        elif d.op == 'remove':
            lines.append(f"- {d.path}: {json.dumps(d.old)}")
        elif d.op == 'replace':
            lines.append(f"~ {d.path}: {json.dumps(d.old)} → {json.dumps(d.new)}")
    return '\n'.join(lines)

def to_json_patch(diffs) -> list:
    return [d.to_patch() for d in diffs]

def test():
    print("=== JSON Diff Tests ===\n")

    a = {"name": "Alice", "age": 30, "tags": ["admin", "user"]}
    b = {"name": "Alice", "age": 31, "tags": ["admin", "editor"], "email": "a@b.com"}

    diffs = diff(a, b)
    print(format_diff(diffs))
    assert any(d.op == 'replace' and 'age' in d.path for d in diffs)
    assert any(d.op == 'add' and 'email' in d.path for d in diffs)
    assert any(d.op == 'replace' and 'tags/1' in d.path for d in diffs)
    print(f"\n✓ {len(diffs)} differences found")

    # JSON Patch
    patch = to_json_patch(diffs)
    assert all('op' in p and 'path' in p for p in patch)
    print(f"✓ JSON Patch: {len(patch)} operations")

    # No diff
    assert diff({"x": 1}, {"x": 1}) == []
    print("✓ Identical objects: no diff")

    # Type change
    d = diff({"x": 1}, {"x": "one"})
    assert len(d) == 1 and d[0].op == 'replace'
    print("✓ Type change detected")

    # Nested
    d2 = diff({"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 2}}})
    assert d2[0].path == "/a/b/c"
    print(f"✓ Nested diff: {d2[0].path}")

    # Array length change
    d3 = diff([1,2,3], [1,2,3,4])
    assert any(dd.op == 'add' for dd in d3)
    print("✓ Array growth")

    d4 = diff([1,2,3], [1,2])
    assert any(dd.op == 'remove' for dd in d4)
    print("✓ Array shrink")

    # Apply patch roundtrip
    patch_ops = to_json_patch(diff(a, b))
    result = apply_patch(a, patch_ops)
    assert result['age'] == 31
    assert result['email'] == 'a@b.com'
    assert result['tags'][1] == 'editor'
    print("✓ Apply patch roundtrip")

    print("\nAll tests passed! ✓")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--test": test()
    elif len(args) == 2:
        with open(args[0]) as f: a = json.load(f)
        with open(args[1]) as f: b = json.load(f)
        print(format_diff(diff(a, b)))
