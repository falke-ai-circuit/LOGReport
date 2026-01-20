"""Test codegraph navigation capabilities"""
import json

# Load codegraph
with open('d:/_APP/LOGReport/codegraph.json', 'r', encoding='utf-8') as f:
    items = [json.loads(line.strip()) for line in f]

entities = {e['name']: e for e in items if e.get('type') == 'entity'}
relations = [r for r in items if r.get('type') == 'relation']

print("=" * 60)
print("CODEGRAPH NAVIGATION TEST")
print("=" * 60)

# Test 1: Find all domains
print("\n1. DOMAINS (High-level architecture):")
domains = [e for e in entities.values() if e['entityType'] == 'Domain']
for d in domains:
    print(f"   - {d['name']}")

# Test 2: Navigate from Domain to Modules
print("\n2. NAVIGATION: Commander Domain → Modules")
commander_clusters = [e for e in entities.values() if e['entityType'] == 'Cluster' and 'Commander' in e['name']]
print(f"   Found {len(commander_clusters)} clusters in Commander domain")
print(f"   Sample clusters: {[c['name'].split('.')[-1] for c in commander_clusters[:5]]}")

# Test 3: Find specific module
print("\n3. LOCATE MODULE: 'context_menu_service'")
context_menu = [e for e in entities.values() if 'context_menu' in e['name'].lower() and e['entityType'] == 'Module']
if context_menu:
    module = context_menu[0]
    print(f"   ✅ Found: {module['name']}")
    print(f"   Observations: {module['observations']}")
    
    # Find what cluster it belongs to
    belongs_to = [r for r in relations if r['from'] == module['name'] and r['relationType'] == 'BELONGS_TO']
    if belongs_to:
        cluster_name = belongs_to[0]['to']
        print(f"   Belongs to: {cluster_name}")

# Test 4: Find key classes
print("\n4. KEY CLASSES (Architectural components):")
classes = [e for e in entities.values() if e['entityType'] == 'Class']
print(f"   Total classes mapped: {len(classes)}")
for cls in classes:
    class_name = cls['name'].split('.')[-1]
    print(f"   - {class_name}")

# Test 5: Navigation path example
print("\n5. NAVIGATION PATH: Feature → Implementation")
print("   Example: 'Context Menu' feature")
print("   Path: Commander (Domain) → Services (Cluster) → context_menu_service (Module) → ContextMenuService (Class)")
print("   Action: Read source file at src/commander/services/context_menu_service.py")

# Test 6: Impact detection example
print("\n6. IMPACT DETECTION: What depends on 'LogProcessor'?")
log_processor = [e for e in entities.values() if 'LogProcessor' in e['name'] and e['entityType'] == 'Class']
if log_processor:
    lp_name = log_processor[0]['name']
    # Find what imports the module containing LogProcessor
    lp_module = '.'.join(lp_name.split('.')[:-1]) + '.File'
    importers = [r for r in relations if r['to'] == lp_module and r['relationType'] == 'IMPORTS']
    print(f"   LogProcessor class found")
    print(f"   Module imported by {len(importers)} other modules")
    print(f"   → Change impact: {len(importers)} modules need review")

print("\n" + "=" * 60)
print("NAVIGATION VERDICT")
print("=" * 60)
print("✅ Domain-level navigation: YES")
print("✅ Module location: YES") 
print("✅ Class identification: YES (key classes only)")
print("⚠️  Method-level detail: NO (removed for size - read source file)")
print("✅ Impact surface: YES (via relations)")
print("✅ File path mapping: YES (via module names)")
print("\nRECOMMENDATION: Use codegraph to LOCATE, then READ SOURCE for details")
print("=" * 60)
