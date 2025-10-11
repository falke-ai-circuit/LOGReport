"""
Verify enhanced codegraph has functional observations
"""
import json
from pathlib import Path

def verify_observations():
    """Check that observations are functional"""
    codegraph_path = Path('d:/_APP/LOGReport/codegraph.json')
    
    entities = {}
    with open(codegraph_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if item['type'] == 'entity':
                entities[item['name']] = item
    
    print("="*70)
    print("CODEGRAPH OBSERVATION VERIFICATION")
    print("="*70)
    
    # Sample modules
    print("\n1. Sample Module Observations:")
    module_samples = [
        'Code.Module.sys_file_loader.File',
        'Code.Module.commander_main_window.File',
        'Code.Module.commander_services_context_menu_service.File',
        'Code.Module.gui.File',
        'Code.Module.commander_node_manager.File',
    ]
    
    for module_name in module_samples:
        if module_name in entities:
            entity = entities[module_name]
            obs = entity['observations']
            # First non-metadata observation
            desc = [o for o in obs if not o.startswith('upd:') and not o.startswith('doc:') and '/' not in o]
            if desc:
                print(f"   📦 {module_name.split('.')[-2]}")
                print(f"      {desc[0]}")
    
    # Sample classes
    print("\n2. Sample Class Observations:")
    class_samples = [
        'Code.Class.commander_services_context_menu_service.ContextMenuService',
        'Code.Class.commander_views_node_tree_view.NodeTreeView',
        'Code.Class.commander_presenters_node_tree_presenter.NodeTreePresenter',
    ]
    
    for class_name in class_samples:
        if class_name in entities:
            entity = entities[class_name]
            obs = entity['observations']
            desc = [o for o in obs if not o.startswith('upd:') and not o.startswith('doc:') and '/' not in o]
            if desc:
                print(f"   🔷 {class_name.split('.')[-1]}")
                print(f"      {desc[0]}")
    
    # Statistics
    print("\n3. Observation Statistics:")
    
    module_entities = {name: ent for name, ent in entities.items() if ent['entityType'] == 'Module'}
    class_entities = {name: ent for name, ent in entities.items() if ent['entityType'] == 'Class'}
    
    # Check which have functional descriptions
    modules_with_desc = 0
    class_with_desc = 0
    
    desc_lengths = []
    
    for entity in module_entities.values():
        obs = entity['observations']
        desc = [o for o in obs if not o.startswith('upd:') and not o.startswith('doc:') and '/' not in o]
        if desc and desc[0] != entity['name'].split('.')[-2]:  # Not just module name
            modules_with_desc += 1
            desc_lengths.append(len(desc[0]))
    
    for entity in class_entities.values():
        obs = entity['observations']
        desc = [o for o in obs if not o.startswith('upd:') and not o.startswith('doc:') and '/' not in o]
        if desc and desc[0] != entity['name'].split('.')[-1]:  # Not just class name
            class_with_desc += 1
            desc_lengths.append(len(desc[0]))
    
    print(f"   Modules: {len(module_entities)}")
    print(f"   Modules with functional descriptions: {modules_with_desc} ({modules_with_desc/len(module_entities)*100:.0f}%)")
    print(f"   Classes: {len(class_entities)}")
    print(f"   Classes with functional descriptions: {class_with_desc} ({class_with_desc/len(class_entities)*100:.0f}%)")
    
    if desc_lengths:
        avg_length = sum(desc_lengths) / len(desc_lengths)
        print(f"   Average description length: {avg_length:.0f} chars")
        print(f"   Min: {min(desc_lengths)}, Max: {max(desc_lengths)}")
    
    # Size check
    print("\n4. Size Validation:")
    size_kb = codegraph_path.stat().st_size / 1024
    print(f"   Size: {size_kb:.2f} KB")
    print(f"   Target: <100 KB")
    if size_kb <= 100:
        print(f"   ✅ Within target ({100-size_kb:.2f} KB remaining)")
    else:
        print(f"   ⚠️  Exceeds target by {size_kb-100:.2f} KB")
    
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70)

if __name__ == '__main__':
    verify_observations()
