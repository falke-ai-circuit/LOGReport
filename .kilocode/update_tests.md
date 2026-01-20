# Update Tests Workflow

**Purpose**: Test optimization via analysis→implementation phases | **Modes**: Analysis (1-3): mcp-analyze | Implementation (4-6): mcp-code/mcp-architect | **Batch**: 5-8 test areas/cycle | **Target**: ≥85% coverage, ≥95% pass rate

## 6-Phase Architecture

| Phase | Type | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| 1 | Analysis | Test coverage assessment | mcp-analyze | Coverage gaps |
| 2 | Analysis | Test strategy evaluation | mcp-analyze | Quality opportunities |
| 3 | Analysis | Implementation planning | mcp-analyze | Test commands |
| 4 | Implementation | Test creation & structure | mcp-code/architect | Test suites |
| 5 | Implementation | Quality enforcement | mcp-code/architect | Validated tests |
| 6 | Implementation | Validation & integration | mcp-code/architect | Verified coverage |

## Parameters

**Scope**: Unit, integration, system testing ↔ performance validation | **Batch**: 5-8 test areas | **Coverage**: ≥85% target | **Quality**: ≥95% pass rate | **Types**: Functional, performance, regression | **Framework**: Project-specific test tools

## Execution Pattern

```bash
# Analysis Phase (mcp-analyze)
1-3: Assess → Evaluate → Plan

# Implementation Phase (mcp-code/mcp-architect)  
4-6: Create → Enforce → Validate
```

## Phase Details

### Phase 1: Test Coverage Assessment
**Scope**: Coverage gaps, test quality analysis, framework evaluation, test cleanup
```
BATCH_PROCESS(test_areas[5-8]):
→ Analyze current test coverage by module/component
→ Identify untested critical paths
→ Assess test quality and effectiveness
→ Map testing framework capabilities
→ Detect obsolete/redundant tests for removal
```

### Phase 2: Test Strategy Evaluation
**Scope**: Quality standards, testing approaches, performance criteria, test optimization
```
EVALUATION_CRITERIA:
→ Coverage targets (≥85% code coverage)
→ Pass rate standards (≥95% success)
→ Performance benchmarks (no regression)
→ Test maintainability and clarity
→ Redundant/outdated test identification
```

### Phase 3: Implementation Planning
**Scope**: Test prioritization, creation commands, validation strategy
```
PLANNING_OUTPUT:
→ Prioritized test creation batches
→ Test framework setup commands
→ Quality gate definitions
→ Validation checkpoint criteria
```

### Phase 4: Test Creation & Structure
**Scope**: Test suite creation, framework setup, structure organization, test cleanup
```
CREATION_COMMANDS:
create_test_suite(module, test_type)
setup_test_framework(project, requirements)
organize_test_structure(categories, hierarchy)
implement_test_cases(functionality, assertions)
remove_obsolete_tests(outdated_tests, validation_first)
```

### Phase 5: Quality Enforcement
**Scope**: Test execution, quality validation, performance verification, test optimization
```
QUALITY_COMMANDS:
execute_test_suite(test_batch, validation_mode)
measure_coverage(module, coverage_target)
validate_performance(test_results, benchmark_criteria)
enforce_quality_gates(test_metrics, standards)
optimize_test_efficiency(test_suite, remove_redundant)
```

### Phase 6: Validation & Integration
**Scope**: Coverage verification, integration testing, CI/CD integration
```
VALIDATION_COMMANDS:
validate_coverage_targets(project, minimum_thresholds)
test_integration_points(components, system_level)
verify_ci_integration(pipeline, automated_testing)
integration_test(test_ecosystem, comprehensive)
```

## Test Categories

| Type | Scope | Purpose | Tools |
|------|-------|---------|-------|
| Unit | Function/method level | Individual component validation | pytest, unittest, jest |
| Integration | Component interaction | Interface and data flow testing | pytest fixtures, mock |
| System | End-to-end workflows | Complete functionality validation | selenium, API testing |
| Performance | Speed/resource usage | Benchmark and regression testing | profiling, load testing |
| Regression | Change impact | Prevent functionality degradation | automated test suites |
| Security | Vulnerability testing | Security flaw identification | security scanners |

## Output Formats

**Analysis Phase (Phases 1-3)**:
```
PHASE_ID: [1-3/6] Analysis
BATCH_ID: [batch_number/total_batches]
TEST_AREA: [module_name → test_coverage_status]
ANALYSIS: [coverage_gap|quality_issue|performance_concern|missing_test_type]
RECOMMENDATION: [create_unit_tests|add_integration_tests|performance_tests|quality_improvement]
RATIONALE: [coverage_increase|quality_enhancement|performance_validation]
PRIORITY: [critical|high|medium|low]
IMPLEMENTATION_READINESS: [ready_for_execution|needs_refinement|requires_validation]
```

**Implementation Phase (Phases 4-6)**:
```
PHASE_ID: [4-6/6] Implementation  
BATCH_ID: [batch_number/total_batches]
TEST_AREA: [module_name → test_suite_created]
ACTION: [create_tests|execute_validation|measure_coverage|integrate_ci]
TEST_COMMAND: [specific test creation/execution command]
EXECUTION_STATUS: [planned|in_progress|completed|validated]
IMPACT: [coverage_improved|quality_enhanced|performance_verified]
VALIDATION: [tests_passing|coverage_target_met|performance_acceptable]
```

## Quality Metrics

| Metric | Target | Measurement | Validation |
|--------|--------|-------------|------------|
| Code Coverage | ≥85% | Line/branch coverage analysis | Automated coverage reports |
| Test Pass Rate | ≥95% | Test execution success ratio | CI/CD pipeline validation |
| Performance | No regression | Execution time comparison | Benchmark testing |
| Maintainability | High readability | Code quality metrics | Static analysis |
| Documentation | Complete test docs | Test description coverage | Manual review |

## MCP Integration

**Mode Separation**: Analysis phases (1-3) in mcp-analyze | Implementation phases (4-6) in mcp-code/architect | **Test Framework**: Project-specific tool integration | **Quality Gates**: Automated threshold enforcement | **CI/CD Integration**: Pipeline automation support | **Coverage Tracking**: Real-time metrics monitoring | **Batch Processing**: Context preservation via structured execution