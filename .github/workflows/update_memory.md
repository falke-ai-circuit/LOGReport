# Update Memory Workflow

**Purpose**: Memory hierarchy compliance via layer-by-layer analysis | **Focus**: Maximum entity condensation+similar entity merging+hierarchical connection creation+obsolete removal | **Global Strategy**: Distill project memory→universal patterns for cross-project reuse | **Modes**: Analysis(1-4,9-12) mcp-analyze | Implementation(5-8,13-16) mcp-code/architect | **Processing**: All entities at once | **Target**: Ultra-condensed+connected hierarchy+reusable patterns+obsolete-free

## 🔄 Dual-Cycle Architecture (Project → Global)

**PRE-PHASE: INVENTORY & VALIDATION** - MANDATORY first step before all phases:
1. **Complete Inventory**: List ALL existing entities|clusters|domains|types in current memory state | **Operations**: List all at each hierarchy level
2. **Connection Audit**: Identify disconnected memory entities | **Operations**: Find disconnected entities+audit entity-cluster connections+audit hierarchy completeness
3. **Pre-Validation**: Validate inventory completeness+connection integrity before starting Phase 1
4. **Inventory Context**: Maintain complete inventory for final verification after all phases complete

**POST-PHASE: INVENTORY VERIFICATION** - MANDATORY final step after all phases:
1. **Final Inventory**: Re-list ALL entities|clusters|domains|types after processing | **Operations**: List all at each hierarchy level
2. **Comparison**: Compare initial vs final inventory | **Operations**: Verify all items processed+none missed+changes documented
3. **Completion Validation**: Confirm complete coverage of initial inventory | **Operations**: 100% inventory coverage validation

**CLEANUP PHASE** - MANDATORY after PRE-PHASE, before Phase 1:
1. **Analyze Removal Candidates**: Run `python scripts/analyze_memory_cleanup.py` to identify removable entities
2. **Removal Categories**: 
   - **MemoryType entities** (organizational metadata, no workflow value) - **ALWAYS REMOVE**
   - **Cluster/Domain/Type meta entities** (hierarchy handled by relations, not entities) - **ALWAYS REMOVE**
   - **Generic documentation** (README/TODO extractions without unique insights) - **REMOVE**
   - **Low-value entities** (<2 observations OR all observations <25 chars) - **REMOVE**
   - **Obsolete entities** (no refs for 90+ days, outdated timestamps) - **REMOVE**
   - **Verbose entities** (>500 total chars) - **CONDENSE to 80-char max per observation**
   - **Disconnected entities** (no relations) - **REVIEW**: Keep if valuable standalone knowledge, remove if meta/organizational
3. **Automated Cleanup**: Phase 1 of unified_memory_optimizer.py handles condensation+removal
4. **Manual Review**: For disconnected entities, manually validate before removal
5. **Output**: Cleanup report documenting removed entities, reasons, backup location

**Cycle 1: Project Memory** (Phases 1-8): Entity compliance+aggressive condensation+**MANDATORY connection enforcement (Entity→Cluster→Domain→Type)**+metadata validation+obsolete removal+4-layer hierarchy enforcement+entity merging | **Cycle 2: Global Memory** (Phases 9-16): Universal pattern distillation+cross-project condensation+**MANDATORY connection enforcement (Entity→Cluster→Domain→Type)**+global metadata validation+non-universal obsolete removal+master hierarchy completion+pattern abstraction

