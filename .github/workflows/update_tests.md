# Update Tests Workflow

**Purpose**: Universal test ecosystem optimization via inventory→analysis→implementation | **Focus**: LLM-generated test consolidation+thematic hierarchy+code alignment+gap identification+obsolete removal | **Architecture**: 10-phase interleaved (0,1→2,3→4,5→6,7→8,9→10) | **Modes**: Analysis(odd) mcp-analyze | Implementation(even) mcp-code/architect | **Target**: ≥85% coverage+≥95% pass rate+hierarchical organization+zero obsolete+zero unconsolidated | **Universal**: Handles tests from ANY source (manual|LLM-generated|auto-generated)

**PRE-PHASE: INVENTORY & VALIDATION** (MANDATORY): 1.Complete Inventory(scan ALL tests+**detect unconsolidated**+categorize+detect duplication) | 2.Reference Audit(map tests→code+identify orphaned+obsolete+**validate LLM-generated tests**) | 3.Pre-Validation(completeness+mapping integrity+coverage gaps+**unconsolidated test count**) | 4.Context(maintain inventory+track thematic groupings+**track test origins**)

**POST-PHASE: VERIFICATION** (MANDATORY): 1.Final Inventory(re-scan ALL tests+categorize+**confirm zero unconsolidated**) | 2.Comparison(initial vs final+verify processed+changes documented+**unconsolidated→organized ratio**) | 3.Completion(100% coverage+≥85% code coverage+≥95% pass rate+**zero unconsolidated tests**)

## 🤖 LLM-Generated Test Detection & Handling

**DETECTION PATTERNS**: Root-level test_*.py files|Non-standard naming|Missing hierarchy|Ad-hoc test directories|Tests without proper categorization|Tests missing docstrings|Tests with generic names(test_1, test_new, test_temp)|Tests in wrong locations | **ORIGIN TRACKING**: Scan test metadata+creation timestamps+file locations+naming patterns+import patterns | **AUTO-CATEGORIZATION**: Analyze imports(determine unit/integration/system)|Analyze assertions(determine scope)|Analyze mocking(determine isolation level)|Analyze fixtures(determine dependencies)|Map to source modules(determine thematic group) | **QUALITY ASSESSMENT**: Check assertions exist|Check proper mocking|Check fixture usage|Check edge cases|Check documentation|Flag low-quality tests for enhancement

## 10-Phase Architecture: Inventory(0) | Coverage(1→2) | Organization(3→4) | Alignment(5→6) | Gaps(7→8) | Validation(9→10)

| Phase | Layer | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| 0 | Test Inventory | Complete test scanning+categorization+thematic clustering | mcp-analyze | Test inventory map+hierarchical structure |
| 1 | Coverage Analysis | Test coverage assessment+gap identification | mcp-analyze | Coverage gaps+untested critical paths |
| 2 | Coverage Implementation | Missing test creation+coverage improvement | mcp-code/architect | New test suites+improved coverage |
| 3 | Organization Analysis | Thematic organization+hierarchy analysis+duplication detection | mcp-analyze | Reorganization plan+merge opportunities |
| 4 | Organization Implementation | Test restructuring+hierarchy enforcement+duplication removal | mcp-code/architect | Organized test hierarchy+removed duplicates |
| 5 | Alignment Analysis | Test-to-code validation+obsolete test detection | mcp-analyze | Alignment gaps+obsolete test candidates |
| 6 | Alignment Implementation | Obsolete test removal+test updates for code changes | mcp-code/architect | Aligned tests+removed obsolete |
| 7 | Gap Analysis | Functional gap identification+missing test types detection | mcp-analyze | Gap report+prioritized test creation plan |
| 8 | Gap Implementation | Gap-filling test creation+test type diversification | mcp-code/architect | Complete test coverage+diverse test types |
| 9 | Validation Analysis | Quality validation+performance benchmarking+CI/CD integration check | mcp-analyze | Quality metrics+integration status |
| 10 | Validation Implementation | Quality enforcement+CI/CD integration+test documentation | mcp-code/architect | Validated test ecosystem+integrated CI/CD |

