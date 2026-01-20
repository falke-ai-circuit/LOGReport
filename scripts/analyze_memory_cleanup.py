#!/usr/bin/env python3
"""
Analyze memory for entities that should be cleaned up.
Identifies meta-entities, low-value entities, and organizational clutter.
"""

import json
from pathlib import Path
from collections import defaultdict

def load_memory(filepath):
    """Load JSONL memory file"""
    entities = []
    relations = []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'entity':
                    entities.append(data)
                elif data.get('type') == 'relation':
                    relations.append(data)
            except json.JSONDecodeError:
                continue
    
    return entities, relations

def analyze_cleanup_candidates(entities, relations):
    """Identify entities that should be removed"""
    
    # Build connection map
    entity_names = {e['name'] for e in entities}
    connected = set()
    for rel in relations:
        if rel.get('from') in entity_names:
            connected.add(rel['from'])
        if rel.get('to') in entity_names:
            connected.add(rel['to'])
    
    disconnected = entity_names - connected
    
    # Categories for removal
    removal_categories = {
        'meta_types': [],          # MemoryType entities (organizational metadata)
        'cluster_meta': [],        # Cluster entities
        'domain_meta': [],         # Domain entities
        'type_meta': [],           # Type entities
        'documentation_meta': [],  # Generic documentation entities
        'low_value': [],           # Minimal observations
        'disconnected': [],        # No relations
        'verbose': [],             # Overly verbose
        'obsolete': [],            # Old timestamps with no refs
    }
    
    for entity in entities:
        name = entity['name']
        entity_type = entity.get('entityType', '')
        observations = entity.get('observations', [])
        
        # Meta-type entities (organizational only, no workflow value)
        if entity_type == 'MemoryType':
            removal_categories['meta_types'].append({
                'name': name,
                'reason': 'Organizational metadata, not workflow knowledge',
                'observations': observations
            })
        
        # Cluster/Domain/Type meta entities
        elif name.startswith('Project.Cluster.') or entity_type == 'Cluster':
            removal_categories['cluster_meta'].append({
                'name': name,
                'reason': 'Cluster organizational entity',
                'observations': observations
            })
        elif name.startswith('Project.Domain.') or entity_type == 'Domain':
            removal_categories['domain_meta'].append({
                'name': name,
                'reason': 'Domain organizational entity',
                'observations': observations
            })
        elif name.startswith('Project.Type.') or entity_type == 'Type':
            removal_categories['type_meta'].append({
                'name': name,
                'reason': 'Type organizational entity',
                'observations': observations
            })
        
        # Generic documentation entities (README/TODO extraction, no unique value)
        elif entity_type == 'Document' and any(kw in name for kw in ['Project_Overview', 'Project_Features', 'Project_Requirements', 'Project_Installation', 'Project_Usage', 'Project_Tasks']):
            removal_categories['documentation_meta'].append({
                'name': name,
                'reason': 'Generic README/TODO extraction, no unique workflow value',
                'observations': observations
            })
        
        # Low-value entities (minimal observations)
        elif len(observations) <= 1 or all(len(obs) < 25 for obs in observations):
            removal_categories['low_value'].append({
                'name': name,
                'reason': 'Minimal observations, low information value',
                'observations': observations
            })
        
        # Disconnected entities
        elif name in disconnected:
            removal_categories['disconnected'].append({
                'name': name,
                'reason': 'No connections to other entities',
                'observations': observations
            })
        
        # Overly verbose (>500 chars total)
        elif sum(len(obs) for obs in observations) > 500:
            removal_categories['verbose'].append({
                'name': name,
                'reason': 'Overly verbose, needs condensation',
                'observations': observations,
                'total_chars': sum(len(obs) for obs in observations)
            })
    
    return removal_categories

def main():
    memory_path = Path('project_memory.json')
    
    print("=" * 80)
    print("MEMORY CLEANUP ANALYSIS")
    print("=" * 80)
    print()
    
    entities, relations = load_memory(memory_path)
    print(f"Loaded: {len(entities)} entities, {len(relations)} relations")
    print()
    
    categories = analyze_cleanup_candidates(entities, relations)
    
    total_removable = 0
    
    for category, items in categories.items():
        if items:
            print(f"\n{category.upper().replace('_', ' ')}: {len(items)} entities")
            print("-" * 80)
            total_removable += len(items)
            
            # Show first 5 examples
            for item in items[:5]:
                print(f"  • {item['name']}")
                print(f"    Reason: {item['reason']}")
                if 'total_chars' in item:
                    print(f"    Total chars: {item['total_chars']}")
                print(f"    Observations: {len(item['observations'])}")
                if item['observations']:
                    first_obs = item['observations'][0]
                    preview = first_obs[:70] + '...' if len(first_obs) > 70 else first_obs
                    print(f"    Preview: {preview}")
                print()
            
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
                print()
    
    print("=" * 80)
    print(f"TOTAL REMOVAL CANDIDATES: {total_removable} / {len(entities)} ({total_removable/len(entities)*100:.1f}%)")
    print("=" * 80)
    print()
    
    # Breakdown
    print("REMOVAL BREAKDOWN:")
    for category, items in categories.items():
        if items:
            print(f"  {category:25s}: {len(items):4d} entities")
    
    print()
    print("RECOMMENDATION:")
    print("  1. Remove all MemoryType entities (organizational metadata only)")
    print("  2. Remove Cluster/Domain/Type meta entities (hierarchy handled by relations)")
    print("  3. Remove generic documentation entities (README/TODO extractions)")
    print("  4. Remove or condense low-value entities (minimal observations)")
    print("  5. Review disconnected entities for relevance")
    print("  6. Condense verbose entities to 80-char observations")

if __name__ == '__main__':
    main()