| Phase | Layer | Project Objective (1-8) | Global Objective (9-16) | Mode | Output |
|-------|-------|-------------------------|-------------------------|------|--------|
| 1,9 | Entity | **CLEANUP: Remove meta entities (MemoryType|Cluster|Domain|Type organizational)|generic docs|low-value|obsolete** | Template compliance+condensation analysis+**entity→cluster connection validation**+metadata validation+obsolete detection(90d) | Pattern distillation analysis+global condensation+**entity→cluster connection validation**+metadata validation+non-universal obsolete detection(180d) | mcp-analyze | **Removal report: categories+counts+reasons** | Compliance gaps+condensation opportunities+**disconnected entities**+metadata issues+obsolete candidates \| Universal pattern opportunities+global condensation targets+**disconnected entities**+metadata gaps+non-universal patterns |
| 2,10 | Cluster | Entity grouping+**entity→cluster connection validation**+**cluster→domain connection validation**+cluster condensation+obsolete cluster detection(30d) | Universal cluster template analysis+**entity→cluster connection validation**+**cluster→domain connection validation**+global cluster condensation+obsolete global cluster detection(60d) | mcp-analyze | Cluster optimization+**unconnected entities**+**unconnected clusters**+condensed clusters+empty cluster removal \| Reusable cluster patterns+global cluster optimization+**connection validation**+universal templates |
| 3,11 | Domain | Cluster grouping+**cluster→domain connection validation**+**domain→type connection validation**+domain condensation+obsolete domain detection(60d) | Domain pattern library analysis+**cluster→domain connection validation**+**domain→type connection validation**+global domain condensation+obsolete global domain detection(90d) | mcp-analyze | Domain structure+**unconnected clusters**+**unconnected domains**+condensed domains+empty domain removal \| Universal domain structures+global domain optimization+**connection validation**+pattern libraries |
| 4,12 | Type | Domain grouping+**domain→type connection validation**+**complete chain validation (Entity→Cluster→Domain→Type)**+promotion readiness+type condensation+obsolete type detection(90d) | Architectural pattern analysis+**domain→type connection validation**+**complete chain validation (Entity→Cluster→Domain→Type)**+master hierarchy+global type condensation+obsolete global type detection(120d) | mcp-analyze | Type hierarchy+**unconnected domains**+**broken connection chains**+global candidates+condensed types+empty type removal \| Reusable architectural patterns+**connection chain validation**+master hierarchy+universal types |
| 5,13 | Entity | Template compliance+condensation implementation+**entity→cluster connection enforcement**+metadata creation+obsolete removal | Universal pattern implementation+abstraction+**entity→cluster connection enforcement**+global metadata creation+non-universal removal | mcp-code/architect | Condensed compliant entities+**all entities connected to clusters**+complete metadata+obsolete-free \| Context-agnostic reusable entities+**all entities connected to clusters**+global metadata+universal patterns |
| 6,14 | Cluster | Entity clustering+**entity→cluster connection enforcement**+**cluster→domain connection enforcement**+cluster condensation+obsolete cluster removal | Universal cluster template implementation+**entity→cluster connection enforcement**+**cluster→domain connection enforcement**+global cluster condensation+non-universal cluster removal | mcp-code/architect | **All entities connected to clusters**+**all clusters connected to domains**+condensed clusters+no empty clusters \| Cross-project cluster templates+**complete connections**+global clusters+universal groupings |
| 7,15 | Domain | Cluster domain+**cluster→domain connection enforcement**+**domain→type connection enforcement**+domain condensation+obsolete domain removal | Domain pattern library implementation+**cluster→domain connection enforcement**+**domain→type connection enforcement**+global domain condensation+non-universal domain removal | mcp-code/architect | **All clusters connected to domains**+**all domains connected to types**+condensed domains+no empty domains \| Universal domain pattern libraries+**complete connections**+global domains+cross-project structures |
| 8,16 | Type | Domain type+connection implementation+type condensation+obsolete type removal | Master architectural pattern implementation+global type condensation+non-universal type removal | mcp-code/architect | Connected complete project hierarchy+condensed types+no empty types \| Complete global hierarchy+reusable patterns+universal architectures |

## Parameters
**PRE-PHASE**: Complete inventory+validation MANDATORY before Phase 1 | **POST-PHASE**: Inventory verification+comparison MANDATORY after Phase 16 | **Template**: [MemoryType].[Domain].[SubCluster].[EntityType]_[Name] **ENFORCED at creation (reject non-compliant)** | **Processing**: All entities processed together | **Cycles**: Project(1-8)→Global(9-16) | **MANDATORY**: Entity→Cluster→Domain→Type (4-layer) + created_date|last_modified|last_accessed|reference_count|usage_count|hierarchy_path|content_hash|obsolete_check_date **(ALL 8 REQUIRED+ENFORCED if missing)** | **EntityType**: JSON field MUST match name suffix **ENFORCED** | **Operations**: Inventory→**CLEANUP**→Analyze(1-4,9-12)→Implement(5-8,13-16)→Verify | **Focus**: Complete inventory+**intelligent cleanup**+4-layer hierarchy+pattern distillation+metadata validation+final verification | **CONDENSATION**: **AGGRESSIVE 80 CHARS MAX** per entity observation | **MANDATORY: 6:1+ RATIOS** Entity:Cluster≥6:1 | Cluster:Domain≥6:1 | Domain:Type≥2:1 (Project Memory) **or** 3:1+ for Global Memory | Eliminate filler | Pipe separators | Ultra-compact | **CLEANUP**: **MANDATORY before Phase 1**: Remove MemoryType entities (organizational metadata)|Cluster/Domain/Type meta entities (hierarchy via relations)|Generic documentation (README/TODO extracts)|Low-value entities (<2 obs or <25 chars each)|Obsolete entities (no refs 90+d)|Verbose entities (>500 chars→condense) | **OBSOLETE**: Auto-detect+remove ALL LEVELS: No refs(90+d)|Duplicate(>80%)|Outdated timestamps|Zero usage|Broken connections|Invalid hierarchy | **Reports**: `/logs/memory_analysis_[cycle]_[YYYY-MM-DD_HHMMSS].md` | **UNIFIED TOOL**: `python scripts/unified_memory_optimizer.py [memory_file] [--target-ratio 6]`