## Parameters
**PRE-PHASE**: Complete inventory+validation MANDATORY | **POST-PHASE**: Verification+comparison MANDATORY | **Scope**: Unit+integration+system+regression+performance | **Coverage**: ≥85% target | **Quality**: ≥95% pass rate | **Organization**: Thematic hierarchy (tests/unit|integration|system|regression|performance) | **Framework**: pytest+unittest+mock+fixtures | **Processing**: All tests together+context preservation | **Reports**: `/logs/tests_analysis_[phase]_[YYYY-MM-DD_HHMMSS].md`

## Execution: PRE-PHASE: INVENTORY→VALIDATION | Phases(0-10): Analysis(odd)→Implementation(even) | POST-PHASE: VERIFICATION→COMPARISON→COMPLETION

## Phase Operations

| Phase | Layer | Target | Commands |
|-------|-------|--------|----------|
| 0 | Inventory | Scan all tests+**detect unconsolidated**+categorize+map hierarchy+identify themes+detect duplication+map to code+**track origins** | scan_test_directory\|**detect_unconsolidated_tests**\|categorize_tests\|map_hierarchy\|identify_themes\|detect_duplicates\|map_tests_to_code\|**track_test_origins** |
| 1 | Coverage Analysis | Measure coverage+identify gaps+assess quality+detect low-value tests+**assess LLM-generated test quality** | analyze_coverage\|identify_untested_paths\|assess_quality\|detect_ineffective_tests\|**assess_llm_test_quality** |
| 2 | Coverage Implementation | Create unit tests+integration tests+setup fixtures+implement edge cases+**enhance LLM-generated tests** | create_unit_tests\|create_integration_tests\|setup_fixtures\|implement_edge_cases\|**enhance_llm_tests** |
| 3 | Organization Analysis | Analyze themes+validate hierarchy+detect duplication+identify misplaced tests+**auto-categorize unconsolidated**+**cluster similar tests** | analyze_thematic_org\|validate_hierarchy\|detect_duplicate_tests\|identify_misplaced\|**auto_categorize_unconsolidated**\|**cluster_similar_tests** |
| 4 | Organization Implementation | Reorganize by theme+move to correct category+merge duplicates+enforce naming+create suites+**consolidate unconsolidated**+**organize LLM-generated** | reorganize_by_theme\|move_tests\|merge_duplicates\|enforce_naming\|create_suites\|**consolidate_unconsolidated_tests**\|**organize_llm_generated** |
| 5 | Alignment Analysis | Validate against codebase+detect obsolete+identify broken imports+flag API changes+**validate LLM tests vs current code**+**detect misaligned assumptions** | validate_against_code\|detect_obsolete\|identify_broken_imports\|flag_api_changes\|**validate_llm_tests_vs_code**\|**detect_misaligned_assumptions** |
| 6 | Alignment Implementation | Remove obsolete+update imports+update for API changes+archive with reason+**fix LLM-generated misalignments**+**update test assumptions** | remove_obsolete\|update_imports\|update_for_api_changes\|archive_obsolete\|**fix_llm_misalignments**\|**update_assumptions** |
| 7 | Gap Analysis | Identify untested modules+missing test types+edge cases+regression tests+**identify redundant LLM tests**+**identify missing coverage** | identify_untested_modules\|detect_missing_types\|identify_edge_cases\|detect_missing_regression\|**identify_redundant_llm_tests**\|**identify_missing_coverage** |
| 8 | Gap Implementation | Create missing tests+diversify test types+create edge case tests+performance tests+**optimize LLM-generated tests**+**remove redundant LLM tests** | create_missing_tests\|create_integration_tests\|create_edge_cases\|create_performance_tests\|**optimize_llm_tests**\|**remove_redundant_llm_tests** |
| 9 | Validation Analysis | Execute suite+measure coverage/pass rate+analyze performance+assess CI/CD+**validate consolidated tests**+**measure optimization gains** | execute_suite\|measure_coverage\|measure_pass_rate\|analyze_performance\|assess_ci_cd\|**validate_consolidated**\|**measure_optimization** |
| 10 | Validation Implementation | Enforce gates+optimize tests+fix flaky tests+integrate CI/CD+document+**document consolidated structure**+**create test organization guide** | enforce_gates\|optimize_slow_tests\|fix_flaky_tests\|integrate_ci_cd\|document_tests\|**document_consolidated_structure**\|**create_organization_guide** |

