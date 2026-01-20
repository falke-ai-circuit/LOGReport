"""
Phase 4: Code-Test Alignment Analysis
Validates test structure against src/ codebase structure
"""
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class AlignmentAnalyzer:
    """Analyzes alignment between source code and test files"""
    
    def __init__(self, src_dir: Path, tests_dir: Path):
        self.src_dir = src_dir
        self.tests_dir = tests_dir
        self.src_modules = {}  # module_name -> path
        self.test_files = {}   # test_name -> path
        self.mappings = []     # List of (src, test, status) tuples
        self.orphaned_tests = []
        self.untested_modules = []
        
    def scan_source_files(self) -> Dict[str, Path]:
        """Scan all Python files in src/ directory"""
        modules = {}
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".egg-info" in str(py_file):
                continue
            
            # Get module path relative to src/
            rel_path = py_file.relative_to(self.src_dir)
            module_name = str(rel_path).replace("\\", ".").replace(".py", "")
            
            # Skip __init__ files for now
            if module_name.endswith(".__init__"):
                module_name = module_name[:-9]  # Remove .__init__
            
            modules[module_name] = py_file
        
        return modules
    
    def scan_test_files(self) -> Dict[str, Path]:
        """Scan all test files in tests/ directory"""
        tests = {}
        for test_file in self.tests_dir.rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue
            
            # Get test path relative to tests/
            rel_path = test_file.relative_to(self.tests_dir)
            test_name = str(rel_path).replace("\\", "/")
            
            tests[test_name] = test_file
        
        return tests
    
    def extract_test_target(self, test_name: str) -> List[str]:
        """
        Extract potential source module names from test filename.
        E.g., test_log_creator.py -> log_creator
        """
        # Remove test_ prefix and .py suffix
        base_name = test_name.split("/")[-1]  # Get filename
        if base_name.startswith("test_"):
            base_name = base_name[5:]  # Remove "test_"
        base_name = base_name.replace(".py", "")
        
        # Generate possible module names
        candidates = []
        
        # Direct match (e.g., log_creator)
        candidates.append(base_name)
        
        # Commander module match (e.g., commander.log_writer)
        candidates.append(f"commander.{base_name}")
        
        # Utils match
        candidates.append(f"utils.{base_name}")
        
        # Commander submodules
        for subdir in ["services", "ui", "presenters", "commands", "utils"]:
            candidates.append(f"commander.{subdir}.{base_name}")
        
        return candidates
    
    def analyze_alignment(self):
        """Perform alignment analysis"""
        print("🔍 Scanning source files...")
        self.src_modules = self.scan_source_files()
        print(f"   Found {len(self.src_modules)} source modules")
        
        print("🔍 Scanning test files...")
        self.test_files = self.scan_test_files()
        print(f"   Found {len(self.test_files)} test files")
        
        print("\n📊 Analyzing test-to-code mappings...")
        
        # Track which modules have tests
        tested_modules = set()
        
        for test_name, test_path in sorted(self.test_files.items()):
            candidates = self.extract_test_target(test_name)
            found = False
            
            for candidate in candidates:
                if candidate in self.src_modules:
                    self.mappings.append((candidate, test_name, "✅ ALIGNED"))
                    tested_modules.add(candidate)
                    found = True
                    break
            
            if not found:
                # Check for partial matches (integration/system tests)
                if any(keyword in test_name.lower() for keyword in 
                       ["integration", "comprehensive", "workflow", "e2e", "end_to_end"]):
                    self.mappings.append(("INTEGRATION", test_name, "🔗 INTEGRATION"))
                else:
                    self.orphaned_tests.append(test_name)
                    self.mappings.append(("ORPHANED", test_name, "⚠️ ORPHANED"))
        
        # Find untested modules
        for module_name in self.src_modules:
            if module_name not in tested_modules:
                # Skip certain modules
                if any(skip in module_name for skip in ["__init__", "runtime_hooks"]):
                    continue
                self.untested_modules.append(module_name)
        
        print(f"   ✅ {len(tested_modules)} modules have tests")
        print(f"   ⚠️ {len(self.orphaned_tests)} orphaned tests")
        print(f"   ❌ {len(self.untested_modules)} untested modules")
    
    def generate_report(self) -> str:
        """Generate detailed alignment report"""
        report = []
        report.append("# PHASE 4: Code-Test Alignment Analysis Report")
        report.append("=" * 80)
        report.append("")
        
        # Summary statistics
        report.append("## Summary Statistics")
        report.append("")
        report.append(f"**Source Modules**: {len(self.src_modules)}")
        report.append(f"**Test Files**: {len(self.test_files)}")
        report.append(f"**Aligned Mappings**: {len([m for m in self.mappings if '✅' in m[2]])}")
        report.append(f"**Integration Tests**: {len([m for m in self.mappings if '🔗' in m[2]])}")
        report.append(f"**Orphaned Tests**: {len(self.orphaned_tests)}")
        report.append(f"**Untested Modules**: {len(self.untested_modules)}")
        report.append("")
        
        # Alignment ratio
        tested_count = len([m for m in self.mappings if '✅' in m[2]])
        total_testable = len(self.src_modules) - len([m for m in self.src_modules if "__init__" in m])
        alignment_ratio = (tested_count / total_testable * 100) if total_testable > 0 else 0
        report.append(f"**Alignment Ratio**: {alignment_ratio:.1f}% ({tested_count}/{total_testable})")
        report.append("")
        report.append("---")
        report.append("")
        
        # Detailed mappings
        report.append("## Detailed Test-to-Code Mappings")
        report.append("")
        
        # Group by status
        aligned = [m for m in self.mappings if '✅' in m[2]]
        integration = [m for m in self.mappings if '🔗' in m[2]]
        orphaned = [m for m in self.mappings if '⚠️' in m[2]]
        
        if aligned:
            report.append(f"### ✅ ALIGNED TESTS ({len(aligned)} files)")
            report.append("")
            report.append("| Source Module | Test File | Status |")
            report.append("|---------------|-----------|--------|")
            for src, test, status in sorted(aligned):
                report.append(f"| `{src}` | `{test}` | {status} |")
            report.append("")
        
        if integration:
            report.append(f"### 🔗 INTEGRATION TESTS ({len(integration)} files)")
            report.append("")
            report.append("*These tests cover multiple modules or end-to-end workflows*")
            report.append("")
            for _, test, _ in sorted(integration):
                report.append(f"- `{test}`")
            report.append("")
        
        if orphaned:
            report.append(f"### ⚠️ ORPHANED TESTS ({len(orphaned)} files)")
            report.append("")
            report.append("*Tests with no clear corresponding source module*")
            report.append("")
            for _, test, _ in sorted(orphaned):
                report.append(f"- `{test}`")
            report.append("")
        
        # Untested modules
        if self.untested_modules:
            report.append("---")
            report.append("")
            report.append(f"## ❌ UNTESTED MODULES ({len(self.untested_modules)} modules)")
            report.append("")
            report.append("*Source modules with no corresponding test files*")
            report.append("")
            
            # Group by category
            by_category = defaultdict(list)
            for module in sorted(self.untested_modules):
                if "commander" in module:
                    category = "Commander"
                elif "utils" in module:
                    category = "Utils"
                else:
                    category = "Core"
                by_category[category].append(module)
            
            for category, modules in sorted(by_category.items()):
                report.append(f"### {category} ({len(modules)} modules)")
                report.append("")
                for module in modules:
                    src_path = self.src_modules[module]
                    lines = sum(1 for _ in src_path.open('r', encoding='utf-8', errors='ignore'))
                    report.append(f"- `{module}` ({lines} lines)")
                report.append("")
        
        # Recommendations
        report.append("---")
        report.append("")
        report.append("## Recommendations")
        report.append("")
        
        if alignment_ratio < 70:
            report.append("⚠️ **LOW ALIGNMENT**: Less than 70% of modules have corresponding tests.")
            report.append("")
        elif alignment_ratio < 85:
            report.append("⚡ **MODERATE ALIGNMENT**: 70-85% coverage, approaching target.")
            report.append("")
        else:
            report.append("✅ **GOOD ALIGNMENT**: Over 85% of modules have tests.")
            report.append("")
        
        if self.orphaned_tests:
            report.append(f"1. **Review {len(self.orphaned_tests)} orphaned tests**:")
            report.append("   - Verify if they test deprecated code (consider deletion)")
            report.append("   - Check if they're integration tests (reclassify)")
            report.append("   - Update naming to match source modules")
            report.append("")
        
        if self.untested_modules:
            report.append(f"2. **Create tests for {len(self.untested_modules)} untested modules**:")
            report.append("   - Prioritize high-complexity or critical modules")
            report.append("   - Focus on commander services (business logic)")
            report.append("   - Cover error handling and edge cases")
            report.append("")
        
        report.append("3. **Validate imports**:")
        report.append("   - Run `pytest --collect-only` to check test discovery")
        report.append("   - Verify no broken imports after Phase 3 reorganization")
        report.append("")
        
        return "\n".join(report)
    
    def export_json(self) -> Dict:
        """Export alignment data as JSON"""
        return {
            "summary": {
                "source_modules": len(self.src_modules),
                "test_files": len(self.test_files),
                "aligned": len([m for m in self.mappings if '✅' in m[2]]),
                "integration": len([m for m in self.mappings if '🔗' in m[2]]),
                "orphaned": len(self.orphaned_tests),
                "untested": len(self.untested_modules)
            },
            "mappings": [
                {"source": src, "test": test, "status": status}
                for src, test, status in self.mappings
            ],
            "untested_modules": self.untested_modules,
            "orphaned_tests": self.orphaned_tests
        }


def main():
    # Paths
    root = Path(__file__).parent.parent
    src_dir = root / "src"
    tests_dir = root / "tests"
    output_dir = root / "logs"
    
    # Run analysis
    analyzer = AlignmentAnalyzer(src_dir, tests_dir)
    analyzer.analyze_alignment()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    output_file = output_dir / "tests_analysis_PHASE_4_2025-01-12_060000.md"
    output_file.write_text(report, encoding="utf-8")
    print(f"\n✅ Report saved to: {output_file}")
    
    # Save JSON
    json_file = output_dir / "test_alignment_data.json"
    json_file.write_text(json.dumps(analyzer.export_json(), indent=2), encoding="utf-8")
    print(f"✅ JSON data saved to: {json_file}")
    
    print("\n" + "=" * 80)
    print(report.split("---")[0])  # Print summary


if __name__ == "__main__":
    main()