## Execution Pattern
```bash
PRE-PHASE: INVENTORY→VALIDATION | CLEANUP: Analyze→Remove (meta entities|low-value|obsolete) | PROJECT(1-8): Analysis(1-4)→Report→Implementation(5-8)→Global promotion | GLOBAL(9-16): Analysis(9-12)→Report→Implementation(13-16)→Universal patterns | POST-PHASE: INVENTORY_VERIFICATION→COMPARISON→COMPLETION
```

## Phase Operations: Project(1-8) + Global(9-16)

| Phase | Layer | Project Analysis\|Implementation + Global Analysis\|Implementation | Commands |
|-------|-------|------------------------------------------------------------------|----------|
| 1,5\|9,13 | Entity | **CLEANUP (Phase 1 ONLY): Identify+remove meta entities|low-value|obsolete** \| Template compliance\|naming violations\|content quality\|4-layer hierarchy\|**MANDATORY: Validate entity→cluster connections**\|**AGGRESSIVE CONDENSATION (80 CHARS MAX)**\|entity merging\|filler elimination\|METADATA(ALL 8 REQUIRED)\|**TEMPLATE VALIDATION (reject non-[MemoryType].[Domain].[SubCluster].[EntityType]_[Name])**\|**ENTITYTYPE VALIDATION (suffix=field)**\|OBSOLETE(90d\|180d) \| Implementation: fixes\|standardization\|condensation\|merging\|4-layer assignment\|**MANDATORY: Connect unconnected entities→existing clusters OR if multiple unconnected entities with similarity→create new cluster+connect all**\|formatting\|metadata creation(ALL 8)\|obsolete removal | **identify_removable_entities**\|**remove_meta_entities**\|**remove_low_value**\|**remove_obsolete**\|**condense_verbose** \| rename+template_validate\|update_metadata+full_8_fields\|**condense_content_80_chars_max**\|merge_similar\|eliminate_filler\|validate_4layer\|assign_hierarchy\|**validate_template_format**\|**validate_entityType_match**\|**find_unconnected_entities**\|**validate_entity_cluster_connections**\|**connect_entity_to_cluster**\|**group_similar_unconnected_entities**\|**create_cluster_for_group**\|**connect_entities_to_new_cluster**\|validate_metadata+require_8_fields\|create_metadata+all_fields\|update_timestamps\|detect_obsolete\|archive_obsolete\|update_broken_refs \| Global: analyze_cross_project\|create_universal\|abstract_context\|create_reusable\|**condense_global_80_chars_max**\|validate_global_metadata+all_8\|detect_non_universal\|remove_project_specific |
| 2,6\|10,14 | Cluster | Misplaced entities\|overcrowded clusters\|**MANDATORY: Validate cluster→domain connections**\|entity→cluster validation\|hierarchy gaps\|**AGGRESSIVE CONDENSATION (80 CHARS MAX)**\|OBSOLETE CLUSTERS(30d\|60d) \| Implementation: creation\|assignment\|optimization\|**MANDATORY: Connect unconnected clusters→existing domains OR if multiple unconnected clusters with similarity→create new domain+connect all**\|validation\|condensation\|removal | move_entity\|create_cluster\|assign_entities_clusters\|create_entity_cluster_relations\|**find_unconnected_clusters**\|**validate_cluster_domain_connections**\|**connect_cluster_to_domain**\|**group_similar_unconnected_clusters**\|**create_domain_for_group**\|**connect_clusters_to_new_domain**\|**condense_cluster_80_chars**\|detect_obsolete_clusters\|remove_empty_clusters \| Global: analyze_cluster_patterns\|create_cluster_templates\|build_template_libraries\|establish_universal_connections\|**condense_global_cluster_80_chars**\|validate_global_cluster_metadata\|detect_non_universal_clusters\|remove_project_specific_clusters |
| 3,7\|11,15 | Domain | Misplaced clusters\|domain gaps\|**MANDATORY: Validate domain→type connections**\|cluster→domain validation\|hierarchy completion\|**AGGRESSIVE CONDENSATION (80 CHARS MAX)**\|OBSOLETE DOMAINS(60d\|90d) \| Implementation: creation\|assignment\|consolidation\|**MANDATORY: Connect unconnected domains→existing types OR if multiple unconnected domains with similarity→create new type+connect all**\|validation\|condensation\|removal | move_cluster\|create_domain\|assign_clusters_domains\|create_cluster_domain_relations\|**find_unconnected_domains**\|**validate_domain_type_connections**\|**connect_domain_to_type**\|**group_similar_unconnected_domains**\|**create_type_for_group**\|**connect_domains_to_new_type**\|**condense_domain_80_chars**\|detect_obsolete_domains\|remove_empty_domains \| Global: analyze_domain_patterns\|create_domain_libraries\|build_pattern_networks\|establish_universal_domain_relations\|**condense_global_domain_80_chars**\|validate_global_domain_metadata\|detect_non_universal_domains\|remove_project_specific_domains |
| 4,8\|12,16 | Type | Misplaced domains\|missing types\|**MANDATORY: Complete connection chain validation (Entity→Cluster→Domain→Type)**\|promotion candidates\|hierarchy validation\|**AGGRESSIVE CONDENSATION (80 CHARS MAX)**\|OBSOLETE TYPES(90d\|120d) \| Implementation: creation\|assignment\|**MANDATORY: Validate complete 4-layer connection chain+ensure no broken links**\|flagging\|condensation\|removal | move_domain\|create_memory_type\|assign_domains_types\|**validate_complete_connection_chain_entity_to_type**\|**repair_broken_connection_chains**\|**ensure_all_entities_have_complete_path_to_type**\|flag_promotion_candidates\|validate_complete_4layer\|**condense_type_80_chars**\|detect_obsolete_types\|remove_empty_types \| Global: analyze_architectural_patterns\|create_master_patterns\|complete_global_hierarchy\|establish_pattern_ecosystem\|**condense_global_type_80_chars**\|validate_global_type_metadata\|detect_non_universal_types\|remove_project_specific_types |

