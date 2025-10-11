"""
Add functional observations to codegraph entities
Enhances navigation with "what does this module do?" context
Target: 50-80 char observations for modules/classes
"""
import json
from pathlib import Path
import ast

def load_codegraph(path):
    """Load existing codegraph"""
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

def extract_module_purpose(file_path):
    """Extract module purpose from docstring or first comment"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            
            # Try module docstring
            docstring = ast.get_docstring(tree)
            if docstring:
                # Get first line, truncate to 60 chars
                first_line = docstring.split('\n')[0].strip()
                return first_line[:60]
            
            # Try first comment
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line.startswith('#') and not line.startswith('#!'):
                    comment = line.lstrip('#').strip()
                    if len(comment) > 10:  # Meaningful comment
                        return comment[:60]
            
            # Fallback: analyze classes/functions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')]
            
            if classes:
                return f"Implements {', '.join(classes[:2])}"[:60]
            elif functions:
                return f"Provides {', '.join(functions[:2])}"[:60]
            
    except:
        pass
    
    return None

def get_manual_descriptions():
    """Manual descriptions for key modules where auto-extraction fails"""
    return {
        # Core modules
        'sys_file_loader': 'Loads system log files, detects tokens, validates format',
        'token_detector': 'Detects and validates log tokens (AP01M, FBC, RPC)',
        'log_processor': 'Processes log files, extracts data, generates reports',
        
        # Commander modules
        'commander_main_window': 'Main window for Commander UI, node tree management',
        'node_manager': 'Manages node tree operations, validation, state',
        'node_tree_view': 'Qt tree widget view for nodes, handles UI events',
        'node_tree_presenter': 'Presenter for node tree, mediates view-model',
        
        # Services
        'context_menu_service': 'Context menu actions: edit, delete, validate nodes',
        'bstool_command_service': 'BsTool integration: launches external tool, manages state',
        'error_reporting_reporter': 'Error reporting, logging, user notifications',
        
        # GUI
        'gui': 'Main GUI window, tab management, log processing workflows',
        'log_report_gui': 'Log report generation UI, filters, directory selection',
        
        # Workers
        'worker': 'Background worker for async log processing tasks',
        'file_processor': 'Processes individual log files, extracts tokens',
    }

def enhance_observations(entities):
    """Add functional observations to entities"""
    manual_desc = get_manual_descriptions()
    src_path = Path('d:/_APP/LOGReport/src')
    
    enhanced_count = 0
    
    for entity in entities:
        entity_name = entity['name']
        entity_type = entity['entityType']
        
        # Skip Type, Domain, Documentation entities
        if entity_type in ['Type', 'Domain', 'Documentation']:
            continue
        
        # Get current observations
        obs = entity['observations']
        
        # Check if already has functional description (non-name, non-metadata, non-doc)
        has_description = any(
            o for o in obs 
            if not o.startswith('upd:') 
            and not o.startswith('doc:') 
            and '/' not in o
            and o != entity_name.split('.')[-1]  # Not just the class/module name
            and len(o) > 18
        )
        
        if has_description:
            continue
        
        description = None
        
        # For Module entities
        if entity_type == 'Module':
            # Extract module name from entity name
            # Format: Code.Module.path_to_file.File
            parts = entity_name.split('.')
            if len(parts) >= 3:
                module_path = parts[2]  # e.g., "commander_main_window"
                
                # Check manual descriptions first
                for key, desc in manual_desc.items():
                    if key in module_path:
                        description = desc
                        break
                
                # Try to find source file
                if not description:
                    # Convert module path to file path
                    file_name = module_path.replace('_', '_')
                    potential_files = list(src_path.rglob(f'*{file_name.split("_")[0]}*.py'))
                    
                    for py_file in potential_files:
                        if file_name in str(py_file).replace('\\', '_').replace('/', '_'):
                            extracted = extract_module_purpose(py_file)
                            if extracted:
                                description = extracted
                                break
        
        # For Class entities
        elif entity_type == 'Class':
            class_name = parts[-1] if (parts := entity_name.split('.')) else ''
            
            # Check manual descriptions
            for key, desc in manual_desc.items():
                if key.lower() in class_name.lower():
                    description = desc
                    break
            
            # Fallback: describe based on name
            if not description and class_name:
                if 'Service' in class_name:
                    description = f"Service: {class_name.replace('Service', '')} operations"
                elif 'View' in class_name:
                    description = f"View: UI component for {class_name.replace('View', '')}"
                elif 'Presenter' in class_name:
                    description = f"Presenter: mediates {class_name.replace('Presenter', '')}"
                elif 'Worker' in class_name:
                    description = f"Worker: async {class_name.replace('Worker', '')} processing"
                elif 'Manager' in class_name:
                    description = f"Manages {class_name.replace('Manager', '')} operations"
        
        # Add description if found
        if description:
            # Truncate to 60 chars
            description = description[:60]
            
            # Insert description before doc reference or metadata
            insert_pos = len(obs) - 1  # Before metadata
            for i, o in enumerate(obs):
                if o.startswith('doc:'):
                    insert_pos = i
                    break
            
            obs.insert(insert_pos, description)
            enhanced_count += 1
    
    return enhanced_count

def write_codegraph(entities, relations, output_path):
    """Write enhanced codegraph"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for entity in entities:
            f.write(json.dumps(entity, separators=(',', ':')) + '\n')
        for relation in relations:
            f.write(json.dumps(relation, separators=(',', ':')) + '\n')

def main():
    """Enhance codegraph with functional observations"""
    codegraph_path = Path('d:/_APP/LOGReport/codegraph.json')
    
    print("="*60)
    print("ENHANCING CODEGRAPH WITH FUNCTIONAL OBSERVATIONS")
    print("="*60)
    
    # Load
    print("\n1. Loading codegraph...")
    entities, relations = load_codegraph(codegraph_path)
    print(f"   Loaded: {len(entities)} entities, {len(relations)} relations")
    
    size_before = codegraph_path.stat().st_size / 1024
    print(f"   Size before: {size_before:.2f} KB")
    
    # Enhance
    print("\n2. Adding functional observations...")
    enhanced_count = enhance_observations(entities)
    print(f"   Enhanced: {enhanced_count} entities")
    
    # Write
    print("\n3. Writing enhanced codegraph...")
    write_codegraph(entities, relations, codegraph_path)
    
    size_after = codegraph_path.stat().st_size / 1024
    print(f"   Size after: {size_after:.2f} KB")
    print(f"   Increase: +{size_after - size_before:.2f} KB")
    
    # Validate
    print("\n4. Validation...")
    if size_after <= 100:
        print(f"   ✅ Size within target (<100KB)")
        print(f"   ✅ Headroom: {100 - size_after:.2f} KB")
    else:
        print(f"   ⚠️  Size exceeds target by {size_after - 100:.2f} KB")
    
    print("\n" + "="*60)
    print("ENHANCEMENT COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
