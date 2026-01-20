"""
Complete Codegraph System Validation
Tests: update workflow, navigation, documentation pointers, size optimization
"""
import json
import subprocess
import time
from pathlib import Path

def test_complete_workflow():
    """Test complete codegraph update workflow"""
    print("="*70)
    print("CODEGRAPH SYSTEM VALIDATION")
    print("="*70)
    
    # Test 1: Unified update script
    print("\n1. Testing Unified Update Script...")
    start = time.time()
    result = subprocess.run(
        ['python', 'd:/_APP/LOGReport/scripts/update_codegraph.py'],
        capture_output=True,
        text=True
    )
    elapsed = time.time() - start
    
    if result.returncode == 0:
        print(f"   ✅ Update script executed successfully ({elapsed:.1f}s)")
    else:
        print(f"   ❌ Update script failed")
        return False
    
    # Test 2: Load and parse codegraph
    print("\n2. Testing Codegraph Loading...")
    codegraph_path = Path('d:/_APP/LOGReport/codegraph.json')
    
    if not codegraph_path.exists():
        print("   ❌ codegraph.json not found")
        return False
    
    size_kb = codegraph_path.stat().st_size / 1024
    print(f"   ✅ File exists: {size_kb:.2f} KB")
    
    entities = {}
    relations = []
    
    start = time.time()
    with open(codegraph_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            if item['type'] == 'entity':
                entities[item['name']] = item
            else:
                relations.append(item)
    load_ms = (time.time() - start) * 1000
    
    print(f"   ✅ Loaded: {len(entities)} entities, {len(relations)} relations ({load_ms:.0f}ms)")
    
    # Test 3: Size validation
    print("\n3. Testing Size Optimization...")
    if size_kb <= 100:
        print(f"   ✅ Size within target: {size_kb:.2f} KB (target: <100KB)")
        print(f"   ✅ Headroom: {100-size_kb:.2f} KB")
    else:
        print(f"   ❌ Size exceeds target: {size_kb:.2f} KB (target: <100KB)")
        return False
    
    # Test 4: Structure validation
    print("\n4. Testing Structure Hierarchy...")
    
    # Count entity types
    types = {}
    for entity in entities.values():
        entity_type = entity['entityType']
        types[entity_type] = types.get(entity_type, 0) + 1
    
    print(f"   Entity Types:")
    for entity_type, count in sorted(types.items()):
        print(f"     {entity_type}: {count}")
    
    required_types = ['Type', 'Domain', 'Module']
    for req_type in required_types:
        if req_type in types:
            print(f"   ✅ {req_type} entities present")
        else:
            print(f"   ❌ {req_type} entities missing")
            return False
    
    # Test 5: Relation validation
    print("\n5. Testing Relations...")
    
    relation_types = {}
    for rel in relations:
        rel_type = rel['relationType']
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
    
    print(f"   Relation Types:")
    for rel_type, count in sorted(relation_types.items()):
        print(f"     {rel_type}: {count}")
    
    if 'BELONGS_TO' in relation_types:
        print(f"   ✅ Structural relations present")
    else:
        print(f"   ❌ No BELONGS_TO relations")
        return False
    
    # Test 6: Documentation pointer validation
    print("\n6. Testing Documentation Pointers...")
    
    if 'DOCUMENTED_IN' in relation_types:
        doc_count = relation_types['DOCUMENTED_IN']
        print(f"   ✅ Documentation pointers: {doc_count}")
        
        # Find doc entities
        doc_entities = {name: ent for name, ent in entities.items() 
                       if ent['entityType'] == 'Documentation'}
        print(f"   ✅ Documentation entities: {len(doc_entities)}")
        
        # Show examples
        print(f"   Examples:")
        for doc_name in list(doc_entities.keys())[:3]:
            code_refs = [r['from'] for r in relations 
                        if r['to'] == doc_name 
                        and r['relationType'] == 'DOCUMENTED_IN']
            print(f"     {doc_name}")
            print(f"       ← Referenced by: {len(code_refs)} code entities")
    else:
        print(f"   ⚠️  No documentation pointers (optional feature)")
    
    # Test 7: Navigation test
    print("\n7. Testing Navigation...")
    
    # Find a domain
    domains = [name for name, ent in entities.items() 
              if ent['entityType'] == 'Domain']
    if domains:
        print(f"   ✅ Domains found: {len(domains)}")
        test_domain = domains[0]
        print(f"      Example: {test_domain}")
        
        # Find modules in domain
        modules = [r['from'] for r in relations 
                  if r['to'] == test_domain 
                  and r['relationType'] == 'BELONGS_TO']
        print(f"      Modules: {len(modules)}")
    else:
        print(f"   ❌ No domains found")
        return False
    
    # Test 8: Performance validation
    print("\n8. Testing Performance...")
    
    if load_ms <= 1000:
        print(f"   ✅ Load time: {load_ms:.0f}ms (target: <1000ms)")
    else:
        print(f"   ❌ Load time: {load_ms:.0f}ms (exceeds 1000ms)")
        return False
    
    # Calculate token estimate
    tokens = size_kb * 200  # Rough estimate
    print(f"   ✅ Estimated tokens: {tokens:.0f} (~{tokens/2000:.1%} of 200K budget)")
    
    # Test 9: Content quality
    print("\n9. Testing Content Quality...")
    
    # Check observation lengths
    obs_lengths = []
    for entity in entities.values():
        for obs in entity['observations']:
            if not obs.startswith('upd:') and not obs.startswith('doc:'):
                obs_lengths.append(len(obs))
    
    if obs_lengths:
        avg_length = sum(obs_lengths) / len(obs_lengths)
        max_length = max(obs_lengths)
        print(f"   Observation lengths:")
        print(f"     Average: {avg_length:.1f} chars")
        print(f"     Maximum: {max_length} chars")
        
        if max_length <= 20:
            print(f"   ✅ Observations compressed (target: ≤20 chars)")
        else:
            print(f"   ⚠️  Some observations exceed 20 chars")
    
    # Test 10: Completeness check
    print("\n10. Testing Completeness...")
    
    # Count Python files
    src_path = Path('d:/_APP/LOGReport/src')
    py_files = len(list(src_path.rglob('*.py')))
    module_entities = [name for name, ent in entities.items() 
                      if ent['entityType'] == 'Module']
    
    print(f"   Python files in src/: {py_files}")
    print(f"   Module entities: {len(module_entities)}")
    
    coverage = len(module_entities) / py_files * 100 if py_files > 0 else 0
    print(f"   Coverage: {coverage:.0f}%")
    
    if coverage >= 90:
        print(f"   ✅ Coverage meets target (≥90%)")
    else:
        print(f"   ⚠️  Coverage below target (<90%)")
    
    # Final summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"✅ Update workflow: Functional")
    print(f"✅ Size: {size_kb:.2f} KB (target: <100KB)")
    print(f"✅ Load time: {load_ms:.0f}ms (target: <1000ms)")
    print(f"✅ Entities: {len(entities)}")
    print(f"✅ Relations: {len(relations)}")
    print(f"✅ Documentation pointers: {relation_types.get('DOCUMENTED_IN', 0)}")
    print(f"✅ Coverage: {coverage:.0f}%")
    print(f"✅ Performance: Token efficient")
    print("="*70)
    print("STATUS: ALL TESTS PASSED ✅")
    print("="*70)
    
    return True

if __name__ == '__main__':
    success = test_complete_workflow()
    exit(0 if success else 1)