## Global Memory Processing
**Cycle 2 (9-16)**: Global memory = distilled repository of universal patterns from project memory for cross-project reuse | **Distillation**: Project-specific→Universal patterns | Implementation-specific→Reusable templates | Single-use→Multi-project applicable | Context-dependent→Context-agnostic patterns

## 📊 Analysis Report Generation
**Naming**: `memory_analysis_[cycle]_[YYYY-MM-DD_HHMMSS].md` | **Cycles**: project|global | **Location**: `/logs/` | **Content**: Phase results+command recommendations+hierarchy validation+all entity details+metadata status+obsolete findings | **Usage**: Implementation phases reference reports for execution guidance | **Template**: `# Memory Analysis Report - [Cycle] - [Date] ## Phase [X] Results **Entities**: [count] | **Issues**: [count] | **Actions**: [list] ### Commands: [implementation_commands] ### Hierarchy: [compliance_status] ### Metadata: [validation_results] ### Obsolete: [removal_candidates]`

## ️ MANDATORY 4-Layer Hierarchy Validation + Connection Enforcement + 6:1+ Ratios

**ENTITY TYPES**: Type→Domain→Cluster→Memory (4-layer) | **CONNECTION RULES**: Memory MUST→Cluster | Cluster MUST→Domain | Domain MUST→Type | **VALIDATION**: Before any creation/modification | **ENFORCEMENT**: Auto-assignment+connection creation if missing | **CRITICAL**: Many entities lack cluster connections

**MANDATORY CONNECTIONS**: Memory→Cluster | Cluster→Domain | Domain→Type | **VALIDATION**: Entity-cluster linkage+cluster-domain linkage+domain-type linkage

