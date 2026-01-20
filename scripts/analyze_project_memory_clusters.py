import json
import re
from datetime import datetime, timedelta

def load_memory_data(file_path):
    """Loads memory data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return {"entities": [], "relations": []}
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path} as a single object. Attempting line-by-line parsing.")
        data = {"entities": [], "relations": []}
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    entity = json.loads(line.strip())
                    if "type" in entity and entity["type"] == "entity":
                        data["entities"].append(entity)
                    elif "type" in entity and entity["type"] == "relation":
                        data["relations"].append(entity)
                    else:
                        # If it's not an entity or relation, try to append it to entities as a fallback
                        data["entities"].append(entity)
                except json.JSONDecodeError:
                    print(f"Skipping malformed line: {line.strip()}")
        return data

def get_entities_in_cluster(cluster_name, project_memory):
    """Returns a list of entities belonging to a given cluster."""
    entities_in_cluster = []
    for relation in project_memory.get('relations', []):
        if relation.get('relationType') == 'belongs_to' and relation.get('to') == cluster_name:
            entities_in_cluster.append(relation.get('from'))
    return entities_in_cluster

def check_cluster_naming_compliance(cluster_name):
    """
    Checks if a cluster name complies with the template:
    Project.Cluster.[Domain].[SubCluster]_Cluster
    """
    parts = cluster_name.split('.')
    if len(parts) < 3: # Minimum Project.Cluster.Name_Cluster
        return False, "Too few parts in name"
    if not (len(parts) >= 2 and parts == "Project" and parts == "Cluster"):
        return False, "Missing 'Project.Cluster' prefix or incorrect hierarchy"
    if not parts[-1].endswith("_Cluster"):
        return False, "Missing '_Cluster' suffix"
    return True, "Compliant"

def identify_cluster_condensation_opportunities(cluster):
    """
    Identifies verbose observations (longer than 80 characters) in a cluster.
    """
    opportunities = []
    for obs in cluster.get('observations', []):
        if len(obs) > 80:
            opportunities.append(f"Observation too long ({len(obs)} chars): '{obs[:75]}...'")
    return opportunities

def detect_obsolete_clusters(cluster, project_memory, current_date):
    """
    Detects obsolete clusters based on various criteria.
    - Empty (30 days) - simplified by checking if no entities belong to it
    - Duplicate names - requires more advanced similarity, simplified here
    - No entities
    - Broken connections - simplified by checking if 'belongs_to_domain' relation exists
    """
    obsolete_reasons = []

    # Check if cluster has any entities belonging to it
    entities_in_cluster = get_entities_in_cluster(cluster['name'], project_memory)
    if not entities_in_cluster:
        obsolete_reasons.append("No entities belong to this cluster (empty)")

    # Check for broken connections (simplified: no 'BELONGS_TO_DOMAIN' relation)
    has_domain_connection = any(
        r['from'] == cluster['name'] and r['relationType'] == 'HAS_DOMAIN'
        for r in project_memory.get('relations', [])
    )
    if not has_domain_connection:
        obsolete_reasons.append("No explicit domain connection ('HAS_DOMAIN' relation missing)")

    # Check for outdated timestamps (simplified: looking for 'last_modified' in observations)
    last_modified_str = next((obs.split(': ') for obs in cluster.get('observations', []) if 'last_modified' in obs), None)
    if last_modified_str:
        try:
            last_modified_date = datetime.fromisoformat(last_modified_str.replace('Z', '+00:00'))
            if (current_date - last_modified_date).days > 30: # 30 days for clusters
                obsolete_reasons.append("Outdated timestamp (last_modified > 30 days)")
        except ValueError:
            pass # Ignore if date format is incorrect

    return obsolete_reasons

def analyze_cluster_layer(project_memory):
    """Performs a comprehensive analysis of the cluster layer."""
    analysis_results = {
        "compliance_violations": [],
        "condensation_opportunities": [],
        "obsolete_candidates": [],
        "misplaced_entities": [],
        "overcrowded_clusters": [],
        "entities_without_cluster": [],
        "hierarchy_gaps": [],
        "cluster_grouping_suggestions": [] # Placeholder for more advanced grouping
    }

    current_date = datetime.now()
    all_entities = {e['name'] for e in project_memory.get('entities', [])}
    entities_with_cluster = set()

    # Identify clusters
    clusters = [e for e in project_memory.get('entities', []) if e.get('entityType') == 'Cluster']

    for cluster in clusters:
        cluster_name = cluster.get('name', 'UNKNOWN_NAME')

        # 1. Naming Compliance
        is_compliant, reason = check_cluster_naming_compliance(cluster_name)
        if not is_compliant:
            analysis_results["compliance_violations"].append({
                "cluster": cluster_name,
                "issue": "Naming Non-Compliance",
                "details": reason
            })

        # 2. Condensation Opportunities
        cond_ops = identify_cluster_condensation_opportunities(cluster)
        if cond_ops:
            analysis_results["condensation_opportunities"].append({
                "cluster": cluster_name,
                "opportunities": cond_ops
            })

        # 3. Obsolete Detection
        obsolete_reasons = detect_obsolete_clusters(cluster, project_memory, current_date)
        if obsolete_reasons:
            analysis_results["obsolete_candidates"].append({
                "cluster": cluster_name,
                "reasons": obsolete_reasons
            })

        # Track entities belonging to clusters
        entities_in_current_cluster = get_entities_in_cluster(cluster_name, project_memory)
        for entity_name in entities_in_current_cluster:
            entities_with_cluster.add(entity_name)
        
        # Check for overcrowded clusters (arbitrary threshold for now)
        if len(entities_in_current_cluster) > 10:
            analysis_results["overcrowded_clusters"].append({
                "cluster": cluster_name,
                "entity_count": len(entities_in_current_cluster),
                "details": "Consider splitting this cluster for better organization."
            })

    # 4. Entities without a cluster
    for entity_name in all_entities:
        # Exclude clusters themselves and other non-standard entities from this check
        if not entity_name.startswith("Project.Cluster.") and entity_name not in entities_with_cluster:
            # Ensure it's not a domain or memory type entity itself
            entity_obj = next((e for e in project_memory['entities'] if e['name'] == entity_name), None)
            if entity_obj and entity_obj.get('entityType') not in ['Domain', 'MemoryType', 'Cluster']:
                analysis_results["entities_without_cluster"].append({
                    "entity": entity_name,
                    "issue": "No Cluster Assignment",
                    "details": "This entity does not belong to any identified cluster."
                })

    # 5. Hierarchy Gaps (e.g., cluster not connected to a domain)
    # This is partially covered by obsolete detection (broken connections)
    # A more thorough check would involve validating the full path from entity to type

    return analysis_results

if __name__ == "__main__":
    project_memory_data = load_memory_data("project_memory.json")

    if project_memory_data:
        cluster_analysis_report = analyze_cluster_layer(project_memory_data)

        print(json.dumps(cluster_analysis_report, indent=2))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_filename = f"logs/memory_analysis_project_cluster_layer_{timestamp}.md"
        with open(report_filename, 'w') as f:
            f.write(f"# Memory Analysis Report - Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Phase 2 Results: Cluster Layer Analysis\n\n")
            f.write(f"**Clusters Analyzed**: {len([e for e in project_memory_data.get('entities', []) if e.get('entityType') == 'Cluster'])}\n")
            f.write(f"**Compliance Violations**: {len(cluster_analysis_report['compliance_violations'])}\n")
            f.write(f"**Condensation Opportunities**: {len(cluster_analysis_report['condensation_opportunities'])}\n")
            f.write(f"**Obsolete Candidates**: {len(cluster_analysis_report['obsolete_candidates'])}\n")
            f.write(f"**Misplaced Entities**: {len(cluster_analysis_report['misplaced_entities'])}\n")
            f.write(f"**Overcrowded Clusters**: {len(cluster_analysis_report['overcrowded_clusters'])}\n")
            f.write(f"**Entities Without Cluster**: {len(cluster_analysis_report['entities_without_cluster'])}\n\n")

            if cluster_analysis_report["compliance_violations"]:
                f.write("### Naming Compliance Violations\n")
                for item in cluster_analysis_report["compliance_violations"]:
                    f.write(f"- **Cluster**: {item['cluster']}\n  **Issue**: {item['issue']}\n  **Details**: {item['details']}\n")
                f.write("\n")

            if cluster_analysis_report["condensation_opportunities"]:
                f.write("### Condensation Opportunities\n")
                for item in cluster_analysis_report["condensation_opportunities"]:
                    f.write(f"- **Cluster**: {item['cluster']}\n  **Opportunities**:\n")
                    for opp in item['opportunities']:
                        f.write(f"    - {opp}\n")
                f.write("\n")

            if cluster_analysis_report["obsolete_candidates"]:
                f.write("### Obsolete Candidates\n")
                for item in cluster_analysis_report["obsolete_candidates"]:
                    f.write(f"- **Cluster**: {item['cluster']}\n  **Reasons**: {', '.join(item['reasons'])}\n")
                f.write("\n")

            if cluster_analysis_report["overcrowded_clusters"]:
                f.write("### Overcrowded Clusters\n")
                for item in cluster_analysis_report["overcrowded_clusters"]:
                    f.write(f"- **Cluster**: {item['cluster']}\n  **Entity Count**: {item['entity_count']}\n  **Details**: {item['details']}\n")
                f.write("\n")

            if cluster_analysis_report["entities_without_cluster"]:
                f.write("### Entities Without Cluster Assignment\n")
                for item in cluster_analysis_report["entities_without_cluster"]:
                    f.write(f"- **Entity**: {item['entity']}\n  **Issue**: {item['issue']}\n  **Details**: {item['details']}\n")
                f.write("\n")

        print(f"Cluster analysis report saved to {report_filename}")