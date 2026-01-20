"""Final ultra-compression for codegraph"""
import json
from pathlib import Path

input_file = "d:/_APP/LOGReport/codegraph.json"
output_file = input_file

# Load
with open(input_file, 'r', encoding='utf-8') as f:
    lines = [json.loads(l.strip()) for l in f]

entities = [l for l in lines if l['type'] == 'entity']
relations = [l for l in lines if l['type'] == 'relation']

# Ultra-compress observations to 35 chars
for e in entities:
    e['observations'] = [
        obs[:35] if not obs.startswith('upd:') else obs 
        for obs in e['observations']
    ]

# Write with compact JSON (no spaces)
with open(output_file, 'w', encoding='utf-8') as f:
    for item in entities + relations:
        f.write(json.dumps(item, separators=(',', ':')) + '\n')

# Report
size_kb = Path(output_file).stat().st_size / 1024
print(f"Final size: {size_kb:.2f} KB")
if size_kb <= 100:
    print(f"✅ SUCCESS - Within target by {100-size_kb:.2f} KB!")
else:
    print(f"⚠️  Over by {size_kb-100:.2f} KB")