**MANDATORY RATIOS** (Project Memory): 
- **Entity:Cluster ≥ 6:1** (minimum 6 entities per cluster)
- **Cluster:Domain ≥ 6:1** (minimum 6 clusters per domain)  
- **Domain:Type ≥ 2:1** (minimum 2 domains per type)
- **Global Memory**: 3:1+ ratios acceptable for smaller corpus
- **SEMANTIC CLUSTERING**: Group by PURPOSE not naming patterns (e.g., Services≠Methods≠Tests)
- **AVOID OVER-CONSOLIDATION**: 20:1 ratios create "junk drawers" with 17+ entity types mixed

**CONNECTION ENFORCEMENT WORKFLOW** (MANDATORY every phase):
- **Phase 1 (Entity)**: Find unconnected entities→analyze similarity | Single: connect→existing cluster | Multiple similar: group→create new cluster→connect all | Validate entity→cluster complete | **TARGET: 6:1+ Entity:Cluster ratio**
- **Phase 2 (Cluster)**: Find unconnected clusters→analyze similarity | Single: connect→existing domain | Multiple similar: group→create new domain→connect all | Validate cluster→domain complete | **TARGET: 6:1+ Cluster:Domain ratio**
- **Phase 3 (Domain)**: Find unconnected domains→analyze similarity | Single: connect→existing type | Multiple similar: group→create new type→connect all | Validate domain→type complete | **TARGET: 2:1+ Domain:Type ratio**
- **Phase 4 (Type)**: Validate complete chain Entity→Cluster→Domain→Type ALL entities | Find+repair broken chains | Ensure 100% complete paths | Zero orphaned entities | **VALIDATE: All ratios meet targets**

**CONNECTION OPERATIONS**: Validate 4-layer+enforce complete hierarchy+auto-assign+**verify 6:1+ ratios** | Find disconnected entities+orphaned clusters+orphaned domains | Auto-connect all+create missing connections by type+**semantic clustering by purpose**
- Validate complete connection chain: Entity→Cluster→Domain→Type path
- Validate ratio targets: Entity:Cluster≥6:1 | Cluster:Domain≥6:1 | Domain:Type≥2:1

## 🗑️ Obsolete Detection+Removal (ALL LEVELS)
**TRIGGERS**: Entity: No refs(90d)|>80% similarity|broken hierarchy|zero usage(30d)|outdated(180d) | Cluster: Empty(30d)|duplicate names|no entities|broken connections | Domain: Empty(60d)|duplicate names|no clusters|broken connections | Type: Empty(90d)|duplicate names|no domains|redundancy | **GLOBAL TRIGGERS**: Entity(180d)|Cluster(60d)|Domain(90d)|Type(120d) + single-project usage+non-universal patterns | **TRACKING**: Log access with timestamp+log usage with action+track references+update timestamps | **OPERATIONS**: Scan obsolete at each level+validate integrity+check similarity(>80%)+archive with reason+remove obsolete items

## Output Formats
**PRE-PHASE Inventory**: `INVENTORY|TOTAL_ENTITIES:[count]|DISCONNECTED_ENTITIES:[count]|TOTAL_CLUSTERS:[count]|TOTAL_DOMAINS:[count]|TOTAL_TYPES:[count]|STATUS:[inventory_complete|connection_audit_complete|validation_complete]`

**POST-PHASE Verification**: `VERIFICATION|INITIAL_TOTAL:[count]|FINAL_TOTAL:[count]|PROCESSED:[count]|ADDED:[count]|REMOVED:[count]|MODIFIED:[count]|COVERAGE:[100%]|STATUS:[comparison_complete|verification_complete]`

**Analysis(1-4,9-12)**: `PHASE:[1-4/8|9-12/16]|CYCLE:[Project|Global]|LAYER:[Entity|Cluster|Domain|Type]|TARGET:[current→recommended]|ISSUE:[violation|misplaced|missing|incomplete_hierarchy|**disconnected**|**missing_connections**|uncondensed|similar_duplicate|unconnected|non_universal|missing_metadata|**template_violation**|**entityType_mismatch**|**observation_too_long**|obsolete_candidate]|ACTION:[move|create|rename|merge|condense|connect|**create_connections**|**enforce_connections**|**validate_template**|**validate_entityType**|**truncate_observation**|assign_hierarchy|abstract|distill|create_metadata|remove_obsolete]|PRIORITY:[critical|high|medium|low]|REPORT:memory_analysis_[cycle]_[date].md`

