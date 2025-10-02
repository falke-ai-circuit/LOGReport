# 🧠 Memory Standards Template

> **Purpose:** Standardized entity naming + hierarchical structuring for consistent memory organization | **Format:** `[MemoryType].[Domain].[SubCluster].[EntityType]_[Name]` | **Audience:** MCP developers | **Solves:** Chaotic entity naming + poor hierarchical organization

## 📋 Overview
Memory entities require consistent hierarchical structuring for discoverability+reusability+relationships | Defines naming conventions+hierarchical rules+connection patterns | **MANDATORY METADATA**: All entities must have complete metadata for tracking+obsolete detection

### 🏛️ MANDATORY 4-Layer Hierarchy: Entity→Cluster(SubCluster)→Domain→Type(MemoryType) | **NO ORPHANS** | **VALIDATION**: Entity without 4-layer path = invalid

### 📊 MANDATORY Metadata: created_date|last_modified|last_accessed|reference_count|usage_count|hierarchy_path|content_hash|obsolete_check_date | **AUTO-GENERATED** by memory system | Updated on access/modification | Used for obsolete detection | **Template**: `metadata: {created_date: YYYY-MM-DD_HHMMSS, last_modified: YYYY-MM-DD_HHMMSS, last_accessed: YYYY-MM-DD_HHMMSS, reference_count: int, usage_count: int, hierarchy_path: "Entity→Cluster→Domain→Type", content_hash: "sha256", obsolete_check_date: YYYY-MM-DD_HHMMSS}`

## 🏗️ Hierarchical Structure

### Memory Types: Project(Application-specific entities|Current codebase|`Project.Frontend.UI.Component_NavBar`) | Pattern(Reusable design solutions|Cross-project|`Pattern.Architecture.Layer_MVC`) | Tool(Development utilities|Workflow support|`Tool.Debug.Inspector_LogParser`) | Config(Settings+configuration|Environment setup|`Config.Database.Connection_MySQL`)

### Domain Categories
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

## 🔧 Entity Types
| Type | Purpose | Naming Example |
|------|---------|----------------|
| **Component** | Reusable code units | `Component_NavigationHeader` |
| **Service** | Business logic services | `Service_UserAuthentication` |
| **Tool** | Development utilities | `Tool_LogParser` |
| **Pattern** | Design implementations | `Pattern_ObserverNotification` |
| **Config** | Settings + configuration | `Config_DatabaseConnection` |
| **Script** | Automation utilities | `Script_DeploymentAutomation` |
| **Test** | Testing frameworks | `Test_IntegrationSuite` |
| **Workflow** | Process coordination | `Workflow_ReleaseManagement` |
| **Model** | Data structures | `Model_UserProfile` |
| **Handler** | Event processing | `Handler_AuthRequest` |

## 📝 Content Standards
**Format:** `[Core Function]: [Technical Detail] | [Context/Usage] | [Key Connections]` | **Length:** 80-120 chars max | **Style:** Technical precision, no filler | **Links:** 2-4 meaningful connections | **Naming:** 3-25 chars PascalCase, clear purpose

### Hierarchical Connection Rules
**MANDATORY VERTICAL:** Entity → SubCluster → Domain → MemoryType (4-layer path REQUIRED for every entity) | **Horizontal:** Related entities same level | **Cross-Domain:** Entities across domains | **Pattern:** Implementation → Pattern entities | **Validation:** Entities without complete vertical path are invalid

## ✅/❌ Examples
```
✅ Project.Frontend.UI.Component_ResponsiveNavigationHeader
✅ Pattern.Architecture.Layer_PresentationMVCController  
✅ Project.Backend.API.Endpoint_UserAuthentication
✅ Pattern.Problem.Connection_RetryWithExponentialBackoff

❌ navigation_component (no hierarchy, unclear scope)
❌ some_auth_thing (vague naming, no structure)  
❌ Project.Thing.Stuff.Component_Whatever (meaningless domains)
```

## 🔗 Relationships: Dependency(`depends_on:[Service_Authentication]`) | Composition(`contains:[Component_A,Component_B]`) | Implementation(`implements:[Pattern_Observer]`) | Inheritance(`extends:[Component_BaseModal]`) | Association(`associates_with:[State_UserSession]`) | **Hierarchical(`belongs_to:[SubCluster→Domain→MemoryType]`)** | **Depth**: MANDATORY Min 4 levels | Max 6 levels | Optimal 4-5 levels

## 🚀 Implementation: Phase 1(Template compliance+hierarchy analysis+domain mapping) | Phase 2(Missing domain creation+orphan identification+connection planning) | Phase 3(Entity transformation+relationship establishment+quality validation)

## 📊 Quality Standards: Naming Compliance(95%+template adherence) | **Hierarchy Completeness(100% entities MUST have 4-layer hierarchy)** | Connection Coverage(90%+entities with 2+connections) | **Orphan Elimination(0 entities without complete Entity→Cluster→Domain→Type path)** | Validation Targets: Discoverability(85%+search success|Keyword testing) | Reusability(3x pattern adoption|Usage tracking) | Consistency(95%+standard adherence|Automated validation) | Connectivity(2.5+avg connections|Relationship analysis) | **Hierarchy(MANDATORY 4.0 levels|4-layer validation)**

## 🔧 Commands: Structure(`memory.create_domains(missing,template)|memory.create_subclusters(missing,mapping)|memory.establish_hierarchy(entities,format)`) | Connectivity(`memory.create_connections(orphans,targets)|memory.map_relationships(entities,types)|memory.validate_hierarchy(structure,rules)`) | Quality(`memory.validate_compliance(entities,standards)|memory.analyze_connectivity(graph,targets)|memory.optimize_structure(hierarchy,metrics)`)

## 📈 Success Metrics: Immediate(All entities follow template) | Short-term(50% search reduction) | Long-term(3x pattern reuse) | Quality(Zero orphans+optimal connectivity)