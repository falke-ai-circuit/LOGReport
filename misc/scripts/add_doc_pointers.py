"""
Enhance codegraph with documentation pointers
Creates DOCUMENTED_IN relations linking code entities to documentation files
"""
import json
from pathlib import Path
import re

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

def scan_documentation():
    """Scan docs folder and map to code entities"""
    doc_mappings = {
        'architecture': {},  # ARCH_*.md -> Domains
        'technical': {},     # TECH_*.md -> Modules/Classes
        'blueprints': {},    # BLUEPRINT_*.md -> Features/Classes
        'implementation': {} # IMPL_*.md -> Specific implementations
    }
    
    docs_path = Path('d:/_APP/LOGReport/docs')
    
    # Scan architecture docs
    for arch_doc in (docs_path / 'architecture').glob('ARCH_*.md'):
        doc_name = arch_doc.stem.replace('ARCH_', '').lower()
        # Map to domains
        if 'command' in doc_name:
            doc_mappings['architecture']['Code.Domain.Commander'] = str(arch_doc.relative_to('d:/_APP/LOGReport'))
        elif 'node' in doc_name:
            doc_mappings['architecture']['Code.Domain.Commander'] = str(arch_doc.relative_to('d:/_APP/LOGReport'))
        elif 'memory' in doc_name:
            doc_mappings['architecture']['Code.Domain.Core'] = str(arch_doc.relative_to('d:/_APP/LOGReport'))
    
    # Scan technical docs
    for tech_doc in (docs_path / 'technical').glob('TECH_*.md'):
        doc_name = tech_doc.stem.replace('TECH_', '').lower()
        # Map to modules/clusters
        if 'commander' in doc_name:
            doc_mappings['technical']['Code.Module.commander_main_window.File'] = str(tech_doc.relative_to('d:/_APP/LOGReport'))
        elif 'codegraph' in doc_name:
            doc_mappings['technical']['ALL_MODULES'] = str(tech_doc.relative_to('d:/_APP/LOGReport'))
        elif 'token' in doc_name:
            doc_mappings['technical']['Code.Module.sys_file_loader.File'] = str(tech_doc.relative_to('d:/_APP/LOGReport'))
    
    # Scan blueprints
    for bp_doc in (docs_path / 'blueprints').glob('BLUEPRINT_*.md'):
        doc_name = bp_doc.stem.replace('BLUEPRINT_', '').lower()
        # Map to classes/features
        if 'context_menu' in doc_name:
            doc_mappings['blueprints']['Code.Class.commander_services_context_menu_service.ContextMenuService'] = str(bp_doc.relative_to('d:/_APP/LOGReport'))
        elif 'bstool' in doc_name:
            doc_mappings['blueprints']['Code.Module.commander_services_bstool_command_service.File'] = str(bp_doc.relative_to('d:/_APP/LOGReport'))
    
    return doc_mappings

def add_doc_pointers(entities, relations):
    """Add DOCUMENTED_IN relations and doc_ref observations"""
    doc_mappings = scan_documentation()
    
    new_relations = []
    entity_updates = {}
    
    # Add specific mappings
    mappings = [
        # Architecture -> Domains
        ('Code.Domain.Commander', 'docs/architecture/ARCH_command_system.md'),
        ('Code.Domain.Core', 'docs/architecture/ARCH_memory_system.md'),
        
        # Technical -> Key modules
        ('Code.Module.commander_main_window.File', 'docs/technical/TECH_commander_window.md'),
        ('Code.Module.sys_file_loader.File', 'docs/technical/TECH_token_management.md'),
        
        # Blueprints -> Classes
        ('Code.Class.commander_services_context_menu_service.ContextMenuService', 'docs/blueprints/BLUEPRINT_context_menu.md'),
        
        # Navigation guide for all
        ('Code.Type.Codebase', 'docs/technical/TECH_codegraph_navigation.md'),
    ]
    
    for entity_name, doc_path in mappings:
        # Add DOCUMENTED_IN relation
        new_relations.append({
            'type': 'relation',
            'from': entity_name,
            'to': f'Doc:{doc_path}',
            'relationType': 'DOCUMENTED_IN'
        })
        
        # Track for observation update
        if entity_name not in entity_updates:
            entity_updates[entity_name] = []
        entity_updates[entity_name].append(f'doc:{doc_path.split("/")[-1]}')
    
    # Update entity observations with doc references
    for entity in entities:
        if entity['name'] in entity_updates:
            # Add doc reference to observations (within size limit)
            doc_ref = entity_updates[entity['name']][0]
            if len(doc_ref) <= 18:  # Stay within our char limit
                # Insert before metadata
                entity['observations'].insert(-1, doc_ref)
    
    return entities, relations + new_relations

def create_doc_entities():
    """Create pseudo-entities for documentation files"""
    doc_entities = [
        {
            'type': 'entity',
            'name': 'Doc:ARCH_command_system.md',
            'entityType': 'Documentation',
            'observations': ['Command arch', 'docs/architecture/', 'upd:2025-10-11,refs:0']
        },
        {
            'type': 'entity',
            'name': 'Doc:TECH_codegraph_navigation.md',
            'entityType': 'Documentation',
            'observations': ['Codegraph guide', 'docs/technical/', 'upd:2025-10-11,refs:0']
        },
        {
            'type': 'entity',
            'name': 'Doc:BLUEPRINT_context_menu.md',
            'entityType': 'Documentation',
            'observations': ['Context menu spec', 'docs/blueprints/', 'upd:2025-10-11,refs:0']
        },
    ]
    return doc_entities

def enhance_codegraph(input_path, output_path):
    """Enhance codegraph with documentation pointers"""
    entities, relations = load_codegraph(input_path)
    
    print(f"Original: {len(entities)} entities, {len(relations)} relations")
    
    # Add documentation pointers
    entities, relations = add_doc_pointers(entities, relations)
    
    # Add doc entities
    doc_entities = create_doc_entities()
    entities.extend(doc_entities)
    
    print(f"Enhanced: {len(entities)} entities (+{len(doc_entities)} doc entities), {len(relations)} relations")
    
    # Write enhanced codegraph
    with open(output_path, 'w', encoding='utf-8') as f:
        for entity in entities:
            f.write(json.dumps(entity, separators=(',', ':')) + '\n')
        for relation in relations:
            f.write(json.dumps(relation, separators=(',', ':')) + '\n')
    
    size_kb = Path(output_path).stat().st_size / 1024
    print(f"Output size: {size_kb:.2f} KB")
    
    if size_kb > 100:
        print(f"⚠️  Over target by {size_kb-100:.2f} KB")
    else:
        print(f"✅ Within target by {100-size_kb:.2f} KB")
    
    return len(entities), len(relations), size_kb

if __name__ == '__main__':
    input_file = 'd:/_APP/LOGReport/codegraph.json'
    output_file = input_file
    
    enhance_codegraph(input_file, output_file)
