# Init Project Workflow

**Purpose**: Greenfield creation+ecosystem compliance from start | **Focus**: Interactive blueprint design→implementation | **Strategy**: Quality-first+blueprint-driven+guided | **Architecture**: 9-phase interleaved | **Target**: Production-ready compliant project+comprehensive blueprints in 45-90min

**PRE-PHASE**: Gather requirements→scope→goals→constraints | **POST-PHASE**: Validate compliance→completeness→DevTeam handoff

## 9-Phase Architecture

| Phase | Type | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| PRE | Discovery | Requirements+scope+goals | Interactive | Project brief |
| 1 | Design | System architecture | Interactive+mcp-architect | ARCH blueprint |
| 2 | Implementation | Structure+configs+memory | mcp-code | Standard layout |
| 3 | Design | Technical specs | Interactive+mcp-architect | TECH blueprint |
| 4 | Implementation | Core docs | mcp-code | Docs suite |
| 5 | Design | Implementation plan | Interactive+mcp-architect | IMPL blueprints |
| 6 | Implementation | Skeleton+boilerplate | mcp-code | Working foundation |
| 7 | Design | Test strategy | Interactive+mcp-architect | TEST blueprint |
| 8 | Implementation | Test infrastructure | mcp-code | Test suite |
| POST | Validation | Compliance+completeness | Manual | Handoff report |

## Parameters

**Input**: Concept+requirements+tech preferences (user choice) | **Output**: Compliant project+blueprints+docs+tests | **Languages**: Python|JS|TS|Java|C#|Go|Rust|Ruby | **Interaction**: Guided+collaborative+AI-assisted | **Memory**: Structured (10-20 project, 30-50 global entities) | **Docs**: Comprehensive blueprints (4 core)+standard docs (4-5) | **Tests**: Full infrastructure+strategy+initial tests | **Quality**: Blueprint-driven+compliance | **Time**: 45-90min (quality over speed)

## Execution Pattern

```
PRE→ARCH(1)→Structure(2)→TECH(3)→Docs(4)→IMPL(5)→Skeleton(6)→TEST(7)→Tests(8)→POST
```

## Phase Operations

| Phase | Layer | Operations | Commands |
|-------|-------|------------|----------|
| PRE | Discovery | gather_requirements\|define_scope\|establish_goals\|identify_constraints\|select_tech\|plan_arch | interview\|clarify\|document |
| 1 | ARCH | design_context\|define_components\|map_flow\|establish_patterns\|create_blueprint\|review | design\|diagram\|review |
| 2 | Structure | create_dirs(src,docs,tests,config,scripts,logs,.github)\|setup_workflows\|init_memory\|init_codegraph\|configs | create\|init\|configure |
| 3 | TECH | design_models\|define_apis\|specify_interfaces\|detail_decisions\|create_blueprint\|review | specify\|define\|review |
| 4 | Docs | generate_readme\|create_arch_docs\|create_tech_docs\|create_api_docs\|apply_standards\|cross_ref | generate\|document\|format |
| 5 | IMPL | plan_features\|design_modules\|create_roadmap\|define_milestones\|create_blueprints\|review | plan\|design\|review |
| 6 | Skeleton | create_entry_points\|generate_boilerplate\|setup_configs\|base_classes\|core_structure\|validate | scaffold\|generate\|implement |
| 7 | TEST | design_strategy\|plan_coverage\|define_patterns\|create_blueprint\|review | strategize\|plan\|review |
| 8 | Tests | install_framework\|create_structure\|generate_base_tests\|setup_ci\|config_coverage\|validate | setup\|generate\|configure |
| POST | Validation | validate_compliance\|verify_quality\|confirm_completeness\|test_workflows\|handoff | validate\|verify\|handoff |

## Multi-Language Support

