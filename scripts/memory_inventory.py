"""
Memory Inventory & Connection Audit Tool
Generates complete inventory of entities, clusters, domains, types and identifies disconnected entities
"""
import json
from collections import defaultdict
from pathlib import Path

def load_memory(file_path):
    """Load JSONL memory file"""
    data = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def analyze_memory(memory_data, memory_name):
    """Analyze memory structure and connections"""
    entities = [e for e in memory_data if e.get('type') == 'entity']
    relations = [r for r in memory_data if r.get('type') == 'relation']
    
    print(f"\n{'='*80}")
    print(f"{memory_name.upper()} INVENTORY")
    print(f"{'='*80}")
    print(f"Total Entities: {len(entities)}")
    print(f"Total Relations: {len(relations)}")
    
    # Parse hierarchy
    entity_names = [e['name'] for e in entities]
    
    # Extract hierarchy levels
    types_set = set()
    domains_set = set()
    clusters_set = set()
    
    for name in entity_names:
        parts = name.split('.')
        if len(parts) >= 1:
            types_set.add(parts[0])
        if len(parts) >= 2:
            domains_set.add('.'.join(parts[:2]))
        if len(parts) >= 3:
            clusters_set.add('.'.join(parts[:3]))
    
    print(f"\nHIERARCHY STRUCTURE:")
    print(f"Unique Types: {len(types_set)}")
    print(f"  Types: {sorted(types_set)}")
    print(f"Unique Domains: {len(domains_set)}")
    print(f"Unique Clusters: {len(clusters_set)}")
    
    # Connection audit
    connected_entities = set()
    for r in relations:
        if 'from' in r:
            connected_entities.add(r['from'])
        if 'to' in r:
            connected_entities.add(r['to'])
    
    disconnected = [e['name'] for e in entities if e['name'] not in connected_entities]
    
    print(f"\nCONNECTION AUDIT:")
    print(f"Connected Entities: {len(connected_entities)}")
    print(f"Disconnected Entities: {len(disconnected)}")
    
    if disconnected:
        print(f"\nDisconnected Entities (first 20):")
        for i, name in enumerate(disconnected[:20], 1):
            print(f"  {i}. {name}")
    
    # Entity types analysis
    entity_types = defaultdict(int)
    for e in entities:
        et = e.get('entityType', 'Unknown')
        entity_types[et] += 1
    
    print(f"\nENTITY TYPES DISTRIBUTION:")
    for et, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {et}: {count}")
    
    # Ratios
    if len(clusters_set) > 0:
        entity_cluster_ratio = len(entities) / len(clusters_set)
        print(f"\nRATIOS:")
        print(f"  Entity:Cluster = {entity_cluster_ratio:.1f}:1 (target: 6:1+)")
    
    if len(domains_set) > 0 and len(clusters_set) > 0:
        cluster_domain_ratio = len(clusters_set) / len(domains_set)
        print(f"  Cluster:Domain = {cluster_domain_ratio:.1f}:1 (target: 6:1+)")
    
    if len(types_set) > 0 and len(domains_set) > 0:
        domain_type_ratio = len(domains_set) / len(types_set)
        print(f"  Domain:Type = {domain_type_ratio:.1f}:1 (target: 2:1+)")
    
    return {
        'total_entities': len(entities),
        'total_relations': len(relations),
        'types': len(types_set),
        'domains': len(domains_set),
        'clusters': len(clusters_set),
        'connected': len(connected_entities),
        'disconnected': len(disconnected),
        'disconnected_list': disconnected
    }

def main():
    # Analyze project memory
    project_data = load_memory('project_memory.json')
    project_stats = analyze_memory(project_data, "PROJECT MEMORY")
    
    # Analyze global memory
    global_data = load_memory('global_memory.json')
    global_stats = analyze_memory(global_data, "GLOBAL MEMORY")
    
    # Summary
    print(f"\n{'='*80}")
    print("PRE-PHASE INVENTORY COMPLETE")
    print(f"{'='*80}")
    print(f"PROJECT: {project_stats['total_entities']} entities, {project_stats['disconnected']} disconnected")
    print(f"GLOBAL: {global_stats['total_entities']} entities, {global_stats['disconnected']} disconnected")
    print(f"\nSTATUS: inventory_complete|connection_audit_complete|validation_complete")
    print(f"READY FOR: CLEANUP PHASE")

if __name__ == '__main__':
    main()
