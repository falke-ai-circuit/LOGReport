"""EXTREME compression - get under 100KB"""
import json
from pathlib import Path

input_file = "d:/_APP/LOGReport/codegraph.json"
output_file = input_file

# Load
with open(input_file, 'r', encoding='utf-8') as f:
    lines = [json.loads(l.strip()) for l in f]

entities = [l for l in lines if l['type'] == 'entity']
relations = [l for l in lines if l['type'] == 'relation']

print(f"Before: {len(entities)} entities, {len(relations)} relations")

# Keep only most critical entities
kept_entities = []
removed_names = set()

for e in entities:
    etype = e['entityType']
    name = e['name']
    
    # Always keep hierarchy
    if etype in ['Type', 'Domain', 'Cluster', 'Module']:
        # Ultra-short observations
        e['observations'] = [e['observations'][0][:25], e['observations'][-1]]
        kept_entities.append(e)
        continue
    
    # Keep only specific key classes
    if etype == 'Class':
        class_name = name.split('.')[-1]
        if class_name in [
            'LogReportGUI', 'CommanderWindow', 'CommanderPresenter', 'NodeTreePresenter',
            'ContextMenuService', 'TelnetService', 'LogProcessor', 'NodeManager'
        ]:
            e['observations'] = [class_name, e['observations'][-1]]
            kept_entities.append(e)
        else:
            removed_names.add(name)
        continue
    
    # Skip ALL methods (too verbose - rely on class names for navigation)
    if etype in ['Method', 'Function']:
        removed_names.add(name)
        continue
    
    kept_entities.append(e)

# Update relations
kept_relations = [r for r in relations if r['from'] not in removed_names and r['to'] not in removed_names]

print(f"After: {len(kept_entities)} entities (-{len(entities)-len(kept_entities)}), {len(kept_relations)} relations (-{len(relations)-len(kept_relations)})")

# Write ultra-compact
with open(output_file, 'w', encoding='utf-8') as f:
    for item in kept_entities + kept_relations:
        f.write(json.dumps(item, separators=(',', ':')) + '\n')

size_kb = Path(output_file).stat().st_size / 1024
print(f"Final size: {size_kb:.2f} KB")
if size_kb <= 100:
    print(f"✅ SUCCESS - Within target by {100-size_kb:.2f} KB!")
else:
    print(f"⚠️  Still over by {size_kb-100:.2f} KB")
