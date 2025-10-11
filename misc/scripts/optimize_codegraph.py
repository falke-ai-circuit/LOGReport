"""
Codegraph Optimizer - Aggressively reduce size for constant loading
Target: <100KB (90% reduction) while maintaining navigability
"""
import json
import sys
from pathlib import Path

def load_codegraph(path):
    """Load codegraph entities and relations"""
    entities = []
    relations = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if item['type'] == 'entity':
                entities.append(item)
            else:
                relations.append(item)
    return entities, relations

def is_private_method(name):
    """Check if method is private (skip these for size reduction)"""
    if '.Method.' not in name and '.Function.' not in name:
        return False
    method_name = name.split('.')[-1]
    # Skip private but keep __init__
    return method_name.startswith('_') and method_name != '__init__'

def is_utility_class(name):
    """Check if class is utility/internal"""
    class_name = name.split('.')[-1]
    return class_name.endswith('Signals') or class_name.endswith('Worker') or 'Internal' in class_name

def compress_observation(obs):
    """Compress observation to max 80 chars"""
    if len(obs) <= 80:
        return obs
    # Keep important prefixes
    if obs.startswith('Method in') or obs.startswith('Function in') or obs.startswith('Class in'):
        prefix = obs.split()[0] + ' in ' + obs.split()[2]
        remaining = 80 - len(prefix) - 3
        return prefix + ' - ' + obs[len(prefix):len(prefix)+remaining].strip()
    return obs[:77] + '...'

def optimize_codegraph(input_path, output_path):
    """Optimize codegraph for size - ULTRA AGGRESSIVE"""
    entities, relations = load_codegraph(input_path)
    
    print(f"Original: {len(entities)} entities, {len(relations)} relations")
    
    # Define key classes to keep methods for (architectural importance)
    key_classes = [
        'LogReportGUI', 'CommanderWindow', 'CommanderPresenter', 'NodeTreePresenter', 'NodeTreeView',
        'ContextMenuService', 'TelnetService', 'CommandQueue', 'LogProcessor', 'ReportGenerator',
        'NodeManager', 'SessionManager', 'BsToolCommandService', 'FbcCommandService', 'RpcCommandService'
    ]
    
    # Filter entities - ULTRA AGGRESSIVE
    kept_entities = []
    removed_names = set()
    entity_map = {e['name']: e for e in entities}
    
    for entity in entities:
        name = entity['name']
        entity_type = entity['entityType']
        
        # Keep: Type, Domain, Cluster - minimal
        if entity_type in ['Type', 'Domain', 'Cluster']:
            entity['observations'] = [obs[:50] for obs in entity['observations'][:1]]
            kept_entities.append(entity)
            continue
        
        # Keep modules - ultra minimal
        if entity_type == 'Module':
            module_name = name.split('.')[-2]
            entity['observations'] = [f"{module_name}", "upd:2025-10-11,refs:0"]
            kept_entities.append(entity)
            continue
        
        # Keep only KEY classes
        if entity_type == 'Class':
            class_name = name.split('.')[-1]
            # Only keep if in key_classes list
            if any(key in class_name for key in key_classes):
                entity['observations'] = [class_name, entity['observations'][-1]]
                kept_entities.append(entity)
            else:
                removed_names.add(name)
            continue
        
        # For methods: ONLY KEEP __init__ and key public methods OF KEY CLASSES
        if entity_type in ['Method', 'Function']:
            method_name = name.split('.')[-1]
            
            # Check if method belongs to a key class
            belongs_to_key_class = False
            for key_class in key_classes:
                if f"_{key_class}." in name:
                    belongs_to_key_class = True
                    break
            
            if not belongs_to_key_class:
                removed_names.add(name)
                continue
            
            # Only keep __init__ and select public methods
            if method_name == '__init__':
                entity['observations'] = ["init", entity['observations'][-1]]
                kept_entities.append(entity)
            elif not method_name.startswith('_') and method_name in [
                'process_directory', 'execute', 'send_command', 'handle_command', 
                'update_node', 'generate_pdf', 'load_config', 'save_config'
            ]:
                entity['observations'] = [method_name, entity['observations'][-1]]
                kept_entities.append(entity)
            else:
                removed_names.add(name)
            continue
        
        # Skip everything else
        removed_names.add(name)
    
    # Filter relations - MINIMAL (only hierarchy)
    kept_relations = []
    for rel in relations:
        # Skip relations to removed entities
        if rel['from'] in removed_names or rel['to'] in removed_names:
            continue
        
        # Keep only: BELONGS_TO (hierarchy), INHERITS (class hierarchy), key IMPORTS
        if rel['relationType'] in ['BELONGS_TO', 'INHERITS']:
            kept_relations.append(rel)
            continue
        
        # Keep IMPORTS only between modules (not to external libs)
        if rel['relationType'] == 'IMPORTS':
            if 'Code.Module.' in rel['from'] and 'Code.Module.' in rel['to']:
                kept_relations.append(rel)
            continue
    
    print(f"Optimized: {len(kept_entities)} entities (-{len(entities)-len(kept_entities)}), {len(kept_relations)} relations (-{len(relations)-len(kept_relations)})")
    
    # Write optimized codegraph
    with open(output_path, 'w', encoding='utf-8') as f:
        for entity in kept_entities:
            f.write(json.dumps(entity) + '\n')
        for relation in kept_relations:
            f.write(json.dumps(relation) + '\n')
    
    # Report size
    size_kb = Path(output_path).stat().st_size / 1024
    print(f"Output size: {size_kb:.2f} KB")
    
    if size_kb > 100:
        print(f"⚠️  Still over target by {size_kb-100:.2f} KB - need more reduction")
    else:
        print(f"✅ Within target (<100KB) - {100-size_kb:.2f} KB under")
    
    return len(kept_entities), len(kept_relations), size_kb

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'codegraph_new.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'codegraph_optimized.json'
    
    optimize_codegraph(input_file, output_file)