## Test Hierarchy & Thematic Organization

| Type | Location | Scope | Current Status | Action |
|------|----------|-------|----------------|--------|
| Unit | `tests/unit/` | Function/method level (node_tree_presenter) | Minimal | Expand coverage |
| Integration | `tests/commander/integration/` | Component interaction (bstool_context_menu) | Moderate | Fill gaps |
| System | `tests/commander/system/` | E2E workflows (bstool_system, UI output) | Good | Maintain |
| Regression | `tests/commander/regression_*.py` | Change impact (load_nodes, select_root, telnet_tab) | Sparse | Create missing |
| Performance | Missing | Speed/resource benchmarks | **GAP** | **Create new** |
| Root-Level | `tests/test_*.py` | Mixed concerns - **DISORGANIZED** | Poor | **Reorganize** |
| **Unconsolidated** | **Any location** | **LLM-generated/ad-hoc tests** | **UNORGANIZED** | **AUTO-CONSOLIDATE** |

## 🔍 Automatic Test Categorization Logic

**IMPORT ANALYSIS**: `from src.` → unit test candidate | `import pytest` → pytest-based | `from unittest.mock import` → integration test candidate | `import requests|httpx` → system/API test | `from PyQt5|PyQt6` → GUI test | `import time|threading` → performance test candidate | **ASSERTION ANALYSIS**: Single function calls → unit | Multiple component interactions → integration | Full workflow → system | Known bug validation → regression | **SCOPE ANALYSIS**: Mocks >50% → unit | Real components → integration | External dependencies → system | Benchmark assertions → performance | **AUTO-ASSIGNMENT**: Unit → `tests/unit/[module]/` | Integration → `tests/integration/[theme]/` | System → `tests/system/[workflow]/` | Regression → `tests/regression/[bug_id_or_feature]/` | Performance → `tests/performance/[operation]/`

## 🎯 Intelligent Thematic Clustering

**SIMILARITY DETECTION**: Import overlap(>70%) → same theme | Module target overlap(>80%) → same theme | Function name patterns → same theme | Test naming patterns → same theme | **AUTO-CLUSTERING**: BsTool tests(test_bstool_*|bstool in imports) → `tests/themes/bstool/` | Token tests(token in name|token in imports) → `tests/themes/token_detection/` | Node tests(node in name|node in imports) → `tests/themes/node_management/` | Telnet tests(telnet in name|telnet in imports) → `tests/themes/telnet/` | Log tests(log in name|log in imports) → `tests/themes/log_management/` | SYS tests(sys_file|node_config in name) → `tests/themes/sys_file_parsing/` | **CONSOLIDATION RULES**: >3 tests same theme in different locations → consolidate | Duplicate test names → merge or rename | Similar test logic(>80% code similarity) → merge | Tests targeting same function → consolidate into single comprehensive test

## 📊 Test Quality Assessment Criteria

**QUALITY METRICS**: Has assertions(REQUIRED) | Has docstring(RECOMMENDED) | Has proper mocking(RECOMMENDED for integration) | Has fixtures(RECOMMENDED for shared setup) | Tests edge cases(RECOMMENDED) | Tests error conditions(RECOMMENDED) | Has meaningful test name(REQUIRED) | Proper categorization(REQUIRED) | **AUTO-ENHANCEMENT**: Add missing assertions | Add docstrings | Suggest mocking opportunities | Identify fixture candidates | Flag missing edge cases | Flag missing error handling | Rename generic test names | Move to proper category | **QUALITY SCORES**: Score 0-2: LOW(needs major enhancement) | Score 3-5: MEDIUM(needs improvement) | Score 6-8: GOOD(minor improvements) | Score 9-10: EXCELLENT(maintain)

