"""Check entity counts across backup files"""
import json

def count_entities(filepath):
    entities = 0
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            if 'observations' in item:
                entities += 1
    return entities

print("PROJECT MEMORY:")
print(f"  BEFORE Phase1: {count_entities('backups/project_memory_before_phase1.json')}")
print(f"  AFTER Phase1:  {count_entities('backups/project_memory_after_phase1.json')}")  
print(f"  AFTER Phase2:  {count_entities('backups/project_memory_after_phase2.json')}")
print(f"  CURRENT:       {count_entities('project_memory.json')}")
print()

print("GLOBAL MEMORY:")
print(f"  BEFORE Phase1: {count_entities('backups/global_memory_before_phase1.json')}")
print(f"  AFTER Phase1:  {count_entities('backups/global_memory_after_phase1.json')}")
print(f"  AFTER Phase2:  {count_entities('backups/global_memory_after_phase2.json')}")
print(f"  CURRENT:       {count_entities('global_memory.json')}")
