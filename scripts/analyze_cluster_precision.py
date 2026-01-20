#!/usr/bin/env python3
"""
Analyze Project Memory Cluster Distribution
Are our 20:1 ratios too aggressive? Do we lose semantic precision?
"""

import json
from pathlib import Path
from collections import defaultdict

memory_path = Path('d:/_APP/LOGReport/project_memory.json')

# Load memory
entities = []
relations = []

with open(memory_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        if data.get('type') == 'entity':
            entities.append(data)
        elif data.get('type') == 'relation':
            relations.append(data)

# Categorize
regular = [e for e in entities if not any(e['name'].startswith(p) for p in ['Project.Domain.', 'Project.Cluster.', 'Project.Type.'])]
clusters = [e for e in entities if e['name'].startswith('Project.Cluster.')]

# Build cluster membership map
cluster_members = defaultdict(list)
for rel in relations:
    if rel.get('relationType') == 'BELONGS_TO':
        from_entity = rel.get('from', '')
        to_cluster = rel.get('to', '')
        if to_cluster.startswith('Project.Cluster.') and from_entity.startswith('Project.') and not from_entity.startswith('Project.Cluster.'):
            cluster_members[to_cluster].append(from_entity)

print("=" * 80)
print("PROJECT MEMORY CLUSTER DISTRIBUTION ANALYSIS")
print("=" * 80)

print(f"\n📊 Overall Statistics:")
print(f"   Total Regular Entities: {len(regular)}")
print(f"   Total Clusters: {len(clusters)}")
print(f"   Overall Ratio: {len(regular)/len(clusters):.1f}:1")

print(f"\n🔍 Distribution by Cluster:")
print(f"   (Analyzing semantic cohesion and precision)")

# Analyze each cluster
cluster_analysis = []

for cluster_entity in sorted(clusters, key=lambda x: x['name']):
    cluster_name = cluster_entity['name']
    members = cluster_members[cluster_name]
    
    # Analyze entity types in this cluster
    entity_types = defaultdict(int)
    entity_categories = defaultdict(int)
    
    for member_name in members:
        # Get entity details
        member = next((e for e in regular if e['name'] == member_name), None)
        if member:
            entity_type = member.get('entityType', 'Unknown')
            entity_types[entity_type] += 1
            
            # Categorize by name pattern
            parts = member_name.split('.')
            if len(parts) >= 2:
                category = parts[1]  # SystemComponent, Method, Feature, etc.
                entity_categories[category] += 1
    
    diversity_score = len(entity_types)  # Higher = more diverse (less cohesive)
    
    cluster_analysis.append({
        'name': cluster_name,
        'count': len(members),
        'types': dict(entity_types),
        'categories': dict(entity_categories),
        'diversity': diversity_score
    })
    
    print(f"\n   {cluster_name.split('.')[-1]}: {len(members)} entities")
    print(f"      Entity Types ({diversity_score} unique):")
    for etype, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"         - {etype}: {count}")
    
    print(f"      Name Categories:")
    for cat, count in sorted(entity_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"         - {cat}: {count}")
    
    # Sample entities (first 5)
    if members:
        print(f"      Sample Entities:")
        for i, member in enumerate(sorted(members)[:5]):
            # Shorten name for display
            short_name = member.replace('Project.', '').replace(cluster_name.split('.')[-2] + '.', '')
            print(f"         {i+1}. {short_name[:70]}")
        if len(members) > 5:
            print(f"         ... and {len(members) - 5} more")

# Precision Analysis
print("\n" + "=" * 80)
print("PRECISION ANALYSIS")
print("=" * 80)

# Find most homogeneous clusters (good precision)
homogeneous = sorted([c for c in cluster_analysis if c['count'] > 0], key=lambda x: x['diversity'])

print(f"\n✅ Most Cohesive Clusters (low diversity = good precision):")
for i, cluster in enumerate(homogeneous[:3], 1):
    print(f"   {i}. {cluster['name'].split('.')[-1]}")
    print(f"      Entities: {cluster['count']}, Diversity: {cluster['diversity']} types")
    print(f"      Main type: {max(cluster['types'].items(), key=lambda x: x[1])[0] if cluster['types'] else 'N/A'}")

