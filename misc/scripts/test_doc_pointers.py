"""
Test enhanced codegraph navigation with documentation pointers
"""
import json
from pathlib import Path

def load_codegraph(path):
    """Load codegraph"""
    entities = {}
    relations = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if item['type'] == 'entity':
                entities[item['name']] = item
            else:
                relations.append(item)
    return entities, relations

def test_doc_pointers():
    """Test documentation pointer navigation"""
    entities, relations = load_codegraph('d:/_APP/LOGReport/codegraph.json')
    
    print("=" * 60)
    print("DOCUMENTATION POINTER TEST")
    print("=" * 60)
    
    # Test 1: Find documentation for Commander domain
    print("\n1. Commander Domain Documentation:")
    commander_docs = [r for r in relations 
                      if r['from'] == 'Code.Domain.Commander' 
                      and r['relationType'] == 'DOCUMENTED_IN']
    if commander_docs:
        for doc_rel in commander_docs:
            doc_name = doc_rel['to']
            print(f"   📄 {doc_name}")
            if doc_name in entities:
                print(f"      {entities[doc_name]['observations']}")
    else:
        print("   ⚠️  No docs found")
    
    # Test 2: Find all code entities with documentation
    print("\n2. Code Entities with Documentation Pointers:")
    code_with_docs = set()
    for rel in relations:
        if rel['relationType'] == 'DOCUMENTED_IN':
            code_with_docs.add(rel['from'])
    
    for entity_name in sorted(code_with_docs):
        if entity_name in entities:
            entity = entities[entity_name]
            docs = [r['to'] for r in relations 
                   if r['from'] == entity_name 
                   and r['relationType'] == 'DOCUMENTED_IN']
            print(f"   📦 {entity_name}")
            print(f"      Type: {entity['entityType']}")
            for doc in docs:
                print(f"      📄 {doc}")
    
    # Test 3: Find all documentation entities
    print("\n3. Documentation Entities:")
    doc_entities = {name: ent for name, ent in entities.items() 
                    if ent['entityType'] == 'Documentation'}
    for doc_name, doc_entity in sorted(doc_entities.items()):
        print(f"   📄 {doc_name}")
        print(f"      {doc_entity['observations']}")
        
        # Find what code points to this doc
        code_refs = [r['from'] for r in relations 
                    if r['to'] == doc_name 
                    and r['relationType'] == 'DOCUMENTED_IN']
        if code_refs:
            print(f"      Referenced by: {len(code_refs)} code entities")
            for ref in code_refs:
                print(f"         ← {ref}")
    
    # Test 4: Navigation workflow
    print("\n4. Navigation Workflow Example:")
    print("   Scenario: Find ContextMenuService documentation")
    target = 'Code.Class.commander_services_context_menu_service.ContextMenuService'
    
    if target in entities:
        print(f"   ✅ Found: {target}")
        print(f"      Observations: {entities[target]['observations']}")
        
        # Find its documentation
        docs = [r['to'] for r in relations 
               if r['from'] == target 
               and r['relationType'] == 'DOCUMENTED_IN']
        
        if docs:
            print(f"      📄 Documentation: {docs}")
            for doc in docs:
                if doc in entities:
                    print(f"         Path: {entities[doc]['observations']}")
        else:
            print(f"      ⚠️  No documentation linked")
        
        # Find its module
        belongs = [r['to'] for r in relations 
                  if r['from'] == target 
                  and r['relationType'] == 'BELONGS_TO']
        if belongs:
            print(f"      📦 Module: {belongs[0]}")
    
    # Test 5: Size validation
    print("\n5. Size Validation:")
    codegraph_path = Path('d:/_APP/LOGReport/codegraph.json')
    size_kb = codegraph_path.stat().st_size / 1024
    print(f"   Size: {size_kb:.2f} KB")
    print(f"   Entities: {len(entities)} (including {len(doc_entities)} doc entities)")
    print(f"   Relations: {len(relations)}")
    if size_kb <= 100:
        print(f"   ✅ Within 100KB target ({100-size_kb:.2f} KB remaining)")
    else:
        print(f"   ⚠️  Exceeds 100KB target by {size_kb-100:.2f} KB")
    
    print("\n" + "=" * 60)
    print("NAVIGATION PATTERN:")
    print("=" * 60)
    print("1. Query codegraph for entity (e.g., Code.Class.X)")
    print("2. Check for DOCUMENTED_IN relations")
    print("3. Load referenced documentation (e.g., Doc:BLUEPRINT_X.md)")
    print("4. Read actual doc file for detailed explanation")
    print("5. Read source code for implementation details")
    print("\nResult: Codegraph = map + pointers, not full content")
    print("=" * 60)

if __name__ == '__main__':
    test_doc_pointers()
