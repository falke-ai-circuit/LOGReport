"""
Simplified Codegraph Update Script - 4-Layer Hierarchy
Type → Domain → Module → Class (No clusters)
Filters generic observations, removes .File suffix
"""
import json
import ast
from pathlib import Path
from datetime import datetime
import time


class SimpleCodeGraphUpdater:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.src_dir = self.root / 'src'
        self.docs_dir = self.root / 'docs'
        self.output_path = self.root / 'codegraph.json'
        
        self.entities = []
        self.relations = []
        self.module_count = 0
        self.class_count = 0
    
    def run(self):
        """Execute complete workflow"""
        start_time = time.time()
        
        print("=" * 60)
        print("CODEGRAPH UPDATE WORKFLOW - SIMPLIFIED")
        print("="*60)
        
        # Phase 1: Assess
        self.phase1_assess()
        
        # Phase 2: Scan
        self.phase2_scan()
        
        # Phase 3: Plan
        self.phase3_plan()
        
        # Phase 4: Generate
        self.phase4_generate()
        
        # Phase 5: Integrate docs
        self.phase5_integrate()
        
        # Phase 6: Validate
        result = self.phase6_validate()
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Time elapsed: {elapsed:.1f}s")
        print(f"Output: {self.output_path}")
        print(f"Status: {'SUCCESS [OK]' if result['success'] else 'FAILED [!]'}")
        print("="*60)
    
    def phase1_assess(self):
        """Phase 1: Assess existing codegraph"""
        print("\n" + "="*60)
        print("PHASE 1/6: ASSESSMENT")
        print("="*60)
        
        if self.output_path.exists():
            with open(self.output_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            entities = []
            relations = []
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    if '"type":"entity"' in line:
                        entities.append(json.loads(line))
                    elif '"type":"relation"' in line:
                        relations.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON at line {i}: {e}")
                    continue
            
            size_kb = self.output_path.stat().st_size / 1024
            
            print(f"Existing codegraph:")
            print(f"  Entities: {len(entities)}")
            print(f"  Relations: {len(relations)}")
            print(f"  Size: {size_kb:.2f} KB")
        else:
            print("No existing codegraph - will create new")
    
    def phase2_scan(self):
        """Phase 2: Scan codebase"""
        print("\n" + "="*60)
        print("PHASE 2/6: SCANNING")
        print("="*60)
        
        py_files = list(self.src_dir.rglob('*.py'))
        print(f"Python files: {len(py_files)}")
        
        arch_docs = list((self.docs_dir / 'architecture').glob('ARCH_*.md')) if (self.docs_dir / 'architecture').exists() else []
        tech_docs = list((self.docs_dir / 'technical').glob('TECH_*.md')) if (self.docs_dir / 'technical').exists() else []
        bp_docs = list((self.docs_dir / 'blueprints').glob('BLUEPRINT_*.md')) if (self.docs_dir / 'blueprints').exists() else []
        
        print(f"Documentation:")
        print(f"  Architecture: {len(arch_docs)}")
        print(f"  Technical: {len(tech_docs)}")
        print(f"  Blueprints: {len(bp_docs)}")
    
    def phase3_plan(self):
        """Phase 3: Plan strategy"""
        print("\n" + "="*60)
        print("PHASE 3/6: PLANNING")
        print("="*60)
        
        print("Strategy: simplified_4_layer_hierarchy")
        print("  1. Type -> Domain -> Module -> Class (no clusters)")
        print("  2. Filter generic observations")
        print("  3. Remove .File suffix")
        print("  4. Keep functional descriptions only")
    
    def phase4_generate(self):
        """Phase 4: Generate entities"""
        print("\n" + "="*60)
        print("PHASE 4/6: GENERATION")
        print("="*60)
        
        print("Extracting entities...")
        
        # 1. Type entity
        self.entities.append({
            'type': 'entity',
            'name': 'Code.Type.Codebase',
            'entityType': 'Type',
            'observations': [
                'LOGReport application root: log analysis and reporting system',
                f'upd:{datetime.now().strftime("%Y-%m-%d")},refs:0'
            ]
        })
        
        # 2. Domain entities
        domains = self._get_domains()
        for domain in domains:
            domain_desc = self._get_domain_description(domain)
            self.entities.append({
                'type': 'entity',
                'name': f'Code.Domain.{domain}',
                'entityType': 'Domain',
                'observations': [
                    domain_desc,
                    f'upd:{datetime.now().strftime("%Y-%m-%d")},refs:0'
                ]
            })
            
            self.relations.append({
                'type': 'relation',
                'from': f'Code.Domain.{domain}',
                'to': 'Code.Type.Codebase',
                'relationType': 'BELONGS_TO'
            })
        
        # 3. Modules and Classes
        self._scan_modules_and_classes()
        
        # 4. Module dependencies (IMPORTS relations)
        self._create_import_relations()
        
        print(f"Generated:")
        print(f"  Entities: {len(self.entities)}")
        print(f"  Relations: {len(self.relations)}")
    
    def phase5_integrate(self):
        """Phase 5: Add documentation pointers"""
        print("\n" + "="*60)
        print("PHASE 5/6: INTEGRATION")
        print("="*60)
        
        print("Adding documentation pointers...")
        initial_relations = len(self.relations)
        
        # Add doc entities and DOCUMENTED_IN relations
        doc_mappings = [
            ('Code.Type.Codebase', 'docs/technical/TECH_codegraph.md'),
            ('Code.Domain.Commander', 'docs/architecture/ARCH_command_system.md'),
            ('Code.Domain.Core', 'docs/architecture/ARCH_memory_system.md'),
        ]
        
        for entity_name, doc_path in doc_mappings:
            doc_entity_name = f'Doc:{doc_path}'
            
            # Add doc entity if not exists
            if not any(e['name'] == doc_entity_name for e in self.entities):
                self.entities.append({
                    'type': 'entity',
                    'name': doc_entity_name,
                    'entityType': 'Documentation',
                    'observations': [
                        f'Documentation for {entity_name.split(".")[-1]}',
                        f'upd:{datetime.now().strftime("%Y-%m-%d")},refs:0'
                    ]
                })
            
            # Add DOCUMENTED_IN relation
            self.relations.append({
                'type': 'relation',
                'from': entity_name,
                'to': doc_entity_name,
                'relationType': 'DOCUMENTED_IN'
            })
        
        added = len(self.relations) - initial_relations
        print(f"  Added {added} DOCUMENTED_IN relations")
    
    def phase6_validate(self) -> dict:
        """Phase 6: Validate and save"""
        print("\n" + "="*60)
        print("PHASE 6/6: VALIDATION")
        print("="*60)
        
        # Write codegraph
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for entity in self.entities:
                f.write(json.dumps(entity, separators=(',', ':'), ensure_ascii=False) + '\n')
            for relation in self.relations:
                f.write(json.dumps(relation, separators=(',', ':'), ensure_ascii=False) + '\n')
        
        # Validate
        size_kb = self.output_path.stat().st_size / 1024
        
        # Test load time
        start = time.time()
        with open(self.output_path, 'r', encoding='utf-8') as f:
            f.read()
        load_ms = (time.time() - start) * 1000
        
        print(f"Validation:")
        print(f"  Size: {size_kb:.2f} KB {'[OK]' if size_kb <= 100 else '[!]'}")
        print(f"  Load time: {load_ms:.0f} ms {'[OK]' if load_ms <= 1000 else '[!]'}")
        print(f"  Entities: {len(self.entities)}")
        print(f"  Relations: {len(self.relations)}")
        print(f"  Modules: {self.module_count}")
        print(f"  Classes: {self.class_count}")
        print(f"  Space remaining: {100-size_kb:.2f} KB")
        
        return {
            'size_kb': size_kb,
            'load_ms': load_ms,
            'success': size_kb <= 100
        }
    
    def _get_domains(self) -> list[str]:
        """Get unique domains from file structure"""
        domains = set()
        for file in self.src_dir.rglob('*.py'):
            if 'commander' in str(file).lower():
                domains.add('Commander')
            else:
                domains.add('Core')
        return sorted(domains)
    
    def _get_domain_description(self, domain: str) -> str:
        """Get domain description"""
        descriptions = {
            'Commander': 'Command system: node management, UI coordination, user actions',
            'Core': 'Core logic: file processing, token detection, data handling'
        }
        return descriptions.get(domain, f'{domain} domain')
    
    def _scan_modules_and_classes(self):
        """Scan modules and classes"""
        for py_file in self.src_dir.rglob('*.py'):
            if py_file.stem == '__init__':
                continue
            
            # Determine domain
            if 'commander' in str(py_file).lower():
                domain = 'Commander'
            else:
                domain = 'Core'
            
            # Create module entity (NO .File suffix)
            rel_path = py_file.relative_to(self.src_dir)
            module_name = str(rel_path).replace('\\', '_').replace('/', '_').replace('.py', '')
            
            # Extract description and filter generic ones
            description = self._extract_module_description(py_file)
            
            # FILTER: Skip generic observations
            if self._is_generic_observation(description):
                description = None  # Will use empty observation
            
            module_entity_name = f'Code.Module.{module_name}'  # NO .File
            
            observations = [
                description if description else 'No description',
                f'upd:{datetime.now().strftime("%Y-%m-%d")},refs:0'
            ]
            
            # Add FULL MODULE DOCSTRING as separate observation (if exists and rich enough)
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))
                    docstring = ast.get_docstring(tree)
                    if docstring and len(docstring) > 100:
                        # Take up to 400 chars of docstring (multi-line OK)
                        doc_clean = ' '.join(docstring.split())  # Remove extra whitespace
                        if len(doc_clean) > 400:
                            doc_clean = doc_clean[:397] + '...'
                        observations.insert(1, f"Doc: {doc_clean}")
            except:
                pass
            
            # Add SECOND observation with function/method details (RICH CONTEXT)
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(py_file))
                    
                    # Extract top-level functions WITH FULL SIGNATURES (RICHER)
                    functions = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                            # Get FULL function signature with types if available
                            args = []
                            for arg in node.args.args:
                                if arg.arg == 'self' or arg.arg == 'cls':
                                    continue
                                # Include type annotations if present
                                if arg.annotation:
                                    arg_str = f"{arg.arg}:{self._get_type_name(arg.annotation)}"
                                else:
                                    arg_str = arg.arg
                                args.append(arg_str)
                            
                            # Get return type if present
                            ret_type = ''
                            if node.returns:
                                ret_type = f" -> {self._get_type_name(node.returns)}"
                            
                            # Build signature
                            if len(', '.join(args)) > 30:  # Long arg list
                                functions.append(f"{node.name}(...){ret_type}")
                            else:
                                functions.append(f"{node.name}({', '.join(args)}){ret_type}")
                    
                    if functions:
                        # Create comma-separated list (up to 300 chars for richer context)
                        func_list = ', '.join(functions[:12])  # First 12 functions
                        if len(func_list) > 300:
                            func_list = func_list[:297] + '...'
                        observations.insert(1, f"Methods: {func_list}")
                    
                    # Extract project imports (THIRD observation - dependencies)
                    project_imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            # Capture relative imports (starting with .) and src/commander imports
                            if node.module:
                                is_project_import = (
                                    node.module.startswith('src.') or 
                                    node.module.startswith('commander.') or
                                    node.level > 0  # Relative import like "from . import X"
                                )
                            else:
                                is_project_import = node.level > 0  # "from . import X"
                            
                            if is_project_import:
                                # Extract imported names
                                imported = [alias.name for alias in node.names if alias.name != '*'][:4]
                                if imported:
                                    if node.module:
                                        module_short = node.module.replace('src.', '').replace('commander.', '')
                                    else:
                                        module_short = '.'  # Relative import
                                    project_imports.append(f"{module_short}::{','.join(imported)}")
                    
                    if project_imports:
                        # Add import observation (up to 350 chars for richer context)
                        import_str = ' | '.join(project_imports[:7])
                        if len(import_str) <= 350:
                            observations.insert(len(observations)-1, f"Deps: {import_str}")
                    
                    # Extract class details (FOURTH observation - class info)
                    class_details = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            # Get base classes
                            bases = []
                            for base in node.bases:
                                if isinstance(base, ast.Name):
                                    bases.append(base.id)
                                elif isinstance(base, ast.Attribute):
                                    bases.append(base.attr)
                            
                            # Count methods
                            methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef) and not item.name.startswith('_')]
                            
                            if bases:
                                class_details.append(f"{class_name}({','.join(bases[:2])}):{len(methods)}m")
                            else:
                                class_details.append(f"{class_name}:{len(methods)}m")
                    
                    if class_details and len(class_details) >= 2:  # Only add if 2+ classes
                        class_str = ', '.join(class_details[:6])
                        if len(class_str) <= 280:
                            observations.insert(len(observations)-1, f"Classes: {class_str}")
            except:
                pass
            
            # Remove 'No description' if it's the only functional observation
            if observations[0] == 'No description' and len([o for o in observations if 'upd:' not in o]) == 1:
                observations = [observations[-1]]  # Keep only metadata
            
            self.entities.append({
                'type': 'entity',
                'name': module_entity_name,
                'entityType': 'Module',
                'observations': observations
            })
            
            self.module_count += 1
            
            # Link module directly to domain (no clusters)
            self.relations.append({
                'type': 'relation',
                'from': module_entity_name,
                'to': f'Code.Domain.{domain}',
                'relationType': 'BELONGS_TO'
            })
            
            # Extract classes
            self._extract_classes(py_file, module_entity_name)
    
    def _create_import_relations(self):
        """Create IMPORTS relations between modules based on import statements"""
        print("Creating module dependency relations...")
        
        import_count = 0
        
        # Build a mapping of module names for quick lookup
        module_names = {entity['name'].replace('Code.Module.', ''): entity['name'] 
                       for entity in self.entities if entity['entityType'] == 'Module'}
        
        # Scan each Python file for imports
        for py_file in self.src_dir.rglob('*.py'):
            if py_file.stem == '__init__':
                continue
            
            # Get source module name
            rel_path = py_file.relative_to(self.src_dir)
            source_module = str(rel_path).replace('\\', '_').replace('/', '_').replace('.py', '')
            source_entity = f'Code.Module.{source_module}'
            
            # Extract imports from this file
            imported_modules = self._extract_project_imports(py_file, module_names)
            
            # Create IMPORTS relation for each project import
            for target_module in imported_modules:
                target_entity = f'Code.Module.{target_module}'
                
                # Only create relation if both modules exist in our graph
                if source_entity in [e['name'] for e in self.entities] and \
                   target_entity in [e['name'] for e in self.entities]:
                    self.relations.append({
                        'type': 'relation',
                        'from': source_entity,
                        'to': target_entity,
                        'relationType': 'IMPORTS'
                    })
                    import_count += 1
        
        print(f"  Created {import_count} IMPORTS relations")
    
    def _extract_project_imports(self, file_path: Path, module_names: dict) -> set:
        """Extract project module imports (not external libraries)"""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                # Handle "from X import Y"
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Handle src.module imports
                        if node.module.startswith('src.'):
                            module_path = node.module.replace('src.', '').replace('.', '_')
                            if module_path in module_names:
                                imports.add(module_path)
                        # Handle commander.module imports
                        elif node.module.startswith('commander.'):
                            module_path = 'commander_' + node.module.replace('commander.', '').replace('.', '_')
                            if module_path in module_names:
                                imports.add(module_path)
                        # Handle relative imports (from . import X, from .module import Y)
                        elif node.level > 0:
                            # Relative imports - try to resolve
                            # Get directory of current file
                            current_dir = file_path.parent
                            
                            # Go up 'level' directories
                            for _ in range(node.level - 1):
                                current_dir = current_dir.parent
                            
                            # If module specified, construct full path
                            if node.module:
                                target_parts = node.module.split('.')
                                target_path = current_dir
                                for part in target_parts:
                                    target_path = target_path / part
                                
                                # Check if this resolves to a known module
                                rel_to_src = target_path.relative_to(self.src_dir) if target_path.is_relative_to(self.src_dir) else None
                                if rel_to_src:
                                    module_path = str(rel_to_src).replace('\\', '_').replace('/', '_')
                                    if module_path in module_names:
                                        imports.add(module_path)
                
                # Handle "import X"
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        # Only track project imports
                        if alias.name.startswith('src.'):
                            module_path = alias.name.replace('src.', '').replace('.', '_')
                            if module_path in module_names:
                                imports.add(module_path)
                        elif alias.name.startswith('commander.'):
                            module_path = 'commander_' + alias.name.replace('commander.', '').replace('.', '_')
                            if module_path in module_names:
                                imports.add(module_path)
        except:
            pass
        
        return imports
    
    def _extract_module_description(self, file_path: Path) -> str:
        """Extract RICH functional description from module with aggressive context extraction"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
                # Collect ALL context first
                context_parts = []
                
                # 1. Try module docstring (highest priority)
                docstring = ast.get_docstring(tree)
                if docstring:
                    # Take first meaningful line
                    for line in docstring.split('\n'):
                        line = line.strip()
                        if len(line) > 15 and not line.startswith('"""') and not line.startswith("'''"):
                            context_parts.append(line[:180])
                            break
                
                # 2. Count classes and functions
                classes = []
                functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                    elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                        functions.append(node.name)
                
                # 3. Analyze imports for dependencies
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
                
                # Build RICH observation from collected context
                if context_parts:
                    # Use docstring as base
                    base = context_parts[0]
                else:
                    # 4. Try file-level comments if no docstring
                    lines = content.split('\n')
                    for i, line in enumerate(lines[:30]):
                        stripped = line.strip()
                        if stripped.startswith('class ') or stripped.startswith('def '):
                            break
                        if stripped.startswith('#') and not stripped.startswith('#!'):
                            comment = stripped.lstrip('#').strip()
                            if len(comment) > 20 and not all(c in '=-_*#' for c in comment):
                                context_parts.append(comment[:180])
                                break
                    
                    # 5. Generate from class info
                    if classes:
                        if len(classes) == 1:
                            # Get inheritance info for single class
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef) and node.name == classes[0]:
                                    bases = []
                                    for base in node.bases:
                                        if isinstance(base, ast.Name):
                                            bases.append(base.id)
                                        elif isinstance(base, ast.Attribute):
                                            bases.append(base.attr)
                                    
                                    if bases:
                                        base = f"Implements {classes[0]} ({', '.join(bases[:2])})"
                                    else:
                                        base = f"Implements {classes[0]} class"
                                    break
                        elif len(classes) <= 3:
                            base = f"Classes: {', '.join(classes)} implementation"
                        else:
                            base = f"{len(classes)} classes: {', '.join(classes[:2])}, ..."
                    # 6. Generate from functions
                    elif functions:
                        main_funcs = [f for f in functions if f in ['main', 'run', 'execute', 'process', 'load', 'save', 'create', 'handle']]
                        if main_funcs:
                            base = f"Functions: {', '.join(main_funcs[:3])} operations"
                        elif len(functions) <= 3:
                            base = f"Utility functions: {', '.join(functions[:3])}"
                        else:
                            base = f"{len(functions)} utility functions"
                    # 7. Infer from imports
                    elif 'PyQt5' in imports or 'PyQt6' in imports:
                        base = "UI module: PyQt interface components"
                    elif 'asyncio' in imports or 'threading' in imports:
                        base = "Async/threading module: background processing"
                    elif 'json' in imports and 'pathlib' in imports:
                        base = "Data processing: file I/O and JSON handling"
                    else:
                        return None
                
                # Enhance with counts (RICHER CONTEXT)
                enhancements = []
                if classes:
                    enhancements.append(f"{len(classes)} class{'es' if len(classes)>1 else ''}")
                if functions:
                    enhancements.append(f"{len(functions)} func{'s' if len(functions)>1 else ''}")
                
                # Add key imports (PyQt, asyncio, etc.)
                key_imports = [imp for imp in imports if imp in ['PyQt5', 'PyQt6', 'asyncio', 'threading', 'requests', 'aiohttp']]
                if key_imports:
                    enhancements.append(f"uses {', '.join(key_imports[:2])}")
                
                # Combine base + enhancements
                if enhancements:
                    return f"{base} | {', '.join(enhancements)}"[:200]
                else:
                    return base[:200] if base else None
                    
        except:
            pass
        
        return None
    
    def _is_generic_observation(self, obs: str) -> bool:
        """Check if observation is generic/useless"""
        if not obs:
            return True
        
        obs_lower = obs.lower()
        
        # Generic patterns to filter out (check each condition)
        if 'module:' in obs_lower:
            return True
        if 'file:' in obs_lower:
            return True
        if obs_lower.startswith('file '):
            return True
        if obs_lower == 'file':
            return True
        if len(obs) < 15:  # Too short to be useful
            return True
        
        # Allow "Implements X", "Classes: X", "Functions: X" - they're informative!
        return False
    
    def _get_type_name(self, node: ast.AST) -> str:
        """Extract type annotation name from AST node"""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Constant):
                return str(node.value)
            elif isinstance(node, ast.Subscript):
                # Handle List[X], Dict[X, Y], etc.
                return self._get_type_name(node.value)
            elif isinstance(node, ast.Attribute):
                # Handle module.Type
                return node.attr
            else:
                return '?'
        except:
            return '?'
    
    def _extract_classes(self, file_path: Path, module_name: str):
        """Extract ONLY key class entities from module"""
        # Define key classes we care about (for navigation/architecture)
        key_classes = {
            'LogReportGUI', 'MainWindow', 'CommanderMainWindow',
            'ContextMenuService', 'BsToolCommandService', 
            'NodeTreeView', 'NodeTreePresenter',
            'SystemFileLoader', 'TokenDetector',
            'ReportGenerator', 'LogCreator'
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    
                    # FILTER: Only include key classes
                    if class_name not in key_classes:
                        continue
                    
                    # Extract class description
                    description = self._extract_class_description(node)
                    
                    # FILTER: Skip generic observations
                    if self._is_generic_observation(description):
                        description = None
                    
                    class_entity_name = f'Code.Class.{module_name.replace("Code.Module.", "")}.{class_name}'
                    
                    observations = []
                    if description:
                        observations.append(description)
                    observations.append(f'upd:{datetime.now().strftime("%Y-%m-%d")},refs:0')
                    
                    self.entities.append({
                        'type': 'entity',
                        'name': class_entity_name,
                        'entityType': 'Class',
                        'observations': observations
                    })
                    
                    self.class_count += 1
                    
                    # Link class to module
                    self.relations.append({
                        'type': 'relation',
                        'from': class_entity_name,
                        'to': module_name,
                        'relationType': 'BELONGS_TO'
                    })
        except:
            pass
    
    def _extract_class_description(self, node: ast.ClassDef) -> str:
        """Extract RICH functional description from class with context analysis"""
        try:
            # Collect context
            class_name = node.name
            context_parts = []
            
            # 1. Class docstring (highest priority)
            docstring = ast.get_docstring(node)
            if docstring:
                # Take first meaningful line
                for line in docstring.split('\n'):
                    line = line.strip()
                    if len(line) > 15 and not line.startswith('"""') and not line.startswith("'''"):
                        context_parts.append(line[:180])
                        break
            
            # 2. Analyze inheritance
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            
            # 3. Count and analyze methods
            methods = []
            public_methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
                    if not item.name.startswith('_'):
                        public_methods.append(item.name)
            
            # Build rich observation
            if context_parts:
                base_desc = context_parts[0]
            elif bases:
                # Generate from inheritance
                if 'QMainWindow' in bases or 'QDialog' in bases or 'QWidget' in bases:
                    base_desc = f"UI component: {class_name} window/widget"
                elif 'QThread' in bases or 'Thread' in bases:
                    base_desc = f"Background worker: {class_name} thread"
                elif any('Service' in b for b in bases):
                    base_desc = f"Service: {class_name} business logic"
                else:
                    base_desc = f"{class_name} (extends {', '.join(bases[:2])})"
            else:
                # Infer from method patterns
                if 'load' in public_methods or 'read' in public_methods or 'parse' in public_methods:
                    base_desc = f"Loader/Parser: {class_name} reads and processes data"
                elif 'save' in public_methods or 'write' in public_methods or 'export' in public_methods:
                    base_desc = f"Writer: {class_name} saves and exports data"
                elif 'validate' in public_methods or 'check' in public_methods:
                    base_desc = f"Validator: {class_name} validation logic"
                elif 'process' in public_methods or 'execute' in public_methods or 'run' in public_methods:
                    base_desc = f"Processor: {class_name} executes operations"
                elif 'get' in public_methods and 'set' in public_methods:
                    base_desc = f"Data model: {class_name} encapsulates state"
                # Infer from class name pattern
                elif 'Service' in class_name:
                    base_desc = f"Service: {class_name.replace('Service', '')} operations"
                elif 'View' in class_name:
                    base_desc = f"View: {class_name.replace('View', '')} UI display"
                elif 'Presenter' in class_name:
                    base_desc = f"Presenter: mediates {class_name.replace('Presenter', '')} logic"
                elif 'Manager' in class_name:
                    base_desc = f"Manager: coordinates {class_name.replace('Manager', '')} resources"
                elif 'Worker' in class_name:
                    base_desc = f"Worker: async {class_name.replace('Worker', '')} processing"
                elif 'Dialog' in class_name:
                    base_desc = f"Dialog: {class_name.replace('Dialog', '')} configuration UI"
                elif 'Window' in class_name:
                    base_desc = f"Window: {class_name.replace('Window', '')} main interface"
                else:
                    base_desc = f"{class_name} class"
            
            # Enhance with method counts and key methods
            enhancements = []
            if public_methods:
                enhancements.append(f"{len(public_methods)} public methods")
                # List first 3 key methods
                key_methods = public_methods[:3]
                if key_methods:
                    enhancements.append(f"({', '.join(key_methods)})")
            
            if bases:
                enhancements.append(f"extends {', '.join(bases[:2])}")
            
            # Combine
            if enhancements:
                return f"{base_desc} | {', '.join(enhancements)}"[:200]
            else:
                return base_desc[:200] if base_desc else None
            
        except:
            pass
        
        return None


if __name__ == '__main__':
    updater = SimpleCodeGraphUpdater('d:/_APP/LOGReport')
    updater.run()
