#!/usr/bin/env python3
"""JSON structural diff."""

def diff(a, b, path=""):
    diffs = []
    if type(a) != type(b):
        diffs.append({"path": path, "op": "type_change", "old": repr(a), "new": repr(b)})
        return diffs
    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in sorted(all_keys):
            p = f"{path}.{k}" if path else k
            if k not in a:
                diffs.append({"path": p, "op": "add", "value": b[k]})
            elif k not in b:
                diffs.append({"path": p, "op": "remove", "value": a[k]})
            else:
                diffs.extend(diff(a[k], b[k], p))
    elif isinstance(a, list):
        for i in range(max(len(a), len(b))):
            p = f"{path}[{i}]"
            if i >= len(a):
                diffs.append({"path": p, "op": "add", "value": b[i]})
            elif i >= len(b):
                diffs.append({"path": p, "op": "remove", "value": a[i]})
            else:
                diffs.extend(diff(a[i], b[i], p))
    else:
        if a != b:
            diffs.append({"path": path, "op": "change", "old": a, "new": b})
    return diffs

def format_diff(diffs):
    lines = []
    for d in diffs:
        if d["op"] == "add":
            lines.append(f"+ {d['path']}: {d['value']}")
        elif d["op"] == "remove":
            lines.append(f"- {d['path']}: {d['value']}")
        elif d["op"] == "change":
            lines.append(f"~ {d['path']}: {d['old']} -> {d['new']}")
        elif d["op"] == "type_change":
            lines.append(f"! {d['path']}: {d['old']} -> {d['new']}")
    return "\n".join(lines)

def are_equal(a, b):
    return len(diff(a, b)) == 0

if __name__ == "__main__":
    import json
    a = {"name": "old", "items": [1, 2]}
    b = {"name": "new", "items": [1, 3], "extra": True}
    print(format_diff(diff(a, b)))

def test():
    # Equal
    assert diff({"a": 1}, {"a": 1}) == []
    assert are_equal([1, 2], [1, 2])
    # Changes
    d = diff({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4})
    assert len(d) == 2
    ops = {x["op"] for x in d}
    assert "change" in ops and "add" in ops
    # Removal
    d2 = diff({"a": 1, "b": 2}, {"a": 1})
    assert d2[0]["op"] == "remove"
    # Array
    d3 = diff([1, 2, 3], [1, 4, 3, 5])
    assert len(d3) == 2  # change at [1], add at [3]
    # Type change
    d4 = diff({"x": 1}, {"x": "one"})
    assert d4[0]["op"] == "type_change"
    # Format
    f = format_diff(d)
    assert "~" in f or "+" in f
    print("  json_diff: ALL TESTS PASSED")
