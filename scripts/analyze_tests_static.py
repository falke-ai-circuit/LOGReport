"""
Static Test Analysis Script
Analyzes test structure without executing tests (Python 3.13 compatible)
"""
import ast
import json
import pathlib
from collections import defaultdict
from typing import Dict, List, Tuple

class TestAnalyzer(ast.NodeVisitor):
    """AST-based test analyzer"""
    
    def __init__(self):
        self.test_count = 0
        self.assertion_count = 0
        self.mock_usage = []
        self.imports = []
        self.fixtures = []
        self.parametrize_count = 0
        self.docstring = None
        
    def visit_FunctionDef(self, node):
        if node.name.startswith('test_'):
            self.test_count += 1
            # Check for parametrize decorator
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr') and decorator.func.attr == 'parametrize':
                        self.parametrize_count += 1
            
            # Count assertions in function
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    self.assertion_count += 1
                elif isinstance(child, ast.Call):
                    if hasattr(child.func, 'attr'):
                        if 'assert' in child.func.attr.lower():
                            self.assertion_count += 1
                    elif hasattr(child.func, 'id'):
                        if 'assert' in child.func.id.lower():
                            self.assertion_count += 1
        
        elif node.name.startswith('fixture') or any(
            hasattr(d, 'id') and d.id == 'fixture' for d in node.decorator_list
        ):
            self.fixtures.append(node.name)
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            if 'mock' in alias.name.lower():
                self.mock_usage.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            full_import = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full_import)
            if 'mock' in full_import.lower() or 'mock' in module.lower():
                self.mock_usage.append(full_import)
        self.generic_visit(node)

