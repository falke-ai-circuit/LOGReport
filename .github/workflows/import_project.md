# Import Project Workflow

**Purpose**: External project onboarding into ecosystem | **Focus**: Auto-detect+structure+memory+codegraph+docs+tests | **Strategy**: Full automation+minimal user input+multi-language | **Architecture**: 11-phase interleaved | **Target**: Ecosystem-compliant project in ≤30min

**PRE-PHASE**: Scan repo→detect tech→validate structure | **POST-PHASE**: Validate structure+memory+codegraph+docs+tests→confirm readiness

## 11-Phase Architecture

| Phase | Type | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| PRE | Inventory | Scan+detect+validate | Manual | Inventory report |
| 1 | Analysis | Tech stack+dependencies | mcp-analyze | Tech report |
| 2 | Implementation | Directory structure+configs | mcp-code | Standard layout |
| 3 | Analysis | Codebase+modules+patterns | mcp-analyze | Code inventory |
| 4 | Implementation | Codegraph (<100KB) | mcp-code | codegraph.json |
| 5 | Analysis | Domain concepts+patterns | mcp-analyze | Knowledge map |
| 6 | Implementation | Memory files (empty project+global) | mcp-code | Memory JSON |
| 7 | Analysis | Documentation gaps | mcp-analyze | Doc plan |
| 8 | Implementation | Core docs (5-8 files) | mcp-code | Docs suite |
| 9 | Analysis | Test infrastructure | mcp-analyze | Test plan |
| 10 | Implementation | Test framework+examples | mcp-code | Test setup |
| POST | Validation | Compliance+readiness | Manual | Completion report |

## Parameters

**Input**: Repo path|URL+optional overrides | **Output**: Compliant project+memory+codegraph+docs+tests | **Languages**: Python|JS|TS|Java|C#|Go|Rust|Ruby (auto) | **Automation**: Full auto-detect+smart defaults | **Memory**: Empty project_memory (build during work)+transfer/create global_memory | **Docs**: 5-8 core only (expand via workflow) | **Tests**: Framework+structure+1-2 examples | **Time**: ≤30min (medium projects <50k LOC) | **Validation**: JSON+size+coverage+format compliance

## Execution Pattern

```
PRE→Tech(1)→Structure(2)→Code(3)→Codegraph(4)→Knowledge(5)→Memory(6)→DocPlan(7)→Docs(8)→TestPlan(9)→Tests(10)→POST
```

## Phase Operations

| Phase | Layer | Operations | Commands |
|-------|-------|------------|----------|
| PRE | Inventory | scan_repo\|detect_lang\|parse_deps\|identify_frameworks\|analyze_structure\|calc_metrics | scan\|detect\|parse\|analyze |
| 1 | Tech | parse_deps\|detect_versions\|map_arch\|detect_api_patterns\|identify_db | analyze_tech\|map_stack |
| 2 | Structure | create_dirs(src,docs,tests,config,scripts,logs,.github)\|copy_workflows\|setup_configs\|lang_specific_setup | create\|copy\|setup |
| 3 | Code | scan_modules\|extract_imports\|detect_patterns\|map_dependencies\|analyze_complexity | scan\|extract\|analyze |
| 4 | Codegraph | parse_ast\|extract_entities(Type→Domain→Module→Class)\|create_relations(BELONGS_TO,IMPORTS,INHERITS)\|optimize<100KB | parse\|extract\|optimize |
| 5 | Knowledge | identify_domain_concepts\|detect_arch_patterns\|recognize_tech_patterns\|categorize_knowledge | identify\|detect\|categorize |
| 6 | Memory | create_empty_project_memory\|transfer_global_memory\|validate_json\|validate_hierarchy | create\|transfer\|validate |
| 7 | Docs | assess_existing\|identify_gaps\|plan_core_docs(README+3-7)\|prioritize_actionable | assess\|plan\|prioritize |
| 8 | Docs | generate_readme\|create_arch_doc\|create_api_doc\|create_setup_guide\|apply_templates | generate\|create\|apply |
| 9 | Tests | detect_framework\|assess_coverage\|plan_minimal_suite\|identify_gaps | detect\|assess\|plan |
| 10 | Tests | install_framework\|create_structure(unit,integration,fixtures)\|create_examples\|config_coverage | install\|create\|config |
| POST | Validation | validate_all(structure,memory,codegraph,docs,tests)\|confirm_readiness\|generate_report | validate\|confirm\|report |

## Multi-Language Support

