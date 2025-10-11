"""
Unified Codegraph Update Script
Consolidates: generation → optimization → documentation linking → validation
Similar to update_memory.py workflow pattern
"""
import json
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
import time

class CodeGraphUpdater:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.src_path = self.root / 'src'
        self.docs_path = self.root / 'docs'
        self.output_path = self.root / 'codegraph.json'
        
        self.entities = []
        self.relations = []
        self.module_count = 0
        self.class_count = 0
        
    def phase1_assess(self) -> dict:
        """Phase 1: Assess existing codegraph"""
        print("\n" + "="*60)
        print("PHASE 1/6: ASSESSMENT")
        print("="*60)
        
        if self.output_path.exists():
            entities, relations = self._load_codegraph(self.output_path)
            size_kb = self.output_path.stat().st_size / 1024
            
            print(f"Existing codegraph:")
            print(f"  Entities: {len(entities)}")
            print(f"  Relations: {len(relations)}")
            print(f"  Size: {size_kb:.2f} KB")
            
            return {
                'exists': True,
                'entities': len(entities),
                'relations': len(relations),
                'size_kb': size_kb
            }
        else:
            print("No existing codegraph found - will create new")
            return {'exists': False}
    
    def phase2_scan(self) -> dict:
        """Phase 2: Scan codebase and documentation"""
        print("\n" + "="*60)
        print("PHASE 2/6: SCANNING")
        print("="*60)
        
        # Scan Python files
        py_files = list(self.src_path.rglob('*.py'))
        print(f"Python files: {len(py_files)}")
        
        # Scan documentation
        arch_docs = list((self.docs_path / 'architecture').glob('ARCH_*.md')) if (self.docs_path / 'architecture').exists() else []
        tech_docs = list((self.docs_path / 'technical').glob('TECH_*.md')) if (self.docs_path / 'technical').exists() else []
        bp_docs = list((self.docs_path / 'blueprints').glob('BLUEPRINT_*.md')) if (self.docs_path / 'blueprints').exists() else []
        
        print(f"Documentation:")
        print(f"  Architecture: {len(arch_docs)}")
        print(f"  Technical: {len(tech_docs)}")
        print(f"  Blueprints: {len(bp_docs)}")
        
        return {
            'py_files': len(py_files),
            'arch_docs': len(arch_docs),
            'tech_docs': len(tech_docs),
            'bp_docs': len(bp_docs)
        }
    
    def phase3_plan(self) -> str:
        """Phase 3: Plan update strategy"""
        print("\n" + "="*60)
        print("PHASE 3/6: PLANNING")
        print("="*60)
        
        strategy = "full_regeneration_with_aggressive_optimization"
        print(f"Strategy: {strategy}")
        print("  1. Generate base codegraph (all entities)")
        print("  2. Aggressive optimization (keep only key entities)")
        print("  3. Add documentation pointers")
        print("  4. Validate size <100KB")
        
        return strategy
    
    def phase4_generate(self) -> dict:
        """Phase 4: Generate optimized codegraph"""
        print("\n" + "="*60)
        print("PHASE 4/6: GENERATION")
        print("="*60)
        
        # Step 1: Extract base entities
        print("Step 1: Extracting entities...")
        self._extract_entities()
        
        # Step 2: Aggressive optimization
        print("Step 2: Aggressive optimization...")
        self._optimize_aggressively()
        
        print(f"Generated:")
        print(f"  Entities: {len(self.entities)}")
        print(f"  Relations: {len(self.relations)}")
        
        return {
            'entities': len(self.entities),
            'relations': len(self.relations)
        }
    
    def phase5_integrate(self) -> dict:
        """Phase 5: Integrate documentation pointers"""
        print("\n" + "="*60)
        print("PHASE 5/6: INTEGRATION")
        print("="*60)
        
        print("Adding documentation pointers...")
        initial_count = len(self.relations)
        
        # Add documentation mappings
        self._add_documentation_pointers()
        
        doc_relations = len(self.relations) - initial_count
        print(f"  Added {doc_relations} DOCUMENTED_IN relations")
        
        return {
            'doc_relations': doc_relations,
            'total_relations': len(self.relations)
        }
    
    def phase6_validate(self) -> dict:
        """Phase 6: Validate and save"""
        print("\n" + "="*60)
        print("PHASE 6/6: VALIDATION")
        print("="*60)
        
        # Write to file
        self._write_codegraph()
        
        # Validate
        size_kb = self.output_path.stat().st_size / 1024
        
        # Test load time
        start = time.time()
        self._load_codegraph(self.output_path)
        load_ms = (time.time() - start) * 1000
        
        print(f"Validation:")
        print(f"  Size: {size_kb:.2f} KB {'✅' if size_kb <= 100 else '⚠️'}")
        print(f"  Load time: {load_ms:.0f} ms {'✅' if load_ms <= 1000 else '⚠️'}")
        print(f"  Entities: {len(self.entities)}")
        print(f"  Relations: {len(self.relations)}")
        print(f"  Modules: {self.module_count}")
        print(f"  Classes: {self.class_count}")
        
        if size_kb <= 100:
            print(f"  Space remaining: {100-size_kb:.2f} KB")
        else:
            print(f"  ⚠️  Over target by {size_kb-100:.2f} KB")
        
        return {
            'size_kb': size_kb,
            'load_ms': load_ms,
            'entities': len(self.entities),
            'relations': len(self.relations),
            'success': size_kb <= 100
        }
    
    def _extract_entities(self):
        """Extract entities from source code"""
        # Create hierarchy root
        self.entities.append({
            'type': 'entity',
            'name': 'Code.Type.Codebase',
            'entityType': 'Type',
            'observations': ['LOGReport application root: log analysis and reporting system', 'upd:2025-10-11,refs:0']
        })
        
        # Scan domains
        domains = self._scan_domains()
        for domain in domains:
            domain_desc = self._get_domain_description(domain)
            self.entities.append({
                'type': 'entity',
                'name': f'Code.Domain.{domain}',
                'entityType': 'Domain',
                'observations': [domain_desc, 'upd:2025-10-11,refs:0']
            })
            
            self.relations.append({
                'type': 'relation',
                'from': f'Code.Domain.{domain}',
                'to': 'Code.Type.Codebase',
                'relationType': 'BELONGS_TO'
            })
        
        # Create clusters
        self._create_clusters()
        
        # Scan modules and classes
        self._scan_modules_and_classes()
    
    def _get_domain_description(self, domain: str) -> str:
        """Get descriptive text for domain"""
        descriptions = {
            'Commander': 'Command system: node management, UI coordination, user actions',
            'Frontend': 'GUI layer: main windows, user interface, visual components',
            'Core': 'Core logic: file processing, token detection, data handling',
            'Services': 'Service layer: background processing, external integrations',
        }
        return descriptions.get(domain, f'{domain} domain')
    
    def _scan_domains(self) -> List[str]:
        """Identify domains from folder structure"""
        domains = set()
        
        for py_file in self.src_path.rglob('*.py'):
            rel_path = py_file.relative_to(self.src_path)
            parts = rel_path.parts
            
            if len(parts) > 1:
                # Determine domain from folder structure
                folder = parts[0]
                if 'commander' in folder:
                    domains.add('Commander')
                elif 'gui' in folder or 'views' in folder:
                    domains.add('Frontend')
                elif 'services' in folder or 'workers' in folder:
                    domains.add('Services')
                else:
                    domains.add('Core')
            else:
                domains.add('Core')
        
        return sorted(domains)
    
    def _create_clusters(self):
        """Create intermediate cluster entities for better organization"""
        # Define clusters based on architecture
        cluster_definitions = {
            'Commander': {
                'Services': 'Command services: context menu, bstool, error reporting',
                'Views': 'UI views: node tree, dialogs, widgets',
                'Presenters': 'Presenters: mediates between models and views',
                'Models': 'Data models: node configuration, state management',
            },
            'Core': {
                'FileIO': 'File I/O: log loading, token detection, file processing',
                'Processing': 'Data processing: log parsing, report generation',
                'Configuration': 'Configuration: settings, constants, contracts',
            },
            'Frontend': {
                'MainUI': 'Main GUI: windows, tabs, primary interface',
                'Dialogs': 'Dialog windows: configuration, settings',
                'Workers': 'Background workers: async processing, threading',
            },
        }
        
        for domain, clusters in cluster_definitions.items():
            for cluster_name, description in clusters.items():
                cluster_entity = f'Code.Cluster.{domain}.{cluster_name}'
                
                self.entities.append({
                    'type': 'entity',
                    'name': cluster_entity,
                    'entityType': 'Cluster',
                    'observations': [description, 'upd:2025-10-11,refs:0']
                })
                
                # Link cluster to domain
                self.relations.append({
                    'type': 'relation',
                    'from': cluster_entity,
                    'to': f'Code.Domain.{domain}',
                    'relationType': 'BELONGS_TO'
                })
    
    def _scan_modules_and_classes(self):
        """Scan modules and extract key classes"""
        key_classes = [
            'LogReportGUI', 'MainWindow', 'CommanderMainWindow',
            'ContextMenuService', 'BsToolCommandService', 'NodeTreeView',
            'NodeTreePresenter', 'SystemFileLoader', 'TokenDetector'
        ]
        
        for py_file in self.src_path.rglob('*.py'):
            if py_file.stem == '__init__':
                continue
            
            # Create module entity
            rel_path = py_file.relative_to(self.src_path)
            module_name = str(rel_path).replace('\\', '_').replace('/', '_').replace('.py', '')
            
            # Extract functional description
            description = self._extract_module_description(py_file)
            
            entity_name = f'Code.Module.{module_name}.File'
            obs = [description if description else f'{py_file.stem}', 'upd:2025-10-11,refs:0']
            
            self.entities.append({
                'type': 'entity',
                'name': entity_name,
                'entityType': 'Module',
                'observations': obs
            })
            self.module_count += 1
            
            # Determine domain and cluster
            domain = self._get_domain_for_file(py_file)
            cluster = self._get_cluster_for_file(py_file, domain)
            
            # Link to cluster if exists, otherwise to domain
            if cluster:
                parent = f'Code.Cluster.{domain}.{cluster}'
            else:
                parent = f'Code.Domain.{domain}'
            
            self.relations.append({
                'type': 'relation',
                'from': entity_name,
                'to': parent,
                'relationType': 'BELONGS_TO'
            })
            
            # Extract key classes only
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if node.name in key_classes:
                            class_entity = f'Code.Class.{module_name}.{node.name}'
                            
                            # Extract class description
                            class_desc = self._extract_class_description(node)
                            
                            self.entities.append({
                                'type': 'entity',
                                'name': class_entity,
                                'entityType': 'Class',
                                'observations': [class_desc if class_desc else node.name, 'upd:2025-10-11,refs:0']
                            })
                            self.class_count += 1
                            
                            # Link class to module
                            self.relations.append({
                                'type': 'relation',
                                'from': class_entity,
                                'to': entity_name,
                                'relationType': 'BELONGS_TO'
                            })
                            
                            # Check for inheritance
                            if node.bases:
                                for base in node.bases:
                                    if isinstance(base, ast.Name):
                                        # Simple inheritance
                                        pass  # Can add INHERITS relation if needed
            
            except Exception as e:
                print(f"  Warning: Could not parse {py_file}: {e}")
    
    def _get_cluster_for_file(self, file_path: Path, domain: str) -> str:
        """Determine cluster from file path and domain"""
        rel_path = file_path.relative_to(self.src_path)
        path_str = str(rel_path).lower()
        
        if domain == 'Commander':
            if 'service' in path_str:
                return 'Services'
            elif 'view' in path_str:
                return 'Views'
            elif 'presenter' in path_str:
                return 'Presenters'
            elif 'node' in path_str or 'config' in path_str:
                return 'Models'
        
        elif domain == 'Core':
            if 'loader' in path_str or 'sys_file' in path_str or 'token' in path_str:
                return 'FileIO'
            elif 'processor' in path_str or 'generator' in path_str or 'creator' in path_str:
                return 'Processing'
            elif 'config' in path_str or 'const' in path_str or 'contract' in path_str:
                return 'Configuration'
        
        elif domain == 'Frontend':
            if 'worker' in path_str:
                return 'Workers'
            elif 'dialog' in path_str:
                return 'Dialogs'
            else:
                return 'MainUI'
        
        return None  # Link directly to domain if no cluster match
    
    def _get_domain_for_file(self, file_path: Path) -> str:
        """Determine domain from file path"""
        rel_path = file_path.relative_to(self.src_path)
        path_str = str(rel_path).lower()
        
        if 'commander' in path_str:
            return 'Commander'
        elif 'gui' in path_str or 'view' in path_str:
            return 'Frontend'
        elif 'service' in path_str or 'worker' in path_str:
            return 'Services'
        else:
            return 'Core'
    
    def _extract_module_description(self, file_path: Path) -> str:
        """Extract functional description from module docstring or comments"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
                # Try module docstring
                docstring = ast.get_docstring(tree)
                if docstring:
                    first_line = docstring.split('\n')[0].strip()
                    return first_line[:80]
                
                # Try first meaningful comment
                lines = content.split('\n')
                for line in lines[:10]:
                    line = line.strip()
                    if line.startswith('#') and not line.startswith('#!'):
                        comment = line.lstrip('#').strip()
                        if len(comment) > 10:
                            return comment[:80]
        except:
            pass
        
        # Fallback: use filename with context
        return f"Module: {file_path.stem}"
    
    def _extract_class_description(self, node: ast.ClassDef) -> str:
        """Extract functional description from class docstring"""
        try:
            docstring = ast.get_docstring(node)
            if docstring:
                first_line = docstring.split('\n')[0].strip()
                return first_line[:80]
        except:
            pass
        
        # Fallback: describe based on name pattern
        class_name = node.name
        if 'Service' in class_name:
            return f"Service: {class_name.replace('Service', '')} operations and coordination"[:80]
        elif 'View' in class_name:
            return f"View: UI component for {class_name.replace('View', '')} display"[:80]
        elif 'Presenter' in class_name:
            return f"Presenter: mediates between {class_name.replace('Presenter', '')} model and view"[:80]
        elif 'Worker' in class_name:
            return f"Worker: async background processing for {class_name.replace('Worker', '')}"[:80]
        elif 'Manager' in class_name:
            return f"Manager: coordinates and manages {class_name.replace('Manager', '')} operations"[:80]
        elif 'Dialog' in class_name:
            return f"Dialog: UI dialog for {class_name.replace('Dialog', '')} configuration"[:80]
        elif 'Window' in class_name:
            return f"Window: main window for {class_name.replace('Window', '')} interface"[:80]
        
        return f"Class: {class_name}"
    
    def _optimize_aggressively(self):
        """Aggressive optimization to meet <100KB target"""
        # Truncate observations but preserve functional descriptions
        for entity in self.entities:
            obs = entity['observations']
            new_obs = []
            
            # Keep first observation (functional description) up to 60 chars
            if obs:
                first_obs = obs[0]
                if not first_obs.startswith('upd:') and not first_obs.startswith('doc:') and '/' not in first_obs:
                    new_obs.append(first_obs[:60] if len(first_obs) > 60 else first_obs)
                else:
                    new_obs.append(first_obs)
            
            # Keep doc references
            for o in obs[1:]:
                if o.startswith('doc:'):
                    new_obs.append(o)
            
            # Keep metadata (always last)
            for o in obs:
                if o.startswith('upd:'):
                    new_obs.append(o)
                    break
            
            entity['observations'] = new_obs
    
    def _add_documentation_pointers(self):
        """Add DOCUMENTED_IN relations and doc entities"""
        doc_mappings = [
            # Architecture -> Domains
            ('Code.Domain.Commander', 'docs/architecture/ARCH_command_system.md', 'Command arch'),
            ('Code.Domain.Core', 'docs/architecture/ARCH_memory_system.md', 'Memory arch'),
            
            # Technical -> Key modules
            ('Code.Module.commander_main_window.File', 'docs/technical/TECH_commander_window.md', 'Commander window'),
            ('Code.Module.sys_file_loader.File', 'docs/technical/TECH_token_management.md', 'Token mgmt'),
            
            # Blueprints -> Classes
            ('Code.Class.commander_services_context_menu_service.ContextMenuService', 
             'docs/blueprints/BLUEPRINT_context_menu.md', 'Context menu spec'),
            
            # Navigation guide
            ('Code.Type.Codebase', 'docs/technical/TECH_codegraph_navigation.md', 'Codegraph guide'),
            ('Code.Type.Codebase', 'docs/technical/TECH_documentation_pointers.md', 'Doc pointers'),
        ]
        
        # Create doc entities
        doc_entities_set = set()
        for code_entity, doc_path, description in doc_mappings:
            doc_name = f'Doc:{doc_path}'
            
            # Add doc entity (once)
            if doc_name not in doc_entities_set:
                doc_entities_set.add(doc_name)
                folder = '/'.join(doc_path.split('/')[:-1]) + '/'
                self.entities.append({
                    'type': 'entity',
                    'name': doc_name,
                    'entityType': 'Documentation',
                    'observations': [description[:18], folder, 'upd:2025-10-11,refs:0']
                })
            
            # Add DOCUMENTED_IN relation
            self.relations.append({
                'type': 'relation',
                'from': code_entity,
                'to': doc_name,
                'relationType': 'DOCUMENTED_IN'
            })
            
            # Update entity observation with doc reference
            for entity in self.entities:
                if entity['name'] == code_entity:
                    doc_filename = doc_path.split('/')[-1]
                    doc_ref = f'doc:{doc_filename}'[:18]
                    # Insert before metadata
                    if doc_ref not in entity['observations']:
                        entity['observations'].insert(-1, doc_ref)
                    break
    
    def _write_codegraph(self):
        """Write codegraph to file"""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for entity in self.entities:
                f.write(json.dumps(entity, separators=(',', ':')) + '\n')
            for relation in self.relations:
                f.write(json.dumps(relation, separators=(',', ':')) + '\n')
    
    def _load_codegraph(self, path: Path) -> Tuple[List[dict], List[dict]]:
        """Load codegraph from file"""
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
    
    def run(self):
        """Execute full 6-phase workflow"""
        print("\n" + "="*60)
        print("CODEGRAPH UPDATE WORKFLOW")
        print("="*60)
        
        start_time = time.time()
        
        # Phase 1: Assessment
        assess_result = self.phase1_assess()
        
        # Phase 2: Scanning
        scan_result = self.phase2_scan()
        
        # Phase 3: Planning
        strategy = self.phase3_plan()
        
        # Phase 4: Generation
        gen_result = self.phase4_generate()
        
        # Phase 5: Integration
        int_result = self.phase5_integrate()
        
        # Phase 6: Validation
        val_result = self.phase6_validate()
        
        elapsed = time.time() - start_time
        
        # Summary
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Output: {self.output_path}")
        print(f"Status: {'SUCCESS ✅' if val_result['success'] else 'REVIEW NEEDED ⚠️'}")
        print("="*60)

def main():
    """Entry point"""
    root_path = 'd:/_APP/LOGReport'
    
    updater = CodeGraphUpdater(root_path)
    updater.run()

if __name__ == '__main__':
    main()