def analyze_test_file(filepath: pathlib.Path) -> Dict:
    """Analyze a single test file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(filepath))
        
        analyzer = TestAnalyzer()
        analyzer.visit(tree)
        
        # Get module docstring
        docstring = ast.get_docstring(tree)
        
        # Calculate metrics
        lines = len(content.splitlines())
        assertions_per_test = analyzer.assertion_count / analyzer.test_count if analyzer.test_count > 0 else 0
        
        # Detect test category from imports
        category = 'unit'
        if any('integration' in imp.lower() for imp in analyzer.imports):
            category = 'integration'
        elif any('system' in imp.lower() or 'e2e' in imp.lower() for imp in analyzer.imports):
            category = 'system'
        
        # Detect GUI dependencies
        has_gui = any('pyqt' in imp.lower() or 'pyside' in imp.lower() for imp in analyzer.imports)
        has_telnet = any('telnet' in imp.lower() for imp in analyzer.imports)
        
        # Quality score (0-10)
        score = 0.0
        score += min(2.0, analyzer.test_count * 0.2)  # Test count (max 2)
        score += min(3.0, assertions_per_test * 0.5)  # Assertions (max 3)
        score += 2.0 if len(analyzer.mock_usage) > 0 else 0  # Mocking (2)
        score += 1.5 if docstring else 0  # Docstring (1.5)
        score += 1.0 if analyzer.parametrize_count > 0 else 0  # Parametrize (1)
        score += 0.5 if len(analyzer.fixtures) > 0 else 0  # Fixtures (0.5)
        
        return {
            'path': str(filepath),
            'category': category,
            'test_count': analyzer.test_count,
            'assertion_count': analyzer.assertion_count,
            'assertions_per_test': round(assertions_per_test, 2),
            'mock_count': len(analyzer.mock_usage),
            'mock_types': analyzer.mock_usage[:5],  # Sample
            'fixture_count': len(analyzer.fixtures),
            'parametrize_count': analyzer.parametrize_count,
            'has_docstring': bool(docstring),
            'docstring': docstring[:100] if docstring else None,
            'lines': lines,
            'imports': analyzer.imports[:10],  # Sample
            'has_gui_dependency': has_gui,
            'has_telnet_dependency': has_telnet,
            'quality_score': round(score, 1),
            'executable': not (has_gui or has_telnet),  # Can run in current env
        }
    
    except Exception as e:
        return {
            'path': str(filepath),
            'error': str(e),
            'executable': False
        }

def analyze_all_tests(test_dir: pathlib.Path) -> Dict:
    """Analyze all test files in directory"""
    results = []
    
    # Find all test files
    test_files = sorted(test_dir.rglob('test_*.py'))
    
    print(f"📊 Analyzing {len(test_files)} test files...")
    
    for test_file in test_files:
        result = analyze_test_file(test_file)
        results.append(result)
        
        # Progress indicator
        if len(results) % 10 == 0:
            print(f"  ... {len(results)}/{len(test_files)} analyzed")
    
    # Calculate aggregate metrics
    total_tests = sum(r.get('test_count', 0) for r in results)
    total_assertions = sum(r.get('assertion_count', 0) for r in results)
    avg_quality = sum(r.get('quality_score', 0) for r in results) / len(results) if results else 0
    
    executable_count = sum(1 for r in results if r.get('executable', False))
    
    # Group by category
    by_category = defaultdict(list)
    for r in results:
        by_category[r.get('category', 'unknown')].append(r)
    
    # Identify gaps
    no_docstring = [r['path'] for r in results if not r.get('has_docstring', False)]
    low_assertions = [r['path'] for r in results if r.get('assertions_per_test', 0) < 2.0]
    no_mocking = [r['path'] for r in results if r.get('mock_count', 0) == 0]
    
    summary = {
        'total_files': len(results),
        'total_tests': total_tests,
        'total_assertions': total_assertions,
        'avg_assertions_per_test': round(total_assertions / total_tests, 2) if total_tests > 0 else 0,
        'avg_quality_score': round(avg_quality, 2),
        'executable_count': executable_count,
        'blocked_count': len(results) - executable_count,
        'by_category': {
            cat: {
                'count': len(files),
                'tests': sum(f.get('test_count', 0) for f in files),
                'avg_quality': round(sum(f.get('quality_score', 0) for f in files) / len(files), 2) if files else 0
            }
            for cat, files in by_category.items()
        },
        'gaps': {
            'no_docstring': len(no_docstring),
            'low_assertions': len(low_assertions),
            'no_mocking': len(no_mocking)
        },
        'gap_files': {
            'no_docstring': no_docstring[:10],  # Sample
            'low_assertions': low_assertions[:10],
            'no_mocking': no_mocking[:10]
        }
    }
    
    return {
        'summary': summary,
        'files': results
    }

if __name__ == '__main__':
    import sys
    
    # Get test directory
    test_dir = pathlib.Path('tests')
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)
    
    # Analyze
    results = analyze_all_tests(test_dir)
    
    # Save to JSON
    output_file = pathlib.Path('logs/test_static_analysis.json')
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2), encoding='utf-8')
    
    # Print summary
    summary = results['summary']
    print("\n" + "="*70)
    print("📊 STATIC TEST ANALYSIS SUMMARY")
    print("="*70)
    print(f"\n📁 Total Files: {summary['total_files']}")
    print(f"✅ Executable: {summary['executable_count']} ({summary['executable_count']/summary['total_files']*100:.1f}%)")
    print(f"❌ Blocked: {summary['blocked_count']} ({summary['blocked_count']/summary['total_files']*100:.1f}%)")
    print(f"\n🧪 Total Tests: {summary['total_tests']}")
    print(f"🎯 Total Assertions: {summary['total_assertions']}")
    print(f"📊 Avg Assertions/Test: {summary['avg_assertions_per_test']}")
    print(f"⭐ Avg Quality Score: {summary['avg_quality_score']}/10.0")
    
    print(f"\n📦 By Category:")
    for cat, data in summary['by_category'].items():
        print(f"  {cat.upper():12} → {data['count']:2} files, {data['tests']:3} tests, {data['avg_quality']:.1f}/10 quality")
    
    print(f"\n🚨 Quality Gaps:")
    print(f"  Missing Docstrings: {summary['gaps']['no_docstring']}")
    print(f"  Low Assertions (<2): {summary['gaps']['low_assertions']}")
    print(f"  No Mocking: {summary['gaps']['no_mocking']}")
    
    print(f"\n💾 Full report saved: {output_file}")
    print("="*70)