| Language | Detection | Package Mgr | Test Framework | Auto-Setup |
|----------|-----------|-------------|----------------|------------|
| Python | *.py+requirements.txt\|pyproject.toml | pip\|poetry | pytest+pytest-cov | pytest.ini,conftest.py,requirements-test.txt |
| JavaScript | *.js+package.json (no TS) | npm\|yarn | jest\|mocha | jest.config.js,test utils |
| TypeScript | *.ts+tsconfig.json | npm\|yarn | jest\|mocha | jest.config.js,ts-jest |
| Java | *.java+pom.xml\|build.gradle | maven\|gradle | junit 5 | pom.xml/build.gradle config |
| C# | *.cs+*.csproj\|*.sln | nuget\|dotnet | xUnit\|NUnit | test project+packages |
| Go | *.go+go.mod | go modules | go test | *_test.go structure |
| Rust | *.rs+Cargo.toml | cargo | cargo test | tests/ structure |
| Ruby | *.rb+Gemfile | bundler | RSpec | spec_helper,rspec config |

## Standard Directory Structure

```
project/
├── src/ (preserve existing+organize)
├── tests/ (unit,integration,fixtures,utils)
├── docs/ (architecture,technical,blueprints,analysis)
├── config/ (configs)
├── scripts/ (utilities)
├── logs/ (workflow reports)
├── templates/ (doc standards)
├── backups/ (memory backups)
├── .github/
│   ├── workflows/ (5 workflows)
│   ├── instructions/ (5 instruction files)
│   └── chatmodes/ (DevTeam.chatmode.md)
├── project_memory.json (EMPTY)
├── global_memory.json (transferred/minimal 10-15 entities)
├── codegraph.json (<100KB)
└── [lang-specific configs]
```

## Memory Strategy

**Project Memory**: EMPTY structure (0 entities)
```json
{
  "entities": [],
  "relations": [],
  "metadata": {"project_name":"[name]","created_date":"YYYY-MM-DD","entity_count":0,...}
}
```
**Rationale**: Build during actual work→accurate knowledge vs assumptions

**Global Memory**: Transfer existing OR create minimal (10-15 universal patterns)
- Core patterns: ServiceLayer,Repository,Factory,Singleton,Observer,Strategy
- Best practices: ErrorHandling,Logging,Validation
- 4-layer hierarchy: Type→Domain→Cluster→Entity
**Rationale**: Reusable patterns available immediately→cross-project consistency

## Codegraph Strategy

**Target**: <100KB (strict) | **Coverage**: ≥80% | **Hierarchy**: Type→Domain→Module→Class | **Relations**: BELONGS_TO,IMPORTS,INHERITS,IMPLEMENTS

**Format**:
```json
{"type":"entity","name":"Code.Module.user_service","entityType":"Module","observations":["User auth+profile mgmt","upd:2025-10-16,refs:0"]}
```

**Optimization**: Remove noise+functional descriptions only+80 chars max obs

## Documentation Strategy

**Initial**: 5-8 core docs
- README.md: overview+quickstart+structure+docs links
- ARCH_system_overview_v1.md: context+components+stack+flow
- API_reference_v1.md: endpoints+auth (if API)
- SETUP_guide_v1.md: prerequisites+install+config

**During Work**: Expand via update_documents workflow

**Constraints**: 500-2000 lines each+condensed format+actionable content

## Test Strategy

**Initial**: Framework+structure+1-2 examples
- Install lang-specific framework
- Create directory structure (unit,integration,fixtures)
- Config coverage reporting
- 1-2 sanity tests (demonstrates setup)

**During Work**: Generate tests via TDD/post-impl workflow

**Rationale**: Infrastructure enables testing→don't pre-test unknown code

## User Input

**Required**: Repository path|URL (REQUIRED)

**Optional**: Project name override|Global memory source (defaults: detect name, create minimal)

**Execution**:
```bash
# Fully automated
"Import project from /path/to/repo"

# With overrides
"Import project from /path/to/repo, project name 'MyApp', use existing global memory"

# Interactive (rare)
Detects ambiguity (e.g., multiple test frameworks) → asks preference → continues
```

## Validation Checklist

```
✅ STRUCTURE: dirs(src,docs,tests,config,scripts,logs,.github)+configs present
✅ MEMORY: project_memory(empty,valid)+global_memory(≥10 entities,4-layer)
✅ CODEGRAPH: <100KB+≥80% coverage+hierarchy valid+relations complete
✅ DOCS: README+≥3 docs+document_standards compliant
✅ TESTS: framework installed+structure created+≥1 test runs
✅ READY: memory loads+codegraph loads+workflows available
```

## Output Formats

**Inventory**: `INVENTORY|PROJECT:[name]|LANGUAGES:[detected]|FRAMEWORKS:[detected]|LOC:[count]|FILES:[count]|STATUS:complete`

**Analysis**: `PHASE:[1-10/11]|TYPE:Analysis|LAYER:[TechStack|Code|Knowledge|Docs|Tests]|STATUS:complete|FINDINGS:[count]|REPORT:[filename]`

