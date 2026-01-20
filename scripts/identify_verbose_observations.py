import json

def identify_verbose_observations(project_memory_path, max_length=80):
    with open(project_memory_path, 'r') as f:
        data = [json.loads(line) for line in f]

    condensation_opportunities = []

    for item in data:
        if item['type'] == 'entity' and item['entityType'] == 'Cluster':
            entity_name = item['name']
            for observation in item.get('observations', []):
                if len(observation) > max_length:
                    condensation_opportunities.append({
                        'entity': entity_name,
                        'observation': observation,
                        'length': len(observation)
                    })
    return condensation_opportunities

if __name__ == "__main__":
    verbose_obs = identify_verbose_observations('project_memory.json')

    print("--- Condensation Opportunities (Observations > 80 chars) ---")
    if verbose_obs:
        for op in verbose_obs:
            print(f"Entity: {op['entity']}")
            print(f"  Length: {op['length']} chars")
            print(f"  Observation: {op['observation']}\n")
    else:
        print("No verbose observations found in clusters.")