| Language | Stack Options | Frameworks | Templates |
|----------|---------------|------------|-----------|
| Python | Web:Flask\|FastAPI\|Django / CLI:Click\|Typer / Data:Pandas\|NumPy | pytest+black+mypy+ruff | api\|cli\|pipeline\|ml |
| JavaScript | Frontend:React\|Vue\|Angular / Backend:Express\|Koa / Full:Next\|Nuxt | jest+eslint+prettier | spa\|ssr\|rest\|graphql |
| TypeScript | Frontend:React\|Vue\|Angular / Backend:NestJS\|Express / Full:Next | jest+eslint+prettier+tsc | enterprise\|microservice\|monorepo |
| Java | Spring\|Quarkus\|Micronaut / Android:Jetpack | junit+mockito+checkstyle | service\|microservice\|batch |
| C# | ASP.NET\|Blazor / Desktop:WPF\|MAUI | xUnit+Moq+StyleCop | api\|blazor\|desktop |
| Go | Web:Gin\|Echo\|Fiber / CLI:Cobra\|Urfave | go test+golangci-lint | microservice\|cli\|worker |
| Rust | Web:Actix\|Rocket / CLI:Clap | cargo test+clippy | service\|cli\|library |
| Ruby | Rails\|Sinatra\|Hanami | RSpec+Rubocop | web\|api\|gem |

## Interactive Blueprint Design

**Phase 1: Architecture** - System context→components→flow→integration→patterns→scale→security | Output: BLUEPRINT_architecture_v1.md (1000-2000 lines)

**Phase 3: Technical** - Data models→API design→business logic→dependencies→config→error handling | Output: BLUEPRINT_technical_v1.md (800-1500 lines)

**Phase 5: Implementation** - Feature breakdown→module design→phases→patterns→workflow | Output: BLUEPRINT_implementation_v1.md (600-1200 lines) + feature blueprints (300-600 lines)

**Phase 7: Testing** - Strategy→patterns→critical paths→test data→CI/CD | Output: BLUEPRINT_testing_v1.md (400-800 lines)

**Process**: AI creates→user reviews→iterative refinement→approval→implementation

## Standard Directory Structure

```
project/
├── src/ (or lib/,app/,pkg/ per language)
│   ├── main.* (entry point)
│   ├── models/,services/,controllers/,utils/,config/
├── tests/ (unit/,integration/,e2e/,fixtures/,utils/)
├── docs/ (architecture/,technical/,blueprints/,analysis/)
├── config/,scripts/,logs/,templates/,backups/
├── .github/ (workflows/,instructions/,chatmodes/)
├── project_memory.json,global_memory.json,codegraph.json
└── [lang-specific configs+dependencies]
```

## Memory Strategy

**Project Memory**: STRUCTURED 10-20 entities from blueprints
```json
{"entities":[
  {"type":"entity","name":"Project.Feature.UserAuth","entityType":"Feature","observations":["User auth+authorization system","JWT+OAuth2","upd:2025-10-16,refs:0"]},
  {"type":"entity","name":"Project.Component.APIGateway","entityType":"Component","observations":["REST gateway+routing","FastAPI","upd:2025-10-16,refs:0"]},
  {"type":"entity","name":"Project.Pattern.ServiceLayer","entityType":"ArchitecturalPattern","observations":["Business logic encapsulation","Separation concerns","upd:2025-10-16,refs:0"]}
],"relations":[{"type":"relation","from":"Project.Feature.UserAuth","to":"Project.Component.APIGateway","relationType":"IMPLEMENTED_IN"}]}
```
**Rationale**: Capture design decisions→structured knowledge from start

**Global Memory**: Full patterns (30-50 entities) - ServiceLayer,Repository,Factory,Observer,Strategy,CQRS,Singleton,Builder,Adapter,Decorator,Proxy,ErrorHandling,Logging,Validation,Security,Performance | **Rationale**: Complete library→guide implementation

## Codegraph Strategy

**Initial**: SKELETON foundation
```json
{"type":"entity","name":"Code.Module.main","entityType":"Module","observations":["Entry point+initialization","upd:2025-10-16,refs:0"]}
{"type":"entity","name":"Code.Module.config","entityType":"Module","observations":["Config mgmt+env vars","upd:2025-10-16,refs:0"]}
```
**Growth**: Update via update_codegraph | **Target**: <100KB | **Coverage**: 100% (tracked from start)

## Documentation Strategy

**Blueprints** (Phases 1,3,5,7): HIGH-QUALITY comprehensive
- BLUEPRINT_architecture_v1.md: System design (1000-2000 lines)
- BLUEPRINT_technical_v1.md: Specs (800-1500 lines)
- BLUEPRINT_implementation_v1.md: Plan (600-1200 lines)
- BLUEPRINT_testing_v1.md: Strategy (400-800 lines)
- Feature blueprints: As needed (300-600 lines)

