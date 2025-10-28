# Refactor Code Workflow

**Purpose**: Code optimization via legacy removal+consolidation+splitting+performance tuning | **Focus**: Remove unused code+split large files+optimize speed+maintain functionality | **Architecture**: 11-phase interleaved (0→1,2→3,4→5,6→7,8→9,10→POST) | **Modes**: Analysis(odd) + Implementation(even) | **Target**: Clean codebase+optimal file sizes+improved performance+zero breakage | **Universal**: Handles any codebase with configurable targets

**PRE-PHASE: INVENTORY & VALIDATION** (MANDATORY): 1.Complete Inventory(scan ALL code+detect large files+identify unused+map dependencies+detect duplicates) | 2.Reference Audit(map usage→definitions+identify dead code+validate imports+detect circular deps) | 3.Pre-Validation(functionality baseline+test pass rate+performance baseline+codegraph integrity) | 4.Context(maintain inventory+track file sizes+track complexity metrics+track dependencies)

**POST-PHASE: VERIFICATION** (MANDATORY): 1.Final Inventory(re-scan ALL code+measure file sizes+confirm removals+validate splits) | 2.Comparison(initial vs final+lines removed+files split+performance gains+test integrity) | 3.Completion(100% tests passing+zero unused code+optimal file sizes+performance improved)

## 🎯 Refactoring Targets

**FILE SIZE TARGETS**: <500 lines = GOOD | 500-1000 lines = REVIEW | 1000-2000 lines = SPLIT | >2000 lines = **CRITICAL SPLIT** | **COMPLEXITY TARGETS**: Cyclomatic <10 = GOOD | 10-20 = REVIEW | 20-30 = REFACTOR | >30 = **CRITICAL REFACTOR** | **PERFORMANCE TARGETS**: Import time <0.5s | Function execution baseline +10% max degradation | Memory usage baseline +5% max increase | **CODE HEALTH**: Zero unused imports | Zero dead code | Zero duplicate functions | Minimal nesting depth (<4 levels)

## 11-Phase Architecture: Inventory(0) | Analysis(1→2) | Unused(3→4) | Split(5→6) | Optimize(7→8) | Test(9→10) | Validation(POST)

| Phase | Layer | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| 0 | Code Inventory | Complete code scanning+metrics+dependency mapping | Analysis | Code inventory map+metrics report |
| 1 | Dead Code Analysis | Unused code detection+import analysis+reference tracking | Analysis | Dead code candidates+unused imports |
| 2 | Dead Code Removal | Remove unused code+clean imports+validate tests | Implementation | Cleaned codebase+updated imports |
| 3 | Duplication Analysis | Detect duplicate code+similar patterns+consolidation opportunities | Analysis | Duplication report+merge plan |
| 4 | Consolidation | Merge duplicates+create utilities+refactor patterns | Implementation | Consolidated code+utility modules |
| 5 | File Split Analysis | Identify large files+analyze cohesion+plan splits | Analysis | Split plan+module organization |
| 6 | File Splitting | Split large files+reorganize modules+update imports | Implementation | Optimally sized files+clean structure |
| 7 | Performance Analysis | Profile code+identify bottlenecks+analyze complexity | Analysis | Performance report+optimization targets |
| 8 | Performance Optimization | Optimize algorithms+reduce complexity+improve efficiency | Implementation | Optimized code+performance gains |
| 9 | Integration Analysis | Test validation+integration checks+regression detection | Analysis | Test status+integration risks |
| 10 | Integration Testing | Run full test suite+fix breaks+validate functionality | Implementation | Passing tests+validated refactor |
| POST | Final Validation | Compare metrics+validate no breakage+confirm improvements | Manual | Completion report+metrics comparison |

## Parameters

**PRE-PHASE**: Complete inventory+validation MANDATORY | **POST-PHASE**: Verification+comparison MANDATORY | **Target**: Files specified OR auto-detect (>1000 lines) | **Safety**: Full test suite MUST pass | **Backup**: Auto-backup before changes | **Validation**: Tests+imports+performance+codegraph | **Reports**: `/logs/refactor_analysis_[phase]_[YYYY-MM-DD_HHMMSS].md` | **Thresholds**: Configurable via workflow parameters

## Execution: PRE-PHASE: INVENTORY→VALIDATION | Phases(0-10): Analysis(odd)→Implementation(even) | POST-PHASE: VERIFICATION→COMPARISON→COMPLETION

## Phase Operations

