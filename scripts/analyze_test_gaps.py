"""
Phase 5: Gap Analysis
Identifies critical testing gaps and prioritizes untested modules
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
import ast
from collections import defaultdict


class GapAnalyzer:
    """Analyzes testing gaps and prioritizes coverage needs"""
    
    def __init__(self, alignment_data_path: Path, src_dir: Path):
        self.alignment_data_path = alignment_data_path
        self.src_dir = src_dir
        self.alignment_data = {}
        self.gap_analysis = {
            "p0_critical": [],
            "p1_high": [],
            "p2_medium": [],
            "p3_low": [],
            "performance_tests_needed": [],
            "orphaned_reclassification": [],
            "missing_test_types": []
        }
        
    def load_alignment_data(self):
        """Load Phase 4 alignment analysis"""
        with open(self.alignment_data_path, 'r', encoding='utf-8') as f:
            self.alignment_data = json.load(f)
        print(f"✅ Loaded alignment data: {len(self.alignment_data.get('untested_modules', []))} untested modules")
    
    def analyze_module_complexity(self, module_name: str) -> Dict:
        """Analyze complexity metrics for a module"""
        # Convert module name to file path
        module_path = module_name.replace(".", "/") + ".py"
        file_path = self.src_dir / module_path
        
        if not file_path.exists():
            return {"error": "File not found", "loc": 0, "complexity": 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Count metrics
            loc = len(content.splitlines())
            classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            imports = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
            
            # Simple complexity heuristic
            complexity_score = (loc * 0.1) + (classes * 5) + (functions * 2) + (imports * 0.5)
            
            return {
                "loc": loc,
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "complexity": round(complexity_score, 2)
            }
        except Exception as e:
            return {"error": str(e), "loc": 0, "complexity": 0}
    
    def categorize_untested_modules(self):
        """Categorize untested modules by priority"""
        untested = self.alignment_data.get("untested_modules", [])
        
        print(f"\n🔍 Analyzing {len(untested)} untested modules...")
        
        for module in untested:
            metrics = self.analyze_module_complexity(module)
            loc = metrics.get("loc", 0)
            complexity = metrics.get("complexity", 0)
            
            # Determine criticality
            is_service = "services" in module
            is_core = module in ["gui", "main", "processor", "node_config_dialog"]
            is_large = loc > 300
            is_complex = complexity > 50
            
            priority_score = 0
            reasons = []
            
            if is_core:
                priority_score += 40
                reasons.append("core module")
            if is_large:
                priority_score += 30
                reasons.append(f"large ({loc} LOC)")
            if is_complex:
                priority_score += 20
                reasons.append(f"complex (score: {complexity})")
            if is_service:
                priority_score += 10
                reasons.append("service layer")
            
            module_data = {
                "module": module,
                "loc": loc,
                "complexity": complexity,
                "classes": metrics.get("classes", 0),
                "functions": metrics.get("functions", 0),
                "priority_score": priority_score,
                "reasons": reasons
            }
            
            # Categorize by priority
            if priority_score >= 60:
                self.gap_analysis["p0_critical"].append(module_data)
            elif priority_score >= 40:
                self.gap_analysis["p1_high"].append(module_data)
            elif priority_score >= 20:
                self.gap_analysis["p2_medium"].append(module_data)
            else:
                self.gap_analysis["p3_low"].append(module_data)
        
        # Sort each category by priority score
        for category in ["p0_critical", "p1_high", "p2_medium", "p3_low"]:
            self.gap_analysis[category].sort(key=lambda x: x["priority_score"], reverse=True)
        
        print(f"   P0 Critical: {len(self.gap_analysis['p0_critical'])} modules")
        print(f"   P1 High: {len(self.gap_analysis['p1_high'])} modules")
        print(f"   P2 Medium: {len(self.gap_analysis['p2_medium'])} modules")
        print(f"   P3 Low: {len(self.gap_analysis['p3_low'])} modules")
    
    def analyze_orphaned_tests(self):
        """Analyze orphaned tests and suggest reclassification"""
        orphaned = self.alignment_data.get("orphaned_tests", [])
        
        print(f"\n🔍 Analyzing {len(orphaned)} orphaned tests...")
        
        behavioral_keywords = ["button", "click", "ui", "behavior", "display", "action"]
        duplicate_patterns = ["_v2", "_additional", "_fixed", "_simple", "_standalone"]
        
        for test_path in orphaned:
            test_name = test_path.split("/")[-1].replace("test_", "").replace(".py", "")
            
            suggestion = {
                "test": test_path,
                "name": test_name,
                "recommendation": "unknown"
            }
            
            # Check for behavioral tests
            if any(kw in test_name.lower() for kw in behavioral_keywords):
                suggestion["recommendation"] = "reclassify_as_integration"
                suggestion["reason"] = "behavioral/UI test pattern"
            
            # Check for potential duplicates
            elif any(pattern in test_name.lower() for pattern in duplicate_patterns):
                suggestion["recommendation"] = "investigate_duplicate"
                suggestion["reason"] = "version suffix detected"
            
            # Check for specific module patterns
            elif "token" in test_name.lower():
                suggestion["recommendation"] = "align_with_token_utils"
                suggestion["reason"] = "token-related functionality"
            
            elif "rpc" in test_name.lower():
                suggestion["recommendation"] = "align_with_rpc_service"
                suggestion["reason"] = "RPC command functionality"
            
            elif "node" in test_name.lower():
                suggestion["recommendation"] = "align_with_node_manager"
                suggestion["reason"] = "node management functionality"
            
            else:
                suggestion["recommendation"] = "review_manually"
                suggestion["reason"] = "unclear module mapping"
            
            self.gap_analysis["orphaned_reclassification"].append(suggestion)
        
        # Group by recommendation
        by_recommendation = defaultdict(list)
        for item in self.gap_analysis["orphaned_reclassification"]:
            by_recommendation[item["recommendation"]].append(item)
        
        for rec, items in by_recommendation.items():
            print(f"   {rec}: {len(items)} tests")
    
    def identify_missing_test_types(self):
        """Identify missing test categories"""
        print(f"\n🔍 Identifying missing test types...")
        
        # Performance tests
        self.gap_analysis["performance_tests_needed"] = [
            {
                "type": "throughput",
                "description": "Command queue throughput test",
                "target": "commander.command_queue",
                "suggested_file": "tests/performance/test_command_queue_throughput.py"
            },
            {
                "type": "concurrency",
                "description": "Telnet session concurrency test",
                "target": "commander.services.telnet_service",
                "suggested_file": "tests/performance/test_telnet_concurrency.py"
            },
            {
                "type": "memory",
                "description": "Memory leak detection in long-running sessions",
                "target": "commander.session_manager",
                "suggested_file": "tests/performance/test_memory_leak_detection.py"
            }
        ]
        
        # Edge case tests
        self.gap_analysis["missing_test_types"].append({
            "category": "edge_cases",
            "description": "Error handling and boundary conditions",
            "priority": "P1",
            "suggested_locations": [
                "tests/unit/edge_cases/test_null_handling.py",
                "tests/unit/edge_cases/test_boundary_conditions.py",
                "tests/unit/edge_cases/test_error_propagation.py"
            ]
        })
        
        # Regression tests
        self.gap_analysis["missing_test_types"].append({
            "category": "regression",
            "description": "Known bug regression tests (only 2 currently)",
            "priority": "P2",
            "suggested_locations": [
                "tests/regression/telnet_issues/",
                "tests/regression/command_queue_issues/"
            ]
        })
        
        print(f"   Performance tests needed: {len(self.gap_analysis['performance_tests_needed'])}")
        print(f"   Missing test categories: {len(self.gap_analysis['missing_test_types'])}")
    
    def generate_report(self) -> str:
        """Generate comprehensive gap analysis report"""
        report = []
        report.append("# PHASE 5: Gap Analysis Report")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        p0_count = len(self.gap_analysis["p0_critical"])
        p1_count = len(self.gap_analysis["p1_high"])
        orphaned_count = len(self.gap_analysis["orphaned_reclassification"])
        perf_count = len(self.gap_analysis["performance_tests_needed"])
        
        report.append(f"**Critical Testing Gaps Identified**: {p0_count} P0 modules, {p1_count} P1 modules")
        report.append(f"**Orphaned Tests**: {orphaned_count} tests need reclassification")
        report.append(f"**Performance Tests**: {perf_count} critical performance tests missing (0 exist)")
        report.append(f"**Total Untested Modules**: {len(self.alignment_data.get('untested_modules', []))}")
        report.append("")
        report.append("---")
        report.append("")
        
        # P0 Critical Modules
        if self.gap_analysis["p0_critical"]:
            report.append(f"## 🚨 P0 CRITICAL MODULES ({len(self.gap_analysis['p0_critical'])} modules)")
            report.append("")
            report.append("*Must be tested before production deployment*")
            report.append("")
            report.append("| Module | LOC | Complexity | Priority | Reasons |")
            report.append("|--------|-----|------------|----------|---------|")
            
            for module_data in self.gap_analysis["p0_critical"]:
                module = module_data["module"]
                loc = module_data["loc"]
                complexity = module_data["complexity"]
                score = module_data["priority_score"]
                reasons = ", ".join(module_data["reasons"])
                report.append(f"| `{module}` | {loc} | {complexity} | {score} | {reasons} |")
            
            report.append("")
        
        # P1 High Priority
        if self.gap_analysis["p1_high"]:
            report.append(f"## ⚠️ P1 HIGH PRIORITY ({len(self.gap_analysis['p1_high'])} modules)")
            report.append("")
            report.append("| Module | LOC | Complexity | Priority | Reasons |")
            report.append("|--------|-----|------------|----------|---------|")
            
            for module_data in self.gap_analysis["p1_high"][:10]:  # Top 10
                module = module_data["module"]
                loc = module_data["loc"]
                complexity = module_data["complexity"]
                score = module_data["priority_score"]
                reasons = ", ".join(module_data["reasons"])
                report.append(f"| `{module}` | {loc} | {complexity} | {score} | {reasons} |")
            
            if len(self.gap_analysis["p1_high"]) > 10:
                report.append(f"| ... | | | | *({len(self.gap_analysis['p1_high']) - 10} more modules)* |")
            
            report.append("")
        
        # Performance Tests
        report.append("---")
        report.append("")
        report.append(f"## ⚡ PERFORMANCE TESTS NEEDED ({len(self.gap_analysis['performance_tests_needed'])} tests)")
        report.append("")
        report.append("**CRITICAL GAP**: No performance tests exist in current suite")
        report.append("")
        
        for perf_test in self.gap_analysis["performance_tests_needed"]:
            report.append(f"### {perf_test['type'].upper()}: {perf_test['description']}")
            report.append("")
            report.append(f"- **Target Module**: `{perf_test['target']}`")
            report.append(f"- **Suggested File**: `{perf_test['suggested_file']}`")
            report.append("")
        
        # Orphaned Tests
        report.append("---")
        report.append("")
        report.append(f"## 📋 ORPHANED TESTS ANALYSIS ({orphaned_count} tests)")
        report.append("")
        
        # Group by recommendation
        by_recommendation = defaultdict(list)
        for item in self.gap_analysis["orphaned_reclassification"]:
            by_recommendation[item["recommendation"]].append(item)
        
        for rec, items in sorted(by_recommendation.items(), key=lambda x: len(x[1]), reverse=True):
            count = len(items)
            report.append(f"### {rec.replace('_', ' ').title()} ({count} tests)")
            report.append("")
            
            for item in items[:5]:  # Top 5 per category
                report.append(f"- `{item['test']}` - {item['reason']}")
            
            if len(items) > 5:
                report.append(f"- *...and {len(items) - 5} more*")
            
            report.append("")
        
        # Recommendations
        report.append("---")
        report.append("")
        report.append("## 📌 RECOMMENDATIONS")
        report.append("")
        
        report.append("### Immediate Actions (Sprint 1)")
        report.append("")
        report.append("1. **Create P0 test suites** (Top 5 critical):")
        for module_data in self.gap_analysis["p0_critical"][:5]:
            suggested_path = self._suggest_test_path(module_data["module"])
            report.append(f"   - `{suggested_path}` → {module_data['functions']} functions, {module_data['classes']} classes")
        report.append("")
        
        report.append("2. **Performance test suite** (CRITICAL):")
        for perf_test in self.gap_analysis["performance_tests_needed"]:
            report.append(f"   - {perf_test['suggested_file']}")
        report.append("")
        
        report.append("3. **Reclassify orphaned tests**:")
        reclassify_count = len(by_recommendation.get("reclassify_as_integration", []))
        duplicate_count = len(by_recommendation.get("investigate_duplicate", []))
        report.append(f"   - Move {reclassify_count} behavioral tests to integration/")
        report.append(f"   - Investigate {duplicate_count} potential duplicates")
        report.append("")
        
        report.append("### Medium-term Goals (Sprint 2-3)")
        report.append("")
        report.append(f"4. **P1 module coverage** ({len(self.gap_analysis['p1_high'])} modules)")
        report.append(f"5. **Edge case testing** (error handling, boundary conditions)")
        report.append(f"6. **Regression test expansion** (current: 2 files, target: 10+)")
        report.append("")
        
        return "\n".join(report)
    
    def _suggest_test_path(self, module_name: str) -> str:
        """Suggest appropriate test file path for a module"""
        if "services" in module_name:
            # Service modules → integration tests
            test_name = module_name.split(".")[-1]
            return f"tests/integration/commander/test_{test_name}.py"
        elif "ui" in module_name:
            # UI modules → unit tests with mocking
            test_name = module_name.split(".")[-1]
            return f"tests/unit/ui/test_{test_name}.py"
        elif "commander" in module_name:
            # Commander modules → commander namespace
            test_name = module_name.split(".")[-1]
            return f"tests/commander/test_{test_name}.py"
        else:
            # Core modules → unit tests
            test_name = module_name.split(".")[-1] if "." in module_name else module_name
            return f"tests/unit/test_{test_name}.py"
    
    def export_json(self) -> Dict:
        """Export gap analysis as JSON"""
        return self.gap_analysis


def main():
    # Paths
    root = Path(__file__).parent.parent
    alignment_data_path = root / "logs" / "test_alignment_data.json"
    src_dir = root / "src"
    output_dir = root / "logs"
    
    # Run analysis
    analyzer = GapAnalyzer(alignment_data_path, src_dir)
    analyzer.load_alignment_data()
    analyzer.categorize_untested_modules()
    analyzer.analyze_orphaned_tests()
    analyzer.identify_missing_test_types()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    output_file = output_dir / "tests_analysis_PHASE_5_2025-01-12_070000.md"
    output_file.write_text(report, encoding="utf-8")
    print(f"\n✅ Report saved to: {output_file}")
    
    # Save JSON
    json_file = output_dir / "test_gap_analysis.json"
    json_file.write_text(json.dumps(analyzer.export_json(), indent=2), encoding="utf-8")
    print(f"✅ JSON data saved to: {json_file}")
    
    print("\n" + "=" * 80)
    print(report.split("---")[0])  # Print summary


if __name__ == "__main__":
    main()