## Thematic Clusters (Consolidation Required)

**BsTool** (`tests/commander/`): test_bstool_*+test_clear_subgroup_log_files*+regression(path_persistence|system_integration|UI_output) → ORGANIZED | **Token Detection** (SCATTERED): tests/test_token_detection*(4 files)+commander/(fbc|rpc|context_menu)_token* → **CONSOLIDATE** `tests/token_detection/` | **Node Management** (SCATTERED): tests/test_node_*+unit/test_node_tree_presenter+commander/test_node_*+regression_test_load_nodes → **CONSOLIDATE** `tests/node_management/` | **Telnet** (`tests/commander/`): test_telnet_*+regression(telnet_tab_visibility) → ORGANIZED | **Log Management** (SCATTERED+DUPLICATES): commander/test_log_*+test_rpc_log_path(ROOT+COMMANDER DUPLICATE) → **CONSOLIDATE** `tests/log_management/`+**REMOVE DUPLICATES** | **Commander Core** (`tests/commander/`): test_commander_window+test_command_execution+test_hierarchical_command_execution+test_button_*+test_clipboard_monitor+test_session_* → ORGANIZED | **SYS File** (SCATTERED): tests/test_sys_file_*+test_node_config_* → **CONSOLIDATE** `tests/sys_file_parsing/` | **Memory** (`tests/memory_optimization/`): test_memory_workflow → ORGANIZED | **Unconsolidated/LLM-Generated** (VARIOUS): **AUTO-DETECT→AUTO-CATEGORIZE→AUTO-CONSOLIDATE**

## 🔄 Dynamic Codebase-to-Test Mapping

**ADAPTIVE MAPPING**: Scan `src/` structure dynamically | Detect new modules automatically | Map tests to actual code (not static mapping) | Validate test relevance continuously | **CURRENT STATE**: `commander/` → `tests/commander/` ✓ | `utils/` → `tests/utils/` **GAP** | `gui*.py` → `tests/gui/` **GAP** | `generator.py|processor.py|log_creator.py` → `tests/core/` **GAP** | `node_config*.py` → `tests/node_config/` REORGANIZE | `sys_file_loader.py` → `tests/sys_file/` REORGANIZE | **FUTURE MODULES**: NEW_MODULE detected in `src/` → **AUTO-CREATE** `tests/NEW_MODULE/` + flag missing tests | **VALIDATION RULES**: Every `src/` module MUST have corresponding test directory | Every public function/class MUST have unit test | Every component interaction MUST have integration test | Every user workflow MUST have system test | **AUTO-GAP-DETECTION**: Scan `src/` modules→identify untested functions→flag for test creation | Scan `src/` classes→identify untested methods→flag for test creation | Scan `src/` workflows→identify untested paths→flag for system tests

## 🗑️ Obsolete Detection & Removal

**TRIGGERS**: Broken imports|References removed code|Tests deprecated functionality|Outdated API usage|Zero relevance(90d)|Duplicate(>80%)|Backup files(.bak)|Commented tests|Superseded versions|**LLM-generated tests for removed features**|**Tests with invalid assumptions** | **CANDIDATES**: test_previous_fix.py(VERIFY)|test_append_output.py+test_output.txt(VERIFY)|test_bstool_append vs commander/test_bstool_*(DUPLICATION)|test_qt_*(overlap?)|test_sys_file_parsing vs v2(CONSOLIDATE)|test_clear_subgroup_log_files*(v1|v2|.bak CONSOLIDATE)|*.bak files(REMOVE)|**Any unconsolidated LLM tests after consolidation** | **TRACKING**: Log execution+track failures+monitor import errors+metadata+**validate vs codebase**+**validate vs architecture**+**track LLM test origins** | **OPERATIONS**: Scan obsolete+validate imports+check code existence+**verify alignment**+archive+remove+**clean backups**+**consolidate LLM-generated**