**Implementation(5-8,13-16)**: `PHASE:[5-8/8|13-16/16]|CYCLE:[Project|Global]|LAYER:[Entity|Cluster|Domain|Type]|TARGET:[current→compliant]|COMMAND:[memory.tool.command]|STATUS:[planned|executing|completed]|IMPACT:[compliance|organization|global_availability|condensation|4_layer_hierarchy_completion|**connection_enforcement**|**hierarchy_connections**|pattern_distillation|cross_project_reusability|universal_templates|metadata_completion|obsolete_removal]|REF:[analysis_report_file]`

## MCP Integration
**PRE-PHASE**: Complete inventory+validation before any MCP operations | **POST-PHASE**: Inventory verification+comparison after all operations | **Mode Separation**: Analysis(1-4,9-12) mcp-analyze+report generation | Implementation(5-8,13-16) mcp-code/architect+report reference | **Cycle Processing**: Project Memory(1-8)→Global Memory(9-16) | **Layer Processing**: Sequential Entity→Cluster→Domain→Type within each cycle | **Template Enforcement**: [MemoryType].[Domain].[SubCluster].[EntityType]_[Name] **REJECT non-compliant at creation** | **EntityType Enforcement**: JSON field=name suffix **REJECT mismatch** | **MANDATORY Hierarchy**: Complete 4-layer Entity→Cluster→Domain→Type path for ALL entities | **MANDATORY Metadata**: **ALL 8 REQUIRED** created_date|last_modified|last_accessed|reference_count|usage_count|hierarchy_path|content_hash|obsolete_check_date **REJECT if incomplete** | **Observation Length**: **AGGRESSIVE 80 CHARS MAX** | **MANDATORY Ratios**: Entity:Cluster≥6:1 | Cluster:Domain≥6:1 | Domain:Type≥2:1 (Project) or 3:1+ (Global) | **Report Management**: Analysis phases generate dated reports | Implementation phases reference analysis reports | **Content Optimization**: Project condensation+global pattern abstraction+aggressive 80 char targets | **Hierarchy Building**: Project connections+global pattern networks | **Pattern Distillation**: Universal pattern extraction for cross-project reuse | **Obsolete Management**: Deterministic removal based on usage metrics+time thresholds+similarity analysis | **Processing Model**: Complete inventory→all entities processed together+context preservation+hierarchy validation+**template validation**+**entityType validation**+metadata validation+**observation length validation**+**ratio validation**+obsolete detection+report generation/reference+final verification across both cycles

## 🛠️ Unified Memory Optimizer Tool

**RECOMMENDED APPROACH**: Use unified tool for complete 4-phase optimization pipeline

**Tool**: `scripts/unified_memory_optimizer.py`

**Features**:
- ✅ **4-Phase Pipeline**: Condensation→Hierarchy→Ratio Optimization→Validation
- ✅ **Auto-Detection**: Detects global vs project memory from filename
- ✅ **Configurable Ratios**: `--target-ratio` option (default 6.0 for project, 3.0 for global)
- ✅ **Automatic Backups**: Creates 4 backups per run in `backups/` directory
- ✅ **100% Connectivity**: Validates all Entity→Cluster→Domain→Type connections
- ✅ **Semantic Clustering**: Groups by purpose not naming patterns
- ✅ **Comprehensive Logging**: Timestamps, structured messages, final reports

**Usage Examples**:

```bash
# Project memory optimization (6:1 target ratio)
python scripts/unified_memory_optimizer.py project_memory.json

# Project memory with custom ratio
python scripts/unified_memory_optimizer.py project_memory.json --target-ratio 7

# Global memory optimization (3:1 target ratio)
python scripts/unified_memory_optimizer.py global_memory.json --target-ratio 3

# Global memory with higher ratio
python scripts/unified_memory_optimizer.py global_memory.json --target-ratio 6
```

**Phases Executed**:
1. **Phase 1 - Condensation**: Remove disconnected entities, condense observations to 80 chars
2. **Phase 2 - Hierarchy**: Build Entity→Cluster→Domain→Type structure with semantic grouping
3. **Phase 3 - Ratio Optimization**: Achieve target ratios (6:1+ for project, 3:1+ for global)
4. **Phase 4 - Validation**: Verify 100% connectivity and ratio compliance

**Output**: Final report with size evolution, ratio metrics, connectivity validation, backup locations

**Supporting Tools**:
- `scripts/validate_both_memories.py` - Comprehensive validation and reporting
- `scripts/analyze_cluster_precision.py` - Cluster quality analysis
- `scripts/final_summary.py` - Status reporting and comparison
