#!/usr/bin/env python3
"""json_diff - Deep diff two JSON files."""
import sys,json
def deep_diff(a,b,path=""):
    diffs=[]
    if type(a)!=type(b):diffs.append({"path":path or"/","type":"type_change","from":type(a).__name__,"to":type(b).__name__,"old":a,"new":b});return diffs
    if isinstance(a,dict):
        for k in set(list(a.keys())+list(b.keys())):
            p=f"{path}/{k}"
            if k not in b:diffs.append({"path":p,"type":"removed","value":a[k]})
            elif k not in a:diffs.append({"path":p,"type":"added","value":b[k]})
            else:diffs.extend(deep_diff(a[k],b[k],p))
    elif isinstance(a,list):
        for i in range(max(len(a),len(b))):
            p=f"{path}/{i}"
            if i>=len(b):diffs.append({"path":p,"type":"removed","value":a[i]})
            elif i>=len(a):diffs.append({"path":p,"type":"added","value":b[i]})
            else:diffs.extend(deep_diff(a[i],b[i],p))
    elif a!=b:diffs.append({"path":path or"/","type":"changed","old":a,"new":b})
    return diffs
if __name__=="__main__":
    if len(sys.argv)<3:print("Usage: json_diff.py <file1> <file2>");sys.exit(1)
    a=json.load(open(sys.argv[1]));b=json.load(open(sys.argv[2]))
    diffs=deep_diff(a,b)
    if not diffs:print("No differences")
    else:
        for d in diffs:
            if d["type"]=="added":print(f"+ {d['path']}: {json.dumps(d['value'])}")
            elif d["type"]=="removed":print(f"- {d['path']}: {json.dumps(d['value'])}")
            elif d["type"]=="changed":print(f"~ {d['path']}: {json.dumps(d['old'])} → {json.dumps(d['new'])}")
            else:print(f"! {d['path']}: {d['from']} → {d['to']}")