## 🔄 Universal Test Processing Workflow

**STEP 1: DISCOVERY** → Scan ALL test files recursively | Identify unconsolidated tests(root-level, ad-hoc locations, generic names) | Track origins(manual, LLM-generated, auto-generated) | **STEP 2: ANALYSIS** → Analyze imports(determine type) | Analyze assertions(determine scope) | Analyze mocking(determine isolation) | Map to source code(determine theme) | Assess quality(score 0-10) | **STEP 3: CATEGORIZATION** → Auto-assign to type(unit/integration/system/regression/performance) | Auto-assign to theme(bstool/token/node/telnet/log/sys/etc) | Auto-assign to location(`tests/[type]/[theme]/`) | **STEP 4: CONSOLIDATION** → Group similar tests | Merge duplicates | Remove redundant | Enhance low-quality | **STEP 5: VALIDATION** → Validate against current codebase | Validate imports | Validate assumptions | Execute and measure | **STEP 6: ORGANIZATION** → Move to proper locations | Enforce naming conventions | Create suites | Document structure

## 📊 Analysis Reports
**Naming**: `tests_analysis_[phase]_[YYYY-MM-DD_HHMMSS].md` | **Location**: `/logs/` | **Content**: Phase results+commands+coverage metrics+organization details+obsolete candidates | **Usage**: Implementation phases reference reports | **Template**: `# Tests Analysis - [Date] ## Phase [X] **Tests**:[count] | **Coverage**:[%] | **Issues**:[count] | **Actions**:[list] ### Commands:[queue] ### Gaps:[list] ### Obsolete:[candidates]`

## Output Formats
**PRE-PHASE**: `INVENTORY|TOTAL:[count]|UNIT:[n]|INTEGRATION:[n]|SYSTEM:[n]|REGRESSION:[n]|PERFORMANCE:[n]|ORPHANED:[n]|**UNCONSOLIDATED:[n]**|**LLM_GENERATED:[n]**|OBSOLETE_CANDIDATES:[n]|THEMES:[list]|STATUS:[inventory_complete|reference_audit_complete|validation_complete]`

**POST-PHASE**: `VERIFICATION|INITIAL:[count]|FINAL:[count]|PROCESSED:[n]|ADDED:[n]|REMOVED:[n]|REORGANIZED:[n]|**CONSOLIDATED:[n]**|**UNCONSOLIDATED_REMAINING:[0]**|COVERAGE:[%]|PASS_RATE:[%]|STATUS:[comparison_complete|verification_complete]`

**Analysis**: `PHASE:[0-10/10]|LAYER:[Inventory|Coverage|Organization|Alignment|Gaps|Validation]|TARGET:[current→recommended]|ISSUE:[coverage_gap|quality_issue|missing_type|disorganized|duplicate|obsolete|broken_import|misplaced|untested_module|missing_integration|missing_regression|missing_performance|flaky|slow|**unconsolidated**|**llm_generated_low_quality**|**misaligned_assumption**]|ACTION:[scan|measure|create|reorganize|merge|remove|update|optimize|enforce|**consolidate**|**auto_categorize**|**enhance_quality**]|PRIORITY:[critical|high|medium|low]|**UNCONSOLIDATED_COUNT:[n]**|**QUALITY_SCORE:[0-10]**|REPORT:tests_analysis_[phase]_[date].md`

**Implementation**: `PHASE:[2-10/10]|LAYER:[Coverage|Organization|Alignment|Gaps|Validation]|TARGET:[current→compliant]|COMMAND:[specific]|STATUS:[planned|executing|completed]|IMPACT:[coverage_improved|tests_reorganized|obsolete_removed|gaps_filled|quality_enforced|**tests_consolidated**|**llm_tests_enhanced**|**assumptions_validated**]|METRICS:[coverage_%|pass_rate_%|added|removed|reorganized|**consolidated**|**quality_improved**]|REF:[analysis_report]`

