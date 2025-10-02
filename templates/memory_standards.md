# 🧠 Memory Standards Template

> **Purpose:** Standardized entity naming+hierarchical structuring | **Format:** `[MemoryType].[Domain].[SubCluster].[EntityType]_[Name]` | **Audience:** MCP developers | **Solves:** Chaotic naming+poor hierarchy

**MANDATORY 4-Layer Hierarchy**: Entity→Cluster→Domain→Type | **NO ORPHANS** | **VALIDATION**: Entity without 4-layer path = invalid | **METADATA**: created_date|last_modified|last_accessed|reference_count|usage_count|hierarchy_path|content_hash|obsolete_check_date (AUTO-GENERATED+updated on access+used for obsolete detection) | **Template**: `metadata: {created_date: YYYY-MM-DD_HHMMSS, last_modified: YYYY-MM-DD_HHMMSS, last_accessed: YYYY-MM-DD_HHMMSS, reference_count: int, usage_count: int, hierarchy_path: "Entity→Cluster→Domain→Type", content_hash: "sha256", obsolete_check_date: YYYY-MM-DD_HHMMSS}`

## 🏗️ Memory Types+Domains

**Types**: Project(App-specific|Current codebase|`Project.Frontend.UI.Component_NavBar`) | Pattern(Reusable solutions|Cross-project|`Pattern.Architecture.Layer_MVC`) | Tool(Dev utilities|Workflow support|`Tool.Debug.Inspector_LogParser`) | Config(Settings+configuration|Environment|`Config.Database.Connection_MySQL`)
| Memory | Domain | SubClusters | Entity Example |
|--------|--------|-------------|----------------|
| **Project** | Frontend | UI•State•Routing•Forms•API•Assets•Testing | `Project.Frontend.UI.Component_ResponsiveNavbar` |
| **Project** | Backend | API•Auth•Database•Business•Integration•Queue•Cache | `Project.Backend.API.Endpoint_UserAuth` |
| **Project** | DevOps | CI•Deploy•Monitor•Infra•Security•Backup•Logging | `Project.DevOps.CI.Pipeline_AutoTest` |
| **Project** | Architecture | Design•Performance•Scalability•Reliability•Migration•Documentation | `Project.Architecture.Design.Pattern_Layered` |
| **Project** | Data | Models•Migration•Query•Sync•Validation•Archive•Transform | `Project.Data.Models.Schema_UserProfile` |
| **Project** | Integration | External•Internal•Protocol•Transform•Webhook•Batch•Sync | `Project.Integration.External.Service_Payment` |
| **Pattern** | Architecture | Components•Layers•Services•Structures•Contracts•Interfaces | `Pattern.Architecture.Layer_PresentationMVC` |
| **Pattern** | Implementation | Code•Framework•Library•Tool•Integration•Optimization | `Pattern.Implementation.Queue_BackgroundProcessor` |
| **Pattern** | Process | Development•Testing•Deployment•Monitoring•Coordination•Optimization | `Pattern.Process.Development_FeatureBranching` |
| **Pattern** | Problem | Debug•Performance•Connection•Data•Security•Scaling•Recovery | `Pattern.Problem.Connection_RetryBackoff` |

## 🔧 Entity Types: Component(Reusable code|`Component_NavigationHeader`) | Service(Business logic|`Service_UserAuthentication`) | Tool(Dev utilities|`Tool_LogParser`) | Pattern(Design implementations|`Pattern_ObserverNotification`) | Config(Settings|`Config_DatabaseConnection`) | Script(Automation|`Script_DeploymentAutomation`) | Test(Testing frameworks|`Test_IntegrationSuite`) | Workflow(Process coordination|`Workflow_ReleaseManagement`) | Model(Data structures|`Model_UserProfile`) | Handler(Event processing|`Handler_AuthRequest`)

## 📝 Content+Connection Standards

**Format**: `[Core Function]: [Technical Detail] | [Context/Usage] | [Key Connections]` | **Length**: 80-120 chars | **Style**: Technical precision+no filler | **Links**: 2-4 connections | **Naming**: 3-25 chars PascalCase+clear purpose

**MANDATORY CONNECTIONS**: Entity→SubCluster→Domain→MemoryType (4-layer REQUIRED) | Horizontal(related entities same level) | Cross-Domain(entities across domains) | Pattern(Implementation→Pattern entities) | **VALIDATION**: No complete vertical path = invalid

**Relationships**: Dependency(`depends_on:[Service_Authentication]`) | Composition(`contains:[Component_A,Component_B]`) | Implementation(`implements:[Pattern_Observer]`) | Inheritance(`extends:[Component_BaseModal]`) | Association(`associates_with:[State_UserSession]`) | Hierarchical(`belongs_to:[SubCluster→Domain→MemoryType]`) | **Depth**: MANDATORY Min 4|Max 6|Optimal 4-5 levels

## ✅/❌ Examples

**Valid**: `Project.Frontend.UI.Component_ResponsiveNavigationHeader` | `Pattern.Architecture.Layer_PresentationMVCController` | `Project.Backend.API.Endpoint_UserAuthentication` | `Pattern.Problem.Connection_RetryWithExponentialBackoff`

**Invalid**: `navigation_component`(no hierarchy) | `some_auth_thing`(vague+no structure) | `Project.Thing.Stuff.Component_Whatever`(meaningless domains)

## 🚀 Implementation+Quality+Operations

**Phases**: 1(Template compliance+hierarchy analysis+domain mapping) | 2(Missing domain creation+orphan identification+connection planning) | 3(Entity transformation+relationship establishment+quality validation)

**Quality**: Naming(95%+template adherence) | **Hierarchy(100% entities MUST have 4-layer)** | Connection(90%+entities with 2+connections) | **Orphan(0 without complete Entity→Cluster→Domain→Type)** | Discoverability(85%+search success) | Reusability(3x pattern adoption) | Consistency(95%+standard adherence) | Connectivity(2.5+avg connections) | **Hierarchy Depth(MANDATORY 4.0 levels)**

**Operations**: Structure(`create_domains|create_subclusters|establish_hierarchy`) | Connectivity(`create_connections|map_relationships|validate_hierarchy`) | Quality(`validate_compliance|analyze_connectivity|optimize_structure`)

**Success**: Immediate(All entities follow template) | Short-term(50% search reduction) | Long-term(3x pattern reuse) | Quality(Zero orphans+optimal connectivity)