| Phase | Layer | Target | Commands |
|-------|-------|--------|----------|
| 0 | Inventory | Scan all code+measure sizes+calculate metrics+map dependencies+identify large files+detect duplicates+analyze complexity | scan_codebase\|measure_file_sizes\|calculate_complexity\|map_dependencies\|identify_large_files\|detect_duplicates\|analyze_imports |
| 1 | Dead Code Analysis | Detect unused functions+unused classes+unused imports+unreachable code+dead branches+orphaned files | analyze_usage\|track_references\|detect_unused_imports\|identify_dead_code\|analyze_call_graph\|check_coverage |
| 2 | Dead Code Removal | Remove unused imports+remove dead functions+remove orphaned files+clean up comments+validate imports+run tests | remove_unused_imports\|remove_dead_functions\|remove_orphaned_files\|clean_comments\|validate_imports\|run_test_suite |
| 3 | Duplication Analysis | Detect duplicate functions+similar code blocks+repeated patterns+copy-paste code+consolidation opportunities | detect_duplicate_code\|analyze_similarity\|identify_patterns\|find_copy_paste\|plan_consolidation |
| 4 | Consolidation | Extract common functions+create utility modules+merge similar code+refactor patterns+update references | extract_common\|create_utilities\|merge_duplicates\|refactor_patterns\|update_references\|run_tests |
| 5 | File Split Analysis | Identify files >1000 lines+analyze cohesion+detect logical boundaries+plan module splits+minimize coupling | identify_large_files\|analyze_cohesion\|detect_boundaries\|plan_splits\|calculate_coupling |
| 6 | File Splitting | Split large files+create submodules+reorganize structure+update imports+maintain interfaces+validate | split_files\|create_submodules\|reorganize_structure\|update_all_imports\|maintain_interfaces\|validate_splits\|run_tests |
| 7 | Performance Analysis | Profile import times+analyze algorithms+detect bottlenecks+measure complexity+identify inefficiencies | profile_imports\|analyze_algorithms\|detect_bottlenecks\|measure_complexity\|identify_inefficiencies\|benchmark_functions |
| 8 | Performance Optimization | Optimize algorithms+reduce complexity+cache results+improve loops+optimize imports+lazy loading | optimize_algorithms\|reduce_complexity\|add_caching\|optimize_loops\|optimize_imports\|implement_lazy_loading\|benchmark_gains |
| 9 | Integration Analysis | Run test suite+check coverage+validate imports+check for breaks+measure performance+validate codegraph | run_full_suite\|check_coverage\|validate_all_imports\|check_breaks\|measure_performance\|validate_codegraph |
| 10 | Integration Testing | Fix broken tests+fix broken imports+adjust for changes+validate functionality+update docs+final validation | fix_broken_tests\|fix_imports\|adjust_tests\|validate_functionality\|update_documentation\|final_test_run |

## 🔍 Dead Code Detection Logic

**UNUSED IMPORTS**: Import statement exists BUT never referenced in file | Import * BUT only subset used | Duplicate imports | Commented imports | **UNUSED FUNCTIONS**: Function defined BUT never called | Function in __all__ BUT never imported | Private function (_func) never called internally | **UNUSED CLASSES**: Class defined BUT never instantiated | Abstract class with no implementations | Exception class never raised | **UNREACHABLE CODE**: Code after return/break/continue | Code in if False blocks | Dead branches (impossible conditions) | **ORPHANED FILES**: Python file with no imports from other files | Module not in __init__.py | Module not referenced anywhere | **VALIDATION**: Cross-reference with tests | Check dynamic imports | Validate against codegraph | Exclude intentional (API, plugins, etc.)

## 📏 File Splitting Strategy

