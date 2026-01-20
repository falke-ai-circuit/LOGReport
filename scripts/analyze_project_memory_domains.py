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
        print(f"Error: Could not decode JSON from {file_path}.")
        return {"entities": [], "relations": []}

def get_clusters_in_domain(domain_name, project_memory):
    """Returns a list of clusters belonging to a given domain."""
    clusters_in_domain = []
    for relation in project_memory.get('relations', []):
        if relation.get('relationType') == 'HAS_DOMAIN' and relation.get('to') == domain_name:
            clusters_in_domain.append(relation.get('from'))
    return clusters_in_domain

def check_domain_naming_compliance(domain_name):
    """
    Checks if a domain name complies with the template:
    Project.Domain.[Name]
    """
    parts = domain_name.split('.')
    if len(parts) != 3: # Expecting Project.Domain.Name
        return False, "Incorrect number of parts in name"
    if not parts == "Project" or not parts == "Domain":
        return False, "Missing 'Project.Domain' prefix"
    return True, "Compliant"

def identify_domain_condensation_opportunities(domain):
    """
    Identifies verbose observations (longer than 80 characters) in a domain.
    """
    opportunities = []
    for obs in domain.get('observations', []):
        if len(obs) > 80:
            opportunities.append(f"Observation too long ({len(obs)} chars): '{obs[:75]}...'")
    return opportunities

def detect_obsolete_domains(domain, project_memory, current_date):
    """
    Detects obsolete domains based on various criteria.
    - Empty (60 days) - simplified by checking if no clusters belong to it
    - Duplicate names - requires more advanced similarity, simplified here
    - No clusters
    - Broken connections - simplified by checking if 'HAS_TYPE' relation exists
    """
    obsolete_reasons = []

    # Check if domain has any clusters belonging to it
    clusters_in_domain = get_clusters_in_domain(domain['name'], project_memory)
    if not clusters_in_domain:
        obsolete_reasons.append("No clusters belong to this domain (empty)")

    # Check for broken connections (simplified: no 'HAS_TYPE' relation)
    has_type_connection = any(
        r['from'] == domain['name'] and r['relationType'] == 'HAS_TYPE'
        for r in project_memory.get('relations', [])
    )
    if not has_type_connection:
        obsolete_reasons.append("No explicit type connection ('HAS_TYPE' relation missing)")

    # Check for outdated timestamps (simplified: looking for 'last_modified' in observations)
    last_modified_str = next((obs.split(': ') for obs in domain.get('observations', []) if 'last_modified' in obs), None)
    if last_modified_str:
        try:
            last_modified_date = datetime.fromisoformat(last_modified_str.replace('Z', '+00:00'))
            if (current_date - last_modified_date).days > 60: # 60 days for domains
                obsolete_reasons.append("Outdated timestamp (last_modified > 60 days)")
        except ValueError:
            pass # Ignore if date format is incorrect

    return obsolete_reasons

def analyze_domain_layer(project_memory):
    """Performs a comprehensive analysis of the domain layer."""
    analysis_results = {
        "compliance_violations": [],
        "condensation_opportunities": [],
        "obsolete_candidates": [],
        "misplaced_clusters": [],
        "clusters_without_domain": [],
        "hierarchy_gaps": [],
        "domain_grouping_suggestions": [] # Placeholder for more advanced grouping
    }

    current_date = datetime.now()
    all_clusters = {e['name'] for e in project_memory.get('entities', []) if e.get('entityType') == 'Cluster'}
    clusters_with_domain = set()

    # Identify domains
    domains = [e for e in project_memory.get('entities', []) if e.get('entityType') == 'Domain']

    for domain in domains:
        domain_name = domain.get('name', 'UNKNOWN_NAME')

        # 1. Naming Compliance
        is_compliant, reason = check_domain_naming_compliance(domain_name)
        if not is_compliant:
            analysis_results["compliance_violations"].append({
                "domain": domain_name,
                "issue": "Naming Non-Compliance",
                "details": reason
            })

        # 2. Condensation Opportunities
        cond_ops = identify_domain_condensation_opportunities(domain)
        if cond_ops:
            analysis_results["condensation_opportunities"].append({
                "domain": domain_name,
                "opportunities": cond_ops
            })

        # 3. Obsolete Detection
        obsolete_reasons = detect_obsolete_domains(domain, project_memory, current_date)
        if obsolete_reasons:
            analysis_results["obsolete_candidates"].append({
                "domain": domain_name,
                "reasons": obsolete_reasons
            })

        # Track clusters belonging to domains
        clusters_in_current_domain = get_clusters_in_domain(domain_name, project_memory)
        for cluster_name in clusters_in_current_domain:
            clusters_with_domain.add(cluster_name)
        
    # 4. Clusters without a domain
    for cluster_name in all_clusters:
        if cluster_name not in clusters_with_domain:
            analysis_results["clusters_without_domain"].append({
                "cluster": cluster_name,
                "issue": "No Domain Assignment",
                "details": "This cluster does not belong to any identified domain."
            })

    return analysis_results

if __name__ == "__main__":
    project_memory_data = load_memory_data("project_memory.json")

    if project_memory_data:
        domain_analysis_report = analyze_domain_layer(project_memory_data)

        print(json.dumps(domain_analysis_report, indent=2))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        report_filename = f"logs/memory_analysis_project_domain_layer_{timestamp}.md"
        with open(report_filename, 'w') as f:
            f.write(f"# Memory Analysis Report - Project - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Phase 3 Results: Domain Layer Analysis\n\n")
            f.write(f"**Domains Analyzed**: {len([e for e in project_memory_data.get('entities', []) if e.get('entityType') == 'Domain'])}\n")
            f.write(f"**Compliance Violations**: {len(domain_analysis_report['compliance_violations'])}\n")
            f.write(f"**Condensation Opportunities**: {len(domain_analysis_report['condensation_opportunities'])}\n")
            f.write(f"**Obsolete Candidates**: {len(domain_analysis_report['obsolete_candidates'])}\n")
            f.write(f"**Misplaced Clusters**: {len(domain_analysis_report['misplaced_clusters'])}\n")
            f.write(f"**Clusters Without Domain**: {len(domain_analysis_report['clusters_without_domain'])}\n\n")

            if domain_analysis_report["compliance_violations"]:
                f.write("### Naming Compliance Violations\n")
                for item in domain_analysis_report["compliance_violations"]:
                    f.write(f"- **Domain**: {item['domain']}\n  **Issue**: {item['issue']}\n  **Details**: {item['details']}\n")
                f.write("\n")

            if domain_analysis_report["condensation_opportunities"]:
                f.write("### Condensation Opportunities\n")
                for item in domain_analysis_report["condensation_opportunities"]:
                    f.write(f"- **Domain**: {item['domain']}\n  **Opportunities**:\n")
                    for opp in item['opportunities']:
                        f.write(f"    - {opp}\n")
                f.write("\n")

            if domain_analysis_report["obsolete_candidates"]:
                f.write("### Obsolete Candidates\n")
                for item in domain_analysis_report["obsolete_candidates"]:
                    f.write(f"- **Domain**: {item['domain']}\n  **Reasons**: {', '.join(item['reasons'])}\n")
                f.write("\n")

            if domain_analysis_report["clusters_without_domain"]:
                f.write("### Clusters Without Domain Assignment\n")
                for item in domain_analysis_report["clusters_without_domain"]:
                    f.write(f"- **Cluster**: {item['cluster']}\n  **Issue**: {item['issue']}\n  **Details**: {item['details']}\n")
                f.write("\n")

        print(f"Domain analysis report saved to {report_filename}")