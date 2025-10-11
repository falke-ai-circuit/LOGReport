import json
from pathlib import Path

f = "d:/_APP/LOGReport/codegraph.json"
lines = [json.loads(l) for l in open(f, 'r', encoding='utf-8')]
entities = [l for l in lines if l['type'] == 'entity']
rels = [l for l in lines if l['type'] == 'relation' and l['relationType'] in ['BELONGS_TO', 'INHERITS']]

# Trim to 18 chars
for e in entities:
    e['observations'] = [obs[:18] if not obs.startswith('upd:') else obs for obs in e['observations']]

with open(f, 'w', encoding='utf-8') as out:
    for i in entities + rels:
        out.write(json.dumps(i, separators=(',', ':')) + '\n')

size = Path(f).stat().st_size / 1024
print(f"{len(entities)} entities, {len(rels)} relations, {size:.2f} KB")
print("✅ SUCCESS!" if size <= 100 else f"⚠️ Over by {size-100:.2f} KB")
