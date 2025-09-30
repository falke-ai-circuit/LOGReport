import json
import re
from datetime import datetime, timedelta

def load_project_memory(file_path="project_memory.json"):
    """Loads project memory from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return {"entities": [], "relations": []}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
        return {"entities": [], "relations": []}

def check_template_compliance(entity_name):
    """
    Checks if an entity name complies with the template:
    [MemoryType].[Domain].[SubCluster].[EntityType]_[Name]
    """
    parts = entity_name.split('.')
    if len(parts) < 2: # Minimum Project.Name or Project.EntityType_Name
        return False, "Too few parts in name"

    # Check for Project prefix
    if not parts.startswith("Project"):
        return False, "Missing 'Project' prefix"

    # Check for EntityType_Name suffix pattern
    if '_' not in parts[-1]:
        return False, "Missing EntityType_Name suffix pattern"

    # Further checks for 4-layer hierarchy (MemoryType.Domain.SubCluster.EntityType_Name)
    # This is a more complex check, focusing on the structure after 'Project'
    if len(parts) < 4: # Project.Domain.EntityType_Name (missing SubCluster) or Project.EntityType_Name (missing Domain, SubCluster)
        return False, "Incomplete 4-layer hierarchy (missing Domain or SubCluster)"

    return True, "Compliant"

def identify_condensation_opportunities(entity):
    """
    Identifies verbose observations (longer than 80 characters) in an entity.
    """
    opportunities = []
    for obs in entity.get('observations', []):
        if len(obs) > 80:
            opportunities.append(f"Observation too long ({len(obs)} chars): '{obs[:75]}...'")
    return opportunities

def validate_metadata(entity):
    """
    Validates the presence of mandatory metadata fields.
    """
    missing_metadata = []
    mandatory_fields = [
        'created_date', 'last_modified', 'last_accessed', 'reference_count',
        'usage_count', 'hierarchy_path', 'content_hash', 'obsolete_check_date'
    ]
    for field in mandatory_fields:
        # Check if the field exists in any observation or as a direct attribute
        if not any(field in obs for obs in entity.get('observations', [])) and field not in entity:
            missing_metadata.append(field)
    return missing_metadata

def detect_obsolete_entities(entity, project_relations, current_date, global_entities):
    """
    Detects obsolete entities based on various criteria.
    - No references (90+ days)
    - Duplicate (>80% similarity) - requires more advanced text similarity, simplified here
    - Outdated timestamps (180 days)
    - Zero usage (30 days)
    - Promoted to global memory
    """
    obsolete_reasons = []

    # Check for promotion to global memory
    if any(rel.get('to') == entity['name'] and rel.get('relationType') == 'PROMOTED_TO' for rel in project_relations):
        obsolete_reasons.append("Promoted to global memory (check for redundancy)")
    
    # Check if entity exists in global memory (as a direct name match or similar concept)
    # This is a simplified check; a real implementation would use semantic similarity
    global_entity_names = {ge['name'] for ge in global_entities}
    if entity['name'].replace('Project.', 'Global.') in global_entity_names:
        obsolete_reasons.append("Similar entity exists in global memory (potential redundancy)")

    # Check for outdated timestamps (simplified: looking for 'last_modified' in observations)
    last_modified_str = next((obs.split(': ') for obs in entity.get('observations', []) if 'last_modified' in obs), None)
    if last_modified_str:
        try:
            last_modified_date = datetime.fromisoformat(last_modified_str.replace('Z', '+00:00'))
            if (current_date - last_modified_date).days > 180:
                obsolete_reasons.append("Outdated timestamp (last_modified > 180 days)")
        except ValueError:
            pass # Ignore if date format is incorrect

    # Check for zero usage (simplified: looking for 'usage_count: 0' in observations)
    if any('usage_count: 0' in obs for obs in entity.get('observations', [])):
        obsolete_reasons.append("Zero usage (usage_count: 0 in observations)")

    # Check for no references (simplified: no relations where this entity is 'from' or 'to')
    has_references = any(r['from'] == entity['name'] or r['to'] == entity['name'] for r in project_relations)
    if not has_references:
        obsolete_reasons.append("No explicit references in project relations")


    return obsolete_reasons

def analyze_entity_layer(project_memory, global_memory):
    """Performs a comprehensive analysis of the entity layer."""
    analysis_results = {
        "compliance_violations": [],
        "condensation_opportunities": [],
        "metadata_issues": [],
        "obsolete_candidates": [],
        "entity_grouping_suggestions": [] # Placeholder for more advanced grouping
    }
    
    current_date = datetime.now()
    global_entities = global_memory.get('entities', [])

    for entity in project_memory.get('entities', []):
        entity_name = entity.get('name', 'UNKNOWN_NAME')

        # 1. Template Compliance
        is_compliant, reason = check_template_compliance(entity_name)
        if not is_compliant:
            analysis_results["compliance_violations"].append({
                "entity": entity_name,
                "issue": "Template Non-Compliance",
                "details": reason
            })

        # 2. Condensation Opportunities
        cond_ops = identify_condensation_opportunities(entity)
        if cond_ops:
            analysis_results["condensation_opportunities"].append({
                "entity": entity_name,
                "opportunities": cond_ops
            })

        # 3. Metadata Validation
        missing_meta = validate_metadata(entity)
        if missing_meta:
            analysis_results["metadata_issues"].append({
                "entity": entity_name,
                "missing_fields": missing_meta
            })

        # 4. Obsolete Detection
        obsolete_reasons = detect_obsolete_entities(entity, project_memory.get('relations', []), current_date, global_entities)
        if obsolete_reasons:
            analysis_results["obsolete_candidates"].append({
                "entity": entity_name,
                "reasons": obsolete_reasons
            })
            
    return analysis_results

if __name__ == "__main__":
    project_memory_data = load_project_memory("project_memory.json")
    global_memory_data = load_project_memory("global_memory.json") # Assuming global_memory.json exists

    if project_memory_data and global_memory_data:
        entity_analysis_report = analyze_entity_layer(project_memory_data, global_memory_data)

        # Output the results in a structured format
        print(json.dumps(entity_analysis_report, indent=2))

        # Example of how to save to a file (as per deliverable)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_filename = f"logs/memory_analysis_project_{timestamp}.md"
        with open(report_filename, 'w') as f:
            f.write(f"# Memory Analysis Report - Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Phase 1 Results: Entity Layer Analysis\n\n")
            f.write(f"**Entities Analyzed**: {len(project_memory_data.get('entities', []))}\n")
            f.write(f"**Compliance Violations**: {len(entity_analysis_report['compliance_violations'])}\n")
            f.write(f"**Condensation Opportunities**: {len(entity_analysis_report['condensation_opportunities'])}\n")
            f.write(f"**Metadata Issues**: {len(entity_analysis_report['metadata_issues'])}\n")
            f.write(f"**Obsolete Candidates**: {len(entity_analysis_report['obsolete_candidates'])}\n\n")

            if entity_analysis_report["compliance_violations"]:
                f.write("### Compliance Violations\n")
                for item in entity_analysis_report["compliance_violations"]:
                    f.write(f"- **Entity**: {item['entity']}\n  **Issue**: {item['issue']}\n  **Details**: {item['details']}\n")
                f.write("\n")

            if entity_analysis_report["condensation_opportunities"]:
                f.write("### Condensation Opportunities\n")
                for item in entity_analysis_report["condensation_opportunities"]:
                    f.write(f"- **Entity**: {item['entity']}\n  **Opportunities**:\n")
                    for opp in item['opportunities']:
                        f.write(f"    - {opp}\n")
                f.write("\n")

            if entity_analysis_report["metadata_issues"]:
                f.write("### Metadata Issues\n")
                for item in entity_analysis_report["metadata_issues"]:
                    f.write(f"- **Entity**: {item['entity']}\n  **Missing Fields**: {', '.join(item['missing_fields'])}\n")
                f.write("\n")

            if entity_analysis_report["obsolete_candidates"]:
                f.write("### Obsolete Candidates\n")
                for item in entity_analysis_report["obsolete_candidates"]:
                    f.write(f"- **Entity**: {item['entity']}\n  **Reasons**: {', '.join(item['reasons'])}\n")
                f.write("\n")

        print(f"Analysis report saved to {report_filename}")