**Standard Docs** (Phase 4): From blueprints
- README.md: Overview+quickstart (200-400 lines)
- ARCH_system_overview_v1.md: Architecture (500-1000 lines)
- TECH_[component]_v1.md: Technical (400-800 lines)
- API_reference_v1.md: API docs (300-600 lines)

**Rationale**: Blueprint-driven→quality planning→implementation follows design

## Test Strategy

**Blueprint** (Phase 7): Comprehensive design - Coverage targets (unit:80%+,integration:60%+,e2e:critical) | Patterns (AAA,BDD,table-driven,parametrized) | Mock strategy | Test data (fixtures,factories) | CI/CD (automated,gates)

**Implementation** (Phase 8): Full infrastructure - Framework+runners | Base classes+utils | Example tests per pattern | Coverage reporting | CI pipeline | Initial tests (entry,config,core)

**Rationale**: Test-ready from start→TDD-enabled→quality enforcement

## User Interaction

**Discovery** (PRE, 10-15min): AI→"Project type?" User→"REST API task mgmt" | AI→"Tech stack?" User→"Python+FastAPI" | AI→"Features?" User→"Auth,CRUD,collab,notify" | AI→"Scale?" User→"<1k→10k+" | AI→"Constraints?" User→"Slack API,PostgreSQL"

**Design** (1,3,5,7, 5-10min each): AI→"Components: [list], flow: [diagram], review: BLUEPRINT_*.md" | User→"Add caching layer" | AI→"Updated+Redis. Approve?" | User→"Yes" | AI→"Implementing..."

**Implementation** (2,4,6,8): AI→"Creating structure... ✓" | "Setting configs... ✓" | "Generating boilerplate... ✓" | "Validating... ✓"

## Validation Checklist

```
✅ BLUEPRINTS: 4 core (ARCH,TECH,IMPL,TEST) user-approved
✅ STRUCTURE: dirs(src,docs,tests,config,scripts,logs,.github)+configs
✅ MEMORY: project(10-20 entities)+global(30-50 patterns)+4-layer hierarchy
✅ CODEGRAPH: skeleton+foundation+valid hierarchy
✅ DOCS: README+ARCH+TECH+API+standards compliant
✅ SKELETON: runnable entry+core structure+configs working
✅ TESTS: framework+strategy+infrastructure+initial tests passing
✅ CI/CD: pipeline+quality gates+automated testing
✅ QUALITY: standards+linting+formatting+type checking configured
✅ READY: DevTeam operational+workflows available+blueprint-guided
```

## Output Formats

**Discovery**: `DISCOVERY|PROJECT:[name]|TYPE:[web_api|cli|etc]|STACK:[lang+framework]|FEATURES:[count]|SCALE:[target]|STATUS:complete`

**Design**: `PHASE:[1,3,5,7/9]|TYPE:Design|LAYER:[ARCH|TECH|IMPL|TEST]|BLUEPRINT:[filename]|STATUS:[drafting|reviewing|approved]`

**Implementation**: `PHASE:[2,4,6,8/9]|TYPE:Implementation|LAYER:[Structure|Docs|Skeleton|Tests]|FILES_CREATED:[count]|STATUS:complete`

**Verification**: `VERIFICATION|BLUEPRINTS:✅|STRUCTURE:✅|MEMORY:✅|DOCS:✅|SKELETON:✅|TESTS:✅|CI:✅|READY:YES`

**Completion**: `INIT_COMPLETE|PROJECT:[name]|DURATION:[min]|BLUEPRINTS:[count]|FILES:[count]|MEMORY:project=[N],global=[N]|TESTS:[count]|STATUS:ready`

## Success Criteria

✅ 4 blueprints (approved) | ✅ Structure+configs | ✅ Memory (10-20 project, 30-50 global) | ✅ Codegraph initialized | ✅ Docs (README+ARCH+TECH+API) | ✅ Runnable skeleton | ✅ Test infrastructure | ✅ CI/CD pipeline | ✅ Quality tooling | ✅ Blueprint-guided dev ready