# Find most heterogeneous clusters (poor precision)
heterogeneous = sorted([c for c in cluster_analysis if c['count'] > 0], key=lambda x: x['diversity'], reverse=True)

print(f"\n⚠️  Most Heterogeneous Clusters (high diversity = potential over-consolidation):")
for i, cluster in enumerate(heterogeneous[:3], 1):
    print(f"   {i}. {cluster['name'].split('.')[-1]}")
    print(f"      Entities: {cluster['count']}, Diversity: {cluster['diversity']} types")
    print(f"      Types: {', '.join(cluster['types'].keys())}")

# Check Implementation.Code cluster specifically
impl_cluster = next((c for c in cluster_analysis if 'Implementation.Code' in c['name']), None)

if impl_cluster:
    print(f"\n🔍 Deep Dive: Implementation.Code Cluster")
    print(f"   Size: {impl_cluster['count']} entities ({impl_cluster['count']/len(regular)*100:.1f}% of all entities)")
    print(f"   Diversity: {impl_cluster['diversity']} different entity types")
    print(f"\n   Type Distribution:")
    total = impl_cluster['count']
    for etype, count in sorted(impl_cluster['types'].items(), key=lambda x: x[1], reverse=True):
        pct = count/total*100
        print(f"      {etype:25s}: {count:3d} ({pct:5.1f}%)")
    
    print(f"\n   Category Distribution:")
    for cat, count in sorted(impl_cluster['categories'].items(), key=lambda x: x[1], reverse=True):
        pct = count/total*100
        print(f"      {cat:25s}: {count:3d} ({pct:5.1f}%)")

# Recommendation
print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

# Calculate metrics
impl_size = impl_cluster['count'] if impl_cluster else 0
impl_percentage = (impl_size / len(regular) * 100) if impl_size else 0

print(f"\n📈 Current State:")
print(f"   - 20.1:1 Entity:Cluster ratio")
print(f"   - 8 total clusters")
print(f"   - Implementation.Code: {impl_size} entities ({impl_percentage:.1f}% of total)")

if impl_percentage > 60:
    print(f"\n⚠️  POTENTIAL OVER-CONSOLIDATION DETECTED")
    print(f"   - One cluster contains >60% of entities")
    print(f"   - {impl_cluster['diversity']} different entity types in same cluster")
    print(f"   - Risk: Loss of semantic granularity")
    
    # Calculate suggested split
    suggested_clusters = max(12, int(len(regular) / 6))  # For 6:1 ratio
    
    print(f"\n💡 Recommendation for 6:1 Ratio:")
    print(f"   - Target clusters: ~{suggested_clusters} (currently {len(clusters)})")
    print(f"   - Split Implementation.Code into:")
    print(f"      • Implementation.Services (SystemComponent/Service entities)")
    print(f"      • Implementation.Methods (Method entities)")
    print(f"      • Implementation.DataModels (DataModel entities)")
    print(f"      • Implementation.UI (UI-related components)")
    print(f"      • Implementation.Workflows (Workflow/Process entities)")
    print(f"   - Keep other clusters as-is (already cohesive)")
    
    print(f"\n   Expected Result:")
    print(f"   - Entity:Cluster ratio: ~{len(regular)/suggested_clusters:.1f}:1")
    print(f"   - Better semantic precision")
    print(f"   - Easier navigation and understanding")
    
elif impl_percentage > 40:
    print(f"\n✅ REASONABLE CONSOLIDATION")
    print(f"   - One cluster contains 40-60% of entities (acceptable)")
    print(f"   - But could benefit from moderate splitting")
    
    suggested_clusters = max(10, int(len(regular) / 8))
    print(f"\n💡 Optional: Consider splitting for 8:1 ratio:")
    print(f"   - Target: ~{suggested_clusters} clusters")
    print(f"   - Split Implementation.Code into 2-3 sub-clusters")
    
else:
    print(f"\n✅ GOOD CONSOLIDATION BALANCE")
    print(f"   - No single cluster dominates")
    print(f"   - Current structure is well-balanced")

print("\n" + "=" * 80)