## Metrics & Targets
| Metric | Target | Measurement | Validation |
|--------|--------|-------------|------------|
| Coverage | ≥85% | Line/branch analysis | pytest-cov |
| Pass Rate | ≥95% | Success ratio | pytest results |
| Organization | 100% hierarchical | Categorization compliance | Directory structure |
| Alignment | 100% synchronized | No obsolete tests | Import validation |
| Gaps | 0 critical | All paths tested | Coverage reports |
| Performance | No regression | Execution time | Test timing |
| Documentation | Complete | Test descriptions | README existence |
| **Consolidation** | **100% organized** | **Zero unconsolidated tests** | **Directory scan** |
| **Quality** | **≥7/10 average** | **Assertions+mocks+fixtures+docs** | **Quality scoring** |

## 📋 Test Organization Guide (Auto-Generated)

**STRUCTURE**: `tests/[type]/[theme]/test_[module]_[function].py` | **NAMING**: `test_[what_is_tested]_[scenario]_[expected_result]` | **EXAMPLES**: `tests/unit/token_detection/test_token_parser_valid_input_returns_tokens.py` | `tests/integration/bstool/test_bstool_service_copy_to_log_creates_file.py` | `tests/system/commander/test_commander_workflow_load_nodes_displays_tree.py` | **LLM-GENERATED TEST HANDLING**: Detect→Analyze→Categorize→Consolidate→Enhance→Validate→Organize | **QUALITY REQUIREMENTS**: Every test MUST have assertions | Every test SHOULD have docstring | Integration tests SHOULD use mocks | Tests SHOULD cover edge cases | Tests MUST have meaningful names | Tests MUST be in correct location

## Test Execution Patterns
**By Type**: `pytest tests/unit/ -v` | `pytest tests/commander/integration/ -v` | `pytest tests/commander/system/ -v` | `pytest tests/commander/regression_*.py -v` | `pytest tests/ --cov=src --cov-report=html --cov-report=term`

**By Theme**: `pytest tests/commander/test_bstool_*.py -v` | `pytest tests/token_detection/ -v` | `pytest tests/node_management/ -v` | `pytest tests/commander/test_telnet_*.py -v` | `pytest tests/log_management/ -v`

**Quick**: `pytest tests/commander/test_<module>.py -v` | `pytest --lf -v` (failed only) | `pytest --nf -v` (new only)

## MCP Integration
**PRE-PHASE**: Complete inventory+validation+**thematic clustering**+**unconsolidated detection**+**LLM test identification** MANDATORY | **POST-PHASE**: Verification+comparison+**coverage ≥85%**+**pass rate ≥95%**+**zero unconsolidated tests** MANDATORY | **Modes**: Analysis(0,1,3,5,7,9) mcp-analyze+reports | Implementation(2,4,6,8,10) mcp-code/architect+report refs | **Sequential**: Inventory(0)→Coverage→Organization→Alignment→Gaps→Validation | **Universal Processing**: Handles ANY test source(manual|LLM-generated|auto-generated) | **Auto-Operations**: Auto-detect unconsolidated→Auto-categorize by analysis→Auto-cluster by theme→Auto-enhance quality→Auto-validate vs codebase→Auto-consolidate to hierarchy | **Processing**: Complete inventory→**detect unconsolidated**→analyze all tests→**auto-categorize**→**auto-cluster**→assess quality→reorganize hierarchically→**consolidate unconsolidated**→align with codebase→**validate assumptions**→fill gaps→**enhance LLM tests**→enforce quality→final verification | **Framework**: pytest+pytest-cov+pytest-mock | **Quality Gates**: Automated threshold enforcement (≥85% coverage|≥95% pass rate|100% consolidated|≥7/10 quality) | **CI/CD**: Pipeline automation | **Execution**: All tests inventoried→**unconsolidated identified**→analyzed by import/assertion/scope→**auto-categorized**→**auto-clustered by theme**→quality assessed→reorganized hierarchically→aligned with codebase→gaps filled→quality enforced→**zero unconsolidated remaining**