**SIZE TRIGGERS**: >2000 lines = **IMMEDIATE SPLIT** | >1500 lines = **HIGH PRIORITY** | >1000 lines = **REVIEW FOR SPLIT** | 500-1000 lines = **ACCEPTABLE** | <500 lines = **IDEAL** | **COHESION ANALYSIS**: Analyze imports (what's used together) | Analyze function calls (what calls what) | Analyze class relationships | Analyze data flow | **SPLIT BOUNDARIES**: By responsibility (SRP) | By abstraction level | By feature/domain | By layer (UI, logic, data) | **SPLIT TYPES**: Horizontal (layer separation: ui.py → ui_main.py, ui_widgets.py, ui_dialogs.py) | Vertical (feature separation: handler.py → token_handler.py, node_handler.py, log_handler.py) | Utility extraction (utils.py → validators.py, formatters.py, parsers.py) | **CONSTRAINTS**: Maintain public API | Minimize coupling | Single __init__.py for backward compatibility | Update all imports | Preserve tests

## 🚀 Performance Optimization Strategies

**IMPORT OPTIMIZATION**: Lazy imports (import inside functions for rarely used) | Conditional imports (import only when needed) | Remove unused imports (reduce load time) | Optimize import order | **ALGORITHM OPTIMIZATION**: Replace O(n²) with O(n log n) or O(n) | Use appropriate data structures (dict lookup vs list iteration) | Avoid repeated calculations (cache results) | Use generators for large datasets | **COMPLEXITY REDUCTION**: Simplify nested loops | Extract complex conditions | Reduce nesting depth | Use early returns | **CACHING**: Memoize expensive functions (@lru_cache) | Cache database queries | Cache file reads | Store computed results | **LAZY LOADING**: Defer initialization | Load on demand | Use properties for expensive operations | **PROFILING**: Measure before optimization | Profile import times | Profile function execution | Identify actual bottlenecks

## 🔄 Duplication Detection & Consolidation

**DETECTION METHODS**: Exact duplicates (100% match) | Near duplicates (>80% similarity) | Structural duplicates (same logic, different names) | Copy-paste detection (similar with modifications) | **SIMILARITY METRICS**: Code similarity (AST comparison) | Function signature similarity | Variable name patterns | Comment similarity | **CONSOLIDATION STRATEGIES**: Extract to utility function | Create base class | Use inheritance/composition | Create shared module | Apply DRY principle | **SAFE CONSOLIDATION**: Maintain behavior | Preserve tests | Update all references | Validate with tests | Document changes | **COMMON PATTERNS**: Database queries → query builder | Validation logic → validators module | File operations → file utils | String processing → string utils | API calls → API client

## 🧪 Test-Driven Refactoring

**TEST BASELINE**: Run full test suite BEFORE refactoring | Record pass rate + coverage | Document test execution time | Capture performance baseline | **CONTINUOUS VALIDATION**: Run tests after EACH change | Validate imports after restructuring | Check coverage after removal | Monitor performance after optimization | **TEST UPDATES**: Update imports in tests | Adjust for new structure | Add tests for new utilities | Maintain test coverage | **REGRESSION PREVENTION**: Compare before/after behavior | Validate edge cases | Check error handling | Verify integrations | **FINAL VALIDATION**: 100% of original tests passing | Coverage maintained or improved | No new failures | Performance improved or stable

## 📊 Metrics & Tracking

**CODE METRICS**: Lines of code (before/after) | File count (before/after) | Average file size | Cyclomatic complexity (before/after) | Import depth | **QUALITY METRICS**: Dead code removed (lines) | Duplicates eliminated (lines) | Large files split (count) | Imports optimized (count) | **PERFORMANCE METRICS**: Import time (before/after % change) | Function execution time (before/after % change) | Memory usage (before/after % change) | Benchmark improvements | **TEST METRICS**: Test pass rate (before/after) | Test coverage (before/after) | Test execution time (before/after) | New tests added | **REFACTOR IMPACT**: Files modified | Functions moved | Classes split | Utilities created | References updated

## 📂 File Splitting Strategy Example

**TYPICAL LARGE FILE**: Large monolithic file (2000+ lines) with mixed responsibilities

**SPLIT APPROACH**:
```
module/
├── __init__.py (public API exports)
├── core.py (main class - core logic, ~300-400 lines)
├── database_operations.py (DB operations, ~400 lines)
├── business_logic.py (business operations, ~500 lines)
├── data_operations.py (data operations, ~300 lines)
├── statistics.py (statistics/reporting, ~300 lines)
├── integrations.py (external integrations, ~400 lines)
├── relationships.py (relationship management, ~200 lines)
└── utilities.py (shared utilities, ~100 lines)
```

**BENEFITS**: Each file <500 lines | Clear responsibilities | Easier to maintain | Better testability | Reduced cognitive load | Improved import times

**BACKWARD COMPATIBILITY**: Original file imports/exports OR __init__.py exports all public API

## 🎯 Target File Candidates (Auto-Detected)

**Priority files** (>1000 lines, auto-detected from workspace):
- Files with >2000 lines - **CRITICAL SPLIT**
- Files with 1500-2000 lines - **HIGH PRIORITY**
- Files with 1000-1500 lines - **REVIEW FOR SPLIT**

**Detection criteria**:
- File size >1000 lines
- High cyclomatic complexity (>50)
- Multiple responsibilities detected
- High import count (>20)
- Mixed abstraction levels

## 📊 Analysis Reports

**Naming**: `refactor_analysis_[phase]_[YYYY-MM-DD_HHMMSS].md` | **Location**: `/logs/` | **Content**: Phase results+metrics+targets+changes+validation | **Usage**: Implementation phases reference reports | **Template**: `# Refactor Analysis - [Date] ## Phase [X] **Files**:[count] | **Lines**:[before→after] | **Issues**:[count] | **Actions**:[list] ### Metrics:[before/after] ### Targets:[list] ### Changes:[summary]`

## Output Formats

**PRE-PHASE**: `INVENTORY|TOTAL_FILES:[count]|TOTAL_LINES:[n]|LARGE_FILES(>1000):[n]|COMPLEX_FILES(>50):[n]|UNUSED_IMPORTS:[n]|DEAD_CODE_CANDIDATES:[n]|DUPLICATES:[n]|AVG_FILE_SIZE:[n]|MAX_FILE_SIZE:[n]|STATUS:[inventory_complete|validation_complete|baseline_captured]`

**POST-PHASE**: `VERIFICATION|INITIAL_FILES:[count]|FINAL_FILES:[count]|LINES_REMOVED:[n]|FILES_SPLIT:[n]|DUPLICATES_REMOVED:[n]|PERFORMANCE_GAIN:[%]|TESTS_PASSING:[%]|COVERAGE:[%]|STATUS:[comparison_complete|verification_complete|all_tests_passing]`

**Analysis**: `PHASE:[0-10/10]|LAYER:[Inventory|DeadCode|Duplication|Split|Performance|Integration]|TARGET:[file_or_pattern]|SIZE:[lines]|COMPLEXITY:[score]|ISSUE:[large_file|dead_code|duplicate|unused_import|performance_bottleneck|high_complexity]|ACTION:[remove|consolidate|split|optimize|test]|PRIORITY:[critical|high|medium|low]|IMPACT:[lines|files|performance_%]|REPORT:refactor_analysis_[phase]_[date].md`

**Implementation**: `PHASE:[2-10/10]|LAYER:[DeadCode|Consolidation|Split|Optimization|Testing]|TARGET:[specific_file_or_function]|COMMAND:[specific_operation]|STATUS:[planned|executing|completed|validated]|IMPACT:[lines_removed|files_created|performance_improved|tests_passing]|METRICS:[before→after|improvement_%]|TESTS:[pass_rate|coverage]|REF:[analysis_report]`

## 🔐 Safety Guarantees

**BACKUP**: Auto-create backups before changes | Store in backups/ directory | Include timestamp | Preserve for 7 days | **VALIDATION**: Run tests after EACH phase | Validate imports after restructuring | Check codegraph integrity | Verify no functional changes | **ROLLBACK**: Keep backups for quick rollback | Document all changes | Maintain change log | Enable easy reversion | **TESTING**: Require 100% test pass | Maintain or improve coverage | Validate performance | Check integrations

## 🎯 Success Criteria

**CODE HEALTH**: Zero unused imports | Zero dead code | All files <1000 lines (or documented exception) | Complexity <30 per function | **PERFORMANCE**: Import time improved or stable | Function execution improved or stable | Memory usage stable or reduced | Benchmarks improved or stable | **TESTS**: 100% of tests passing | Coverage maintained or improved | No new failures | Integration validated | **STRUCTURE**: Clear module organization | Single responsibility per file | Minimal coupling | Clean dependencies | **DOCUMENTATION**: Updated imports documented | Split files documented | API changes documented | Performance improvements documented

## Workflow Integration

**Before**: Run `update_codegraph.md` to establish baseline | Run `update_tests.md` to ensure test health | **During**: Reference codegraph for dependencies | Validate against test suite continuously | **After**: Run `update_codegraph.md` to reflect changes | Run `update_tests.md` to validate test integrity | Update `CHANGELOG.md` with refactor summary

---

**CRITICAL RULES**: 
1. NEVER break functionality - tests MUST pass 100%
2. ALWAYS backup before changes
3. ALWAYS run tests after each phase
4. ALWAYS validate imports after restructuring
5. ALWAYS maintain backward compatibility where possible
6. ALWAYS document significant changes
7. ALWAYS measure performance impact
8. ALWAYS update codegraph after completion