## Example Execution

```
USER: "Create new project: Task Management API"

[PRE] Discovery→REST API,Python+FastAPI,5 features,10k scale
DISCOVERY|PROJECT:task-api|TYPE:web_api|STACK:Python+FastAPI|FEATURES:5|SCALE:10k|STATUS:complete

[1] ARCH→Gateway,Auth,Task,Notification services | Flow:Client→Gateway→Services→PostgreSQL | Patterns:Microservices-lite,ServiceLayer,Repository
AI: "Review: BLUEPRINT_architecture_v1.md" | USER: "Approved"
PHASE:1/9|TYPE:Design|LAYER:ARCH|BLUEPRINT:BLUEPRINT_architecture_v1.md|STATUS:approved

[2] Structure→src/,docs/,tests/,configs,workflows,memory,codegraph
PHASE:2/9|TYPE:Implementation|LAYER:Structure|FILES_CREATED:52|STATUS:complete

[3] TECH→Models:User,Task,Team,Notify | API:RESTful,JWT,25 endpoints | Deps:SQLAlchemy,Pydantic,Celery,Redis
AI: "Review: BLUEPRINT_technical_v1.md" | USER: "Add rate limiting" | AI: "Updated. Approve?" | USER: "Yes"
PHASE:3/9|TYPE:Design|LAYER:TECH|BLUEPRINT:BLUEPRINT_technical_v1.md|STATUS:approved

[4] Docs→README,ARCH_system_v1,TECH_data_models_v1,TECH_api_v1,API_reference_v1
PHASE:4/9|TYPE:Implementation|LAYER:Docs|FILES_CREATED:5|STATUS:complete

[5] IMPL→Phase1:Auth+Core,Phase2:Tasks+Teams,Phase3:Notifications | 15 modules,3 milestones
AI: "Review: BLUEPRINT_implementation_v1.md" | USER: "Approved"
PHASE:5/9|TYPE:Design|LAYER:IMPL|BLUEPRINT:BLUEPRINT_implementation_v1.md|STATUS:approved

[6] Skeleton→main.py,config.py,models/base.py,services/base.py,api/routes.py | Runnable:✓ server+health endpoint
PHASE:6/9|TYPE:Implementation|LAYER:Skeleton|FILES_CREATED:18|STATUS:complete

[7] TEST→TDD,unit:80%,integration:60%,e2e:critical | AAA+fixtures,mock external APIs,CI:pytest+coverage+gates
AI: "Review: BLUEPRINT_testing_v1.md" | USER: "Approved"
PHASE:7/9|TYPE:Design|LAYER:TEST|BLUEPRINT:BLUEPRINT_testing_v1.md|STATUS:approved

[8] Tests→pytest+pytest-cov+pytest-asyncio,test_main,test_config,test_health | Coverage:85% | CI:GitHub Actions
PHASE:8/9|TYPE:Implementation|LAYER:Tests|FILES_CREATED:12|STATUS:complete

[POST] ✅ Blueprints(4) ✅ Structure ✅ Memory(15,45) ✅ Docs(5) ✅ Skeleton ✅ Tests(3) ✅ CI
VERIFICATION|BLUEPRINTS:✅|STRUCTURE:✅|MEMORY:✅|DOCS:✅|SKELETON:✅|TESTS:✅|CI:✅|READY:YES

INIT_COMPLETE|PROJECT:task-api|DURATION:67min|BLUEPRINTS:4|FILES:87|MEMORY:project=15,global=45|TESTS:3|STATUS:ready

Next: Follow BLUEPRINT_implementation_v1.md→Implement via DevTeam→TDD+blueprint guidance→Update memory+codegraph+docs
```

## Notes

**Philosophy**: Blueprint-first→comprehensive planning→guided implementation | Ecosystem compliance from start

**vs import_project**: init=Greenfield+interactive+blueprints+structured | import=Onboarding+auto-detect+minimal+build-during-work

**Interaction**: Collaborative design→AI proposes+user refines→approval gates→quality focus

**Quality**: Blueprint-driven+comprehensive docs+full test strategy+CI/CD from start

**Maintenance**: Follow blueprints→Update during progress→Refine via update_documents→Evolve via DevTeam

