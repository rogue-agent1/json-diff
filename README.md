# json_diff

Deep diff two JSON files with path-aware output. Merge and patch support.

## Usage

```bash
# Diff two files
python3 json_diff.py diff a.json b.json

# Ignore array order
python3 json_diff.py diff a.json b.json --ignore-order

# Deep merge (b overrides a)
python3 json_diff.py merge base.json override.json

# Apply changes
python3 json_diff.py patch original.json changes.json

# Pipe from stdin
echo '{"a":1}' | python3 json_diff.py diff - b.json
```

## Zero dependencies. Single file. Python 3.8+.