**Implementation**: `PHASE:[2-10/11]|TYPE:Implementation|LAYER:[Structure|Codegraph|Memory|Docs|Tests]|FILES_CREATED:[count]|STATUS:complete`

**Verification**: `VERIFICATION|STRUCTURE:✅|MEMORY:✅|CODEGRAPH:✅|DOCS:✅|TESTS:✅|READY:YES|REPORT:[filename]`

**Completion**: `IMPORT_COMPLETE|PROJECT:[name]|DURATION:[min]|FILES:[count]|MEMORY:project=0,global=[count]|CODEGRAPH:[KB]|DOCS:[count]|TESTS:[count]|STATUS:ready`

## Success Criteria

✅ Structure+configs created | ✅ Memory valid (empty project+global) | ✅ Codegraph <100KB ≥80% | ✅ Docs 5-8 core compliant | ✅ Tests framework+examples | ✅ Validation passes | ✅ DevTeam ready | ✅ ≤30min import | ✅ ≤3 inputs

## Example Execution

```
USER: "Import project from D:\ExternalProject\awesome-api"

[PRE] Scanning→Python 3.11,FastAPI,pytest,8.5k LOC,62 files
INVENTORY|PROJECT:awesome-api|LANGUAGES:Python|FRAMEWORKS:FastAPI,pytest|LOC:8500|FILES:62|STATUS:complete

[1] Tech→FastAPI 0.104,SQLAlchemy,Pydantic,REST API,layered
PHASE:1/11|TYPE:Analysis|LAYER:TechStack|STATUS:complete|FINDINGS:24|REPORT:logs/import_tech_analysis_20251016.md

[2] Structure→docs,config,scripts,logs,.github,workflows,chatmodes
PHASE:2/11|TYPE:Implementation|LAYER:Structure|FILES_CREATED:47|STATUS:complete

[3] Code→12 routers,15 services,8 models,143 imports,37 endpoints
PHASE:3/11|TYPE:Analysis|LAYER:Code|STATUS:complete|FINDINGS:45|REPORT:logs/import_code_analysis_20251016.md

[4] Codegraph→45 modules,78 classes,234 functions,87KB,100% coverage
PHASE:4/11|TYPE:Implementation|LAYER:Codegraph|FILES_CREATED:1|STATUS:complete

[5] Knowledge→User/Auth/Project/Task,ServiceLayer,Repository,DI,JWT
PHASE:5/11|TYPE:Analysis|LAYER:Knowledge|STATUS:complete|FINDINGS:28|REPORT:logs/import_knowledge_20251016.md

[6] Memory→project(empty),global(15 patterns)
PHASE:6/11|TYPE:Implementation|LAYER:Memory|FILES_CREATED:2|STATUS:complete

[7] Docs→gaps:arch,API,setup→plan:4 core docs
PHASE:7/11|TYPE:Analysis|LAYER:Docs|STATUS:complete|FINDINGS:4|REPORT:logs/import_doc_plan_20251016.md

[8] Docs→README(updated),ARCH,API(37 endpoints),SETUP
PHASE:8/11|TYPE:Implementation|LAYER:Docs|FILES_CREATED:3|FILES_MODIFIED:1|STATUS:complete

[9] Tests→pytest detected,60% coverage→plan:config+examples
PHASE:9/11|TYPE:Analysis|LAYER:Tests|STATUS:complete|FINDINGS:3|REPORT:logs/import_test_plan_20251016.md

[10] Tests→pytest.ini,conftest.py,test_example.py,requirements-test.txt
PHASE:10/11|TYPE:Implementation|LAYER:Tests|FILES_CREATED:3|FILES_MODIFIED:1|STATUS:complete

[POST] ✅ Structure ✅ Memory(project=empty,global=15) ✅ Codegraph(87KB) ✅ Docs(4) ✅ Tests
VERIFICATION|STRUCTURE:✅|MEMORY:✅|CODEGRAPH:✅|DOCS:✅|TESTS:✅|READY:YES|REPORT:logs/import_completion_20251016.md

IMPORT_COMPLETE|PROJECT:awesome-api|DURATION:18min|FILES:58|MEMORY:project=0,global=15|CODEGRAPH:87KB|DOCS:4|TESTS:33|STATUS:ready

Next: Review docs→Start DevTeam→Build memory during work→Generate tests as needed→Expand docs via workflow
```

## Notes

**Philosophy**: Structure+foundation, NOT comprehensive documentation | Build knowledge during actual work

**Constraints**: Processing limits→essentials only | Token budget→automation over conversation | Time→≤30min medium projects

**Flexibility**: Multi-language auto-detect | Polyglot support | Framework auto-config | Architecture adaptation

**Integration**: Seamless transition to standard workflows | DevTeam operational immediately | All tooling available

**Maintenance**: Memory→update_memory | Codegraph→update_codegraph | Docs→update_documents | Tests→update_tests

