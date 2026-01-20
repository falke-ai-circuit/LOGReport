"""
Code Graph Generator - Creates hierarchical codegraph.json from source folder
Mirrors project_memory.json structure with 6-layer hierarchy and relations

UNIVERSAL & PORTABLE:
- Works with any Python project
- Configurable source directory and output path
- Automatic domain/cluster detection based on folder structure
- Command-line arguments support
- Zero project-specific dependencies

USAGE:
    python generate_codegraph.py [options]
    
OPTIONS:
    --src PATH          Source directory to scan (default: ./src or ./)
    --output PATH       Output file path (default: ./codegraph.json)
    --exclude PATTERN   Exclude pattern (can be used multiple times)
    --verbose           Enable verbose logging

EXAMPLES:
    python generate_codegraph.py
    python generate_codegraph.py --src ./myapp --output ./graph.json
    python generate_codegraph.py --src ./lib --exclude test --exclude __pycache__
"""

import ast
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime

# Default exclude patterns
DEFAULT_EXCLUDES = ['__pycache__', '.egg-info', 'venv', '.venv', 'env', '.env', 'build', 'dist', '.git']

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CodeGraphGenerator:
    """Generates codegraph.json by scanning and analyzing Python codebase"""

    def __init__(self, src_path: Path, output_path: Path, exclude_patterns: List[str] = None, verbose: bool = False):
        """
        Initialize the code graph generator.

        Args:
            src_path: Path to source folder to scan
            output_path: Path where codegraph.json will be written
            exclude_patterns: List of patterns to exclude (folders/files)
            verbose: Enable verbose logging
        """
        self.src_path = src_path.resolve()
        self.output_path = output_path.resolve()
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDES
        self.verbose = verbose
        
        self.entities: List[Dict[str, Any]] = []
        self.relations: List[Dict[str, str]] = []
        self.seen_clusters: Set[str] = set()
        self.seen_domains: Set[str] = set()
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        # Auto-detect project structure
        self.domain_map = self._build_domain_map()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug(f"Source path: {self.src_path}")
            logger.debug(f"Output path: {self.output_path}")
            logger.debug(f"Exclude patterns: {self.exclude_patterns}")
            logger.debug(f"Domain map: {self.domain_map}")

    def _build_domain_map(self) -> Dict[str, str]:
        """
        Auto-detect domain mapping based on folder structure.
        Scans source directory to identify common patterns.
        
        Returns:
            Dictionary mapping folder names to domain names
        """
        domain_map = {
            # Common patterns (case-insensitive matching)
            'api': 'API',
            'apis': 'API',
            'backend': 'Backend',
            'core': 'Core',
            'commands': 'Commands',
            'commander': 'Commander',
            'config': 'Configuration',
            'configuration': 'Configuration',
            'controllers': 'Controllers',
            'db': 'Database',
            'database': 'Database',
            'frontend': 'Frontend',
            'handlers': 'Handlers',
            'middleware': 'Middleware',
            'models': 'Models',
            'presenters': 'Presenters',
            'routes': 'Routes',
            'services': 'Services',
            'tests': 'Testing',
            'ui': 'UI',
            'utils': 'Utilities',
            'utilities': 'Utilities',
            'views': 'Views',
            'widgets': 'Widgets',
        }
        
        # Scan first-level directories to discover custom domains
        if self.src_path.exists():
            for item in self.src_path.iterdir():
                if item.is_dir() and not self._is_excluded(item):
                    folder_name = item.name.lower()
                    if folder_name not in domain_map:
                        # Auto-add as capitalized domain
                        domain_map[folder_name] = folder_name.capitalize()
        
        return domain_map

    def _is_excluded(self, path: Path) -> bool:
        """
        Check if path matches any exclude pattern.
        
        Args:
            path: Path to check
            
        Returns:
            True if should be excluded
        """
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False

    def generate(self) -> None:
        """Main generation workflow"""
        logger.info(f"Scanning {self.src_path}...")
        
        if not self.src_path.exists():
            logger.error(f"Source path does not exist: {self.src_path}")
            return
        
        # Scan all Python files
        python_files = []
        for py_file in self.src_path.rglob("*.py"):
            if not self._is_excluded(py_file):
                python_files.append(py_file)
        
        logger.info(f"Found {len(python_files)} Python files")
        
        for py_file in python_files:
            self._process_file(py_file)
        
        # Add type-level entities
        self._add_hierarchy_structure()
        
        # Write output
        self._write_codegraph()
        logger.info(f"✅ Generated {len(self.entities)} entities and {len(self.relations)} relations")
        logger.info(f"📝 Output: {self.output_path}")

    def _process_file(self, file_path: Path) -> None:
        """
        Process a single Python file.

        Args:
            file_path: Path to Python file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            relative_path = file_path.relative_to(self.src_path)
            module_path = self._get_module_path(relative_path)
            
            # Extract module info
            module_docstring = ast.get_docstring(tree) or "No description"
            self._add_module_entity(module_path, str(relative_path), module_docstring)
            
            # Extract imports
            imports = self._extract_imports(tree)
            for imp in imports:
                self._add_import_relation(module_path, imp)
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._process_class(node, module_path, relative_path)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Only top-level functions (not methods)
                    if self._is_top_level(node, tree):
                        self._process_function(node, module_path, relative_path, is_method=False)
        
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")

    def _get_module_path(self, relative_path: Path) -> str:
        """
        Convert file path to module path.

        Args:
            relative_path: Relative path from src/

        Returns:
            Module path (e.g., "commander.services.context_menu_service")
        """
        parts = list(relative_path.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace(".py", "")
        return ".".join(parts)

    def _add_module_entity(self, module_path: str, file_path: str, docstring: str) -> None:
        """Add module entity"""
        entity_name = f"Code.Module.{module_path.replace('.', '_')}.File"
        domain = self._get_domain_from_path(module_path)
        cluster = self._get_cluster_from_path(module_path)
        
        # Truncate docstring to 80-120 chars
        desc = docstring.split('\n')[0][:120] if docstring else "Module file"
        
        entity = {
            "type": "entity",
            "name": entity_name,
            "entityType": "Module",
            "observations": [
                f"File: {file_path}",
                f"Module: {module_path}",
                desc,
                f"upd:{self.today},refs:0"
            ]
        }
        self.entities.append(entity)
        
        # Add relations: Module → Cluster → Domain → Type
        self._add_entity_relations(entity_name, cluster, domain, "Code.Type.Codebase")

    def _process_class(self, node: ast.ClassDef, module_path: str, relative_path: Path) -> None:
        """Process a class definition"""
        class_name = node.name
        docstring = ast.get_docstring(node) or f"{class_name} class"
        desc = docstring.split('\n')[0][:120]
        
        entity_name = f"Code.Class.{module_path.replace('.', '_')}.{class_name}"
        module_entity = f"Code.Module.{module_path.replace('.', '_')}.File"
        domain = self._get_domain_from_path(module_path)
        cluster = self._get_cluster_from_path(module_path)
        
        # Extract base classes
        bases = [self._get_name(base) for base in node.bases]
        
        observations = [
            f"Class in {module_path}",
            desc,
        ]
        
        if bases:
            observations.append(f"Inherits: {', '.join(bases)}")
        
        # Count methods
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        observations.append(f"Methods: {len(methods)}")
        observations.append(f"upd:{self.today},refs:0")
        
        entity = {
            "type": "entity",
            "name": entity_name,
            "entityType": "Class",
            "observations": observations
        }
        self.entities.append(entity)
        
        # Add relation: Class → Module (not directly to cluster!)
        self.relations.append({
            "type": "relation",
            "from": entity_name,
            "to": module_entity,
            "relationType": "BELONGS_TO"
        })
        
        # Add inheritance relations
        for base in bases:
            if base and base not in ["object", "ABC"]:
                self.relations.append({
                    "type": "relation",
                    "from": entity_name,
                    "to": f"Code.Class.{base}",
                    "relationType": "INHERITS"
                })
        
        # Process methods
        for method in methods:
            self._process_function(method, module_path, relative_path, is_method=True, class_name=class_name, class_entity=entity_name)

    def _process_function(self, node: ast.FunctionDef, module_path: str, relative_path: Path, 
                          is_method: bool = False, class_name: str = None, class_entity: str = None) -> None:
        """Process a function or method definition"""
        func_name = node.name
        docstring = ast.get_docstring(node) or f"{func_name} function"
        desc = docstring.split('\n')[0][:120]
        
        # Build entity name
        if is_method:
            entity_name = f"Code.Method.{module_path.replace('.', '_')}_{class_name}.{func_name}"
        else:
            entity_name = f"Code.Function.{module_path.replace('.', '_')}.{func_name}"
        
        module_entity = f"Code.Module.{module_path.replace('.', '_')}.File"
        
        # Extract parameters
        params = [arg.arg for arg in node.args.args if arg.arg != "self"]
        
        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]
        
        observations = [
            f"{'Method' if is_method else 'Function'} in {module_path}",
            desc,
        ]
        
        if params:
            observations.append(f"Params: {', '.join(params[:5])}")  # First 5 params
        
        if decorators:
            observations.append(f"Decorators: {', '.join(decorators)}")
        
        observations.append(f"upd:{self.today},refs:0")
        
        entity = {
            "type": "entity",
            "name": entity_name,
            "entityType": "Method" if is_method else "Function",
            "observations": observations
        }
        self.entities.append(entity)
        
        # Add relation: Method → Class or Function → Module
        if is_method and class_entity:
            self.relations.append({
                "type": "relation",
                "from": entity_name,
                "to": class_entity,
                "relationType": "BELONGS_TO"
            })
        else:
            self.relations.append({
                "type": "relation",
                "from": entity_name,
                "to": module_entity,
                "relationType": "BELONGS_TO"
            })
        
        # Extract function calls (simplified - just names)
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Call):
                called_func = self._get_name(subnode.func)
                if called_func and called_func not in ["print", "len", "str", "int", "list", "dict"]:
                    self.relations.append({
                        "type": "relation",
                        "from": entity_name,
                        "to": f"Code.Function.{called_func}",
                        "relationType": "CALLS"
                    })

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
        return imports

    def _add_import_relation(self, from_module: str, imported_module: str) -> None:
        """Add import relation"""
        self.relations.append({
            "type": "relation",
            "from": f"Code.Module.{from_module.replace('.', '_')}.File",
            "to": f"Code.Module.{imported_module.replace('.', '_')}.File",
            "relationType": "IMPORTS"
        })

    def _add_entity_relations(self, entity_name: str, cluster: str, domain: str, type_name: str) -> None:
        """
        Add 3-layer relations: Entity → Cluster → Domain → Type

        Args:
            entity_name: Full entity name
            cluster: Cluster name
            domain: Domain name
            type_name: Type name
        """
        cluster_full = f"Code.Cluster.{cluster}"
        domain_full = f"Code.Domain.{domain}"
        
        # Entity → Cluster
        self.relations.append({
            "type": "relation",
            "from": entity_name,
            "to": cluster_full,
            "relationType": "BELONGS_TO"
        })
        
        # Cluster → Domain (only once per cluster)
        if cluster not in self.seen_clusters:
            self.seen_clusters.add(cluster)
            
            # Add cluster entity
            self.entities.append({
                "type": "entity",
                "name": cluster_full,
                "entityType": "Cluster",
                "observations": [
                    f"Cluster for {cluster} components",
                    f"upd:{self.today},refs:0"
                ]
            })
            
            self.relations.append({
                "type": "relation",
                "from": cluster_full,
                "to": domain_full,
                "relationType": "BELONGS_TO"
            })
        
        # Domain → Type (only once per domain)
        if domain not in self.seen_domains:
            self.seen_domains.add(domain)
            
            # Add domain entity
            self.entities.append({
                "type": "entity",
                "name": domain_full,
                "entityType": "Domain",
                "observations": [
                    f"Domain for {domain} functionality",
                    f"upd:{self.today},refs:0"
                ]
            })
            
            self.relations.append({
                "type": "relation",
                "from": domain_full,
                "to": type_name,
                "relationType": "IS_A"
            })

    def _get_domain_from_path(self, module_path: str) -> str:
        """
        Determine domain from module path using auto-detected domain map.
        
        Args:
            module_path: Dot-separated module path
            
        Returns:
            Domain name
        """
        parts = module_path.split('.')
        if len(parts) == 1:
            return "Core"
        
        # Check first-level folder against domain map
        first_folder = parts[0].lower()
        return self.domain_map.get(first_folder, parts[0].capitalize())

    def _get_cluster_from_path(self, module_path: str) -> str:
        """
        Determine cluster from module path using hierarchical naming.
        
        Args:
            module_path: Dot-separated module path
            
        Returns:
            Cluster name (format: "FirstLevel.SecondLevel")
        """
        parts = module_path.split('.')
        
        if len(parts) == 1:
            # Root level: use folder name or "Root" + filename
            return f"Root.{parts[0].capitalize()}"
        elif len(parts) == 2:
            # Two levels: use both
            return f"{parts[0].capitalize()}.{parts[1].capitalize()}"
        else:
            # Three+ levels: use first two
            return f"{parts[0].capitalize()}.{parts[1].capitalize()}"

    def _add_hierarchy_structure(self) -> None:
        """Add top-level hierarchy entities (Type, Domain, Cluster)"""
        # Add Type entity
        self.entities.insert(0, {
            "type": "entity",
            "name": "Code.Type.Codebase",
            "entityType": "Type",
            "observations": [
                "Root type for all codebase entities",
                f"Generated from src/ folder scan",
                f"upd:{self.today},refs:0"
            ]
        })

    def _get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ""

    def _is_top_level(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is top-level (not a method)"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return False
        return True

    def _write_codegraph(self) -> None:
        """Write entities and relations to codegraph.json"""
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for entity in self.entities:
                f.write(json.dumps(entity) + '\n')
            for relation in self.relations:
                f.write(json.dumps(relation) + '\n')


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Generate hierarchical code graph from Python source code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --src ./myapp --output ./graph.json
  %(prog)s --src ./lib --exclude test --exclude __pycache__ --verbose
  
Output:
  Creates codegraph.json with 6-layer hierarchy:
    Type → Domain → Cluster → Module → Class → Method/Function
        """
    )
    
    parser.add_argument(
        '--src',
        type=Path,
        default=None,
        help='Source directory to scan (default: ./src if exists, otherwise ./)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('codegraph.json'),
        help='Output file path (default: ./codegraph.json)'
    )
    
    parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        help='Exclude pattern (can be used multiple times, adds to defaults)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Code Graph Generator v1.0 (Universal & Portable)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point with argument parsing"""
    args = parse_arguments()
    
    # Determine source path
    if args.src:
        src_path = args.src
    else:
        # Auto-detect: prefer ./src if exists, otherwise current directory
        project_root = Path.cwd()
        src_candidate = project_root / "src"
        src_path = src_candidate if src_candidate.exists() else project_root
    
    # Combine default excludes with user-provided excludes
    exclude_patterns = DEFAULT_EXCLUDES + args.exclude
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate
    logger.info("=" * 60)
    logger.info("Code Graph Generator - Universal & Portable")
    logger.info("=" * 60)
    
    generator = CodeGraphGenerator(
        src_path=src_path,
        output_path=args.output,
        exclude_patterns=exclude_patterns,
        verbose=args.verbose
    )
    generator.generate()
    
    logger.info("=" * 60)
    logger.info("✅ Code graph generation complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
