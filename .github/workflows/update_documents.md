# Update Documents Workflow

**Purpose**: Documentation com## \ud83d\uddd1\ufe0f Obsolete Detection+Removal

**TRIGGERS**: No refs(90d)|>80% similarity|outdated timestamps|zero usage|broken links|invalid format|deprecated content|orphaned sections|**codebase changed (code no longer matches docs)**|**architecture evolved (design docs incorrect)**|**functionality removed/changed (feature docs obsolete)**|**API changed (endpoint docs wrong)**|**config changed (setup docs invalid)**

**CODEBASE-DRIVEN OBSOLETE**: Detect docs referencing removed code|deprecated APIs|changed architecture|removed features|modified workflows|renamed components|deleted files|refactored modules | **VALIDATION**: Compare doc content vs current codebase state | **ACTION**: Remove if completely obsolete|Archive with migration notes|Flag for rewrite if partially salvageable

**TRACKING**: Log access+log usage+track references+update timestamps+**compare with codebase changes**+**validate against current architecture** | **OPERATIONS**: Scan obsolete documents+validate integrity+check similarity(>80%)+**verify codebase alignment**+**detect architecture mismatches**+archive with reason+remove obsolete itemsliance via interleaved analysis→implementation | **Focus**: Template compliance+condensation+merging+standardized naming+codebase alignment+**document_standards format consistency** | **Architecture**: 9-phase interleaved (1→2,3→4,5→6,7→8,9) | **Modes**: Analysis(odd) mcp-analyze | Implementation(even) mcp-code/architect | **Processing**: All documents at once | **Target**: Ultra-condensed compliant documentation+cross-references

**PRE-PHASE: INVENTORY & VALIDATION** (MANDATORY before all phases): 1.Complete Inventory(list ALL docs+scan workspace+inventory by category+**identify duplication clusters**) | 2.Reference Audit(identify orphaned docs+broken links+missing cross-refs+validate internal links+check reference completeness) | 3.Pre-Validation(validate inventory completeness+reference integrity+**calculate consolidation potential**) | 4.Inventory Context(maintain complete inventory for final verification+**track merge candidates**)

**POST-PHASE: INVENTORY VERIFICATION** (MANDATORY after all phases): 1.Final Inventory(re-list ALL docs+scan workspace+inventory by category) | 2.Comparison(compare initial vs final+verify all processed+none missed+changes documented) | 3.Completion Validation(confirm 100% inventory coverage)

## 10-Phase Architecture: **Consolidation(0)** | Template(1→2) | Content(3→4) | Naming(5→6) | Codebase(7→8) | Index(9)

| Phase | Layer | Objective | Mode | Output |
|-------|-------|-----------|------|--------|
| **0** | **Wiki Consolidation Planning** | **Topic clustering+merge planning+10:1 ratio strategy** | **mcp-analyze** | **Consolidation map+target core docs(10-15)** |
| 1 | Template Analysis | Template compliance+condensation analysis | mcp-analyze | Gaps+opportunities |
| 2 | Template Implementation | Template compliance+condensation fixes | mcp-code/architect | Condensed compliant docs |
| 3 | Content Analysis | **Aggressive merging+duplication clustering (10:1 ratio)** | mcp-analyze | **Wiki-style merge opportunities+core doc structure** |
| 4 | Content Implementation | **Wiki-style consolidation+section organization (500-2000 lines per core doc)** | mcp-code/architect | **10-15 comprehensive core docs+archived obsolete** |
| 5 | Naming Analysis | Filename+placement analysis | mcp-analyze | Naming violations+placement issues |
| 6 | Naming Implementation | Filename+placement fixes | mcp-code/architect | Named & placed docs |
| 7 | Codebase Analysis | Documentation vs codebase alignment analysis | mcp-analyze | Alignment gaps+coverage issues |
| 8 | Codebase Implementation | Documentation vs codebase alignment fixes | mcp-code/architect | Aligned comprehensive docs |
| 9 | Documentation Index | **Section-level index+#section links+navigation hierarchy** | mcp-code/architect | **Wiki-style index+section-based navigation** |

## Parameters
**PRE-PHASE**: Complete document inventory+validation MANDATORY before Phase 0 | **POST-PHASE**: Inventory verification+comparison MANDATORY after Phase 9 | **Coverage**: Comprehensive documentation ecosystem optimization | **Mode**: 10-phase interleaved analysis→implementation+ultra-condensed formatting+**wiki-style consolidation**+documentation index | **Compliance**: `/templates/document_standards.md` adherence | **Strategy**: **Wiki-style aggressive consolidation (10:1 merge ratio)**+maximum compression+document merging+standardized naming+**section-based navigation**+cross-document references | **CONSOLIDATION METRICS**: Core docs(10-15)|Archive rate(70%+)|Section depth(5-10 per doc)|Internal links(80%+ section-based)|Duplication(<5%)|Core doc size(500-2000 lines) | **CONDENSATION**: 60-80 chars per document | Eliminate filler | Pipe separators | Ultra-compact | **METADATA**: created_date|last_modified|last_accessed|word_count|reference_count|document_hash|obsolete_check_date (AUTO-GENERATED if missing) | **OBSOLETE**: Auto-detect+remove: No refs(90+d)|Duplicate(>80%)|Outdated timestamps|Zero usage|Broken links|Invalid format+**shallow content(<100 lines)**+**version proliferation (v1/v2/v3)** | **Reports**: `/logs/documents_analysis_[phase]_[YYYY-MM-DD_HHMMSS].md` | **Index**: **Section-level navigation+#section links**+cross-references | **MCP**: Interleaved mcp-analyze→mcp-code/architect | **Processing**: All documents together+context preservation | **Output**: **10-15 wiki-style core docs+section-based index**+ultra-condensed+document_standards compliance+cross-references

## Document Names: `[Type]_[Subject]_[Version].md` → `/docs/[category]/`

| Type | Pattern | Location | Example |
|------|---------|----------|----------|
| ARCH | `ARCH_[system]_[v].md` | `/docs/architecture/` | `ARCH_payment_system_v1.md` |
| API | `API_[service]_[v].md` | `/docs/technical/` | `API_user_service_v2.md` |
| PROC | `PROC_[process]_[v].md` | `/docs/blueprints/` | `PROC_deployment_guide_v1.md` |
| SPEC | `SPEC_[component]_[v].md` | `/docs/technical/` | `SPEC_database_schema_v3.md` |
| GUIDE | `GUIDE_[feature]_[v].md` | `/docs/user/` | `GUIDE_auth_setup_v1.md` |
| CONFIG | `CONFIG_[system]_[env].md` | `/docs/technical/` | `CONFIG_logging_production.md` |
| TROUBLE | `TROUBLE_[area]_[v].md` | `/docs/technical/` | `TROUBLE_network_issues_v1.md` |
| MEET | `MEET_[topic]_[YYYYMMDD].md` | `/docs/analysis/` | `MEET_sprint_planning_20250923.md` |
| ADR | `ADR_[decision]_[#].md` | `/docs/architecture/` | `ADR_database_choice_001.md` |
| RUN | `RUN_[procedure]_[v].md` | `/docs/blueprints/` | `RUN_backup_restore_v2.md` |

## Execution: PRE-PHASE: INVENTORY→VALIDATION+**DUPLICATION_CLUSTERING** | **Consolidation(0)** | Template(1→2) | Content(3→4) | Naming(5→6) | Codebase(7→8) | Index(9) | POST-PHASE: INVENTORY_VERIFICATION→COMPARISON→**WIKI_VALIDATION**→COMPLETION | Per-phase reports→ `/logs/documents_analysis_[phase]_[date].md`

## Phase Operations

| Phase | Layer | Target | Commands |
|-------|-------|--------|----------|
| **0** | **Wiki Consolidation Planning** | **Topic clustering: identify duplication clusters (9+ logging docs→1 core)\|group similar topics\|define 10-15 core doc structure\|calculate 10:1 merge ratio\|plan section organization** | **cluster_duplicate_topics\|identify_core_doc_candidates\|map_consolidation_strategy\|calculate_archive_targets(70%+)\|plan_section_hierarchy** |
| 1 | Template Analysis | Template compliance: ultra-condensed format\|structure adherence\|content density\|condensation opportunities\|**document_standards compliance** | analyze_template_compliance\|identify_condensation_opportunities\|validate_document_standards |
| 2 | Template Implementation | Compliance fixes: ultra_condensed_format\|template_structure\|content_compression\|**document_standards_format** | apply_template+ultra_condensed\|compress_content+max_density\|apply_document_standards+format_rules |
| 3 | Content Analysis | **Wiki-style aggressive merging: duplication clusters (10:1 ratio)\|topic consolidation\|section organization\|version unification (v1/v2/v3→single living doc)\|shallow content detection (<100 lines)** | **analyze_duplication_clusters\|identify_aggressive_merge_opportunities(10:1)\|detect_version_proliferation\|detect_shallow_content\|plan_wiki_core_docs(10-15)** |
| 4 | Content Implementation | **Wiki-style consolidation: aggressive merging (300+ docs→10-15 core)\|section-based organization (5-10 sections per core doc)\|archive obsolete (70%+ rate)\|convert to comprehensive format (500-2000 lines per core doc)** | **consolidate_to_core_docs+10:1_ratio\|merge_duplication_clusters\|organize_sections+hierarchy\|archive_obsolete+reason(70%+)\|convert_links_to_sections** |
| 5 | Naming Analysis | Naming standards: filename patterns\|placement rules\|category compliance\|naming violations\|**document_standards naming** | analyze_naming_compliance\|identify_placement_issues\|validate_naming_standards |
| 6 | Naming Implementation | Naming standardization: filename_compliance\|placement_enforcement\|directory_structure\|**document_standards_naming** | rename_document+standard_pattern\|move_document+target_location\|enforce_document_standards_naming+standards |
| 7 | Codebase Analysis | Codebase alignment: documentation coverage\|code-doc sync\|missing documentation\|**outdated references**\|**incorrect docs (codebase changed)**\|**obsolete architecture docs**\|**deprecated functionality docs** | analyze_coverage_gaps\|identify_sync_issues\|detect_outdated_references\|**detect_incorrect_docs_after_code_changes**\|**detect_architecture_mismatches**\|**detect_functionality_changes** |
| 8 | Codebase Implementation | Alignment implementation: coverage_completion\|reference_updates\|sync_maintenance\|**remove_incorrect_docs**\|**archive_obsolete_architecture_docs**\|**remove_deprecated_functionality_docs** | create_missing_docs+templates\|update_references+codebase\|sync_with_code+source\|**remove_docs_no_longer_applicable**\|**archive_obsolete_with_reason**\|**flag_for_rewrite_if_salvageable** |
| 9 | Documentation Index | **Section-level index creation\|#section links\|wiki-style navigation (Core Doc #Section)\|hierarchical structure (5-10 sections per doc)** | **create_section_level_index\|generate_section_links(#section_format)\|embed_wiki_navigation\|build_section_hierarchy\|convert_doc_links_to_section_links** |

## 📊 Analysis Report Generation
**Naming**: `documents_analysis_[YYYY-MM-DD_HHMMSS].md` | **Location**: `/logs/` | **Content**: Phase results+command recommendations+template compliance validation+document optimization details | **Usage**: Implementation phases reference reports for execution | **Template**: `# Documents Analysis Report - [Date] ## Phase [1-4] Results **Documents**: [count] | **Issues**: [count] | **Actions**: [list] ### Command Queue: [commands]`

## 🗑️ Obsolete Detection+Removal: No refs(90d)|>80% similarity|outdated timestamps|zero usage|broken links|invalid format|deprecated content|orphaned sections+**shallow content(<100 lines)**+**version proliferation(v1/v2/v3)**+**duplication clusters(9+ similar docs)** | **WIKI CONSOLIDATION TRIGGERS**: Multiple docs same topic(merge to 1 core)|Shallow content without depth(consolidate)|Version variants(unify to single living doc)|Duplicate content >80% (archive after merge) | **TRACKING**: Log access+log usage+track references+update timestamps+**track consolidation opportunities** | **OPERATIONS**: Scan obsolete documents+validate integrity+check similarity(>80%)+**identify consolidation clusters**+archive with reason+remove obsolete items+**archive post-consolidation (70%+ target)**

## 🔗 Document Relationships+Reference Validation

**Types**: Dependencies(doc A requires B)|Cross-references(internal links)|Navigation hierarchy(parent-child)|External references(links to code/resources) | **Validation**: Before any operations | **Enforcement**: Auto-repair broken links+create missing cross-references

**MANDATORY CHECKS**: Internal Links(validate cross-doc refs+check integrity+update broken) | Orphan Detection(find docs with no incoming refs+identify isolated) | Reference Chain(validate navigation paths+ensure hierarchy completeness) | Bidirectional Links(ensure referenced docs link back when appropriate)

**OPERATIONS**: Validate internal links+cross-references+navigation hierarchy completeness | Find orphaned docs+broken links+missing cross-refs at all levels | Auto-repair broken refs+create missing navigation links+establish doc relationships | Validate complete reference chain: Document→Section→Subsection→Topic path

**CRITICAL**: Many docs lack proper cross-refs+broken links common | **PRIORITY**: Repair all broken links+establish complete cross-ref network | **PROCESSING**: Process all reference repairs together | **VALIDATION**: Zero broken links+complete cross-ref coverage = compliant

## Output: 
**PRE-PHASE Inventory**: `INVENTORY|TOTAL_DOCUMENTS:[count]|ORPHANED_DOCUMENTS:[count]|BROKEN_LINKS:[count]|DOCUMENT_TYPES:[types_list]|STATUS:[inventory_complete|reference_audit_complete|validation_complete]`

**POST-PHASE Verification**: `VERIFICATION|INITIAL_TOTAL:[count]|FINAL_TOTAL:[count]|PROCESSED:[count]|ADDED:[count]|REMOVED:[count]|MODIFIED:[count]|COVERAGE:[100%]|**WIKI_METRICS:CORE_DOCS:[10-15]|ARCHIVE_RATE:[70%+]|SECTION_DEPTH:[5-10_per_doc]|INTERNAL_LINKS:[80%+_section_based]|DUPLICATION:[<5%]**|STATUS:[comparison_complete|**wiki_validation_complete**|verification_complete]`

**Analysis**: `PHASE:[0-9/10]|LAYER:[**Wiki_Consolidation**|Template|Content|Naming|Codebase|Index]|TARGET:[current→recommended]|ISSUE:[non_compliant|uncondensed|duplicate|misnamed|misplaced|unaligned|format_violation|missing_metadata|obsolete_candidate|**broken_links**|**missing_references**|**orphaned_doc**|**shallow_content**|**version_proliferation**|**duplication_cluster**|**missing_sections**]|ACTION:[condense|merge|rename|move|create|align|format_standardize|create_metadata|remove_obsolete|**repair_links**|**create_references**|**establish_navigation**|**consolidate_to_core**|**archive_obsolete(70%+)**|**organize_sections**|**convert_to_section_links**]|PRIORITY:[critical|high|medium|low]|REPORT:documents_analysis_[phase]_[date].md` | **Implementation**: `PHASE:[0,2,4,6,8,9/10]|LAYER:[**Wiki_Consolidation**|Template|Content|Naming|Codebase|Index]|TARGET:[current→compliant]|COMMAND:[specific_command]|STATUS:[planned|executing|completed]|IMPACT:[compliance|optimization|standards|alignment|consistency|metadata_completion|obsolete_removal|**reference_repair**|**cross_reference_completion**|**navigation_establishment**|**wiki_consolidation**|**section_organization**]|REF:[analysis_report]`

## MCP Integration
**PRE-PHASE**: Complete inventory+validation+**duplication clustering** before any MCP operations | **POST-PHASE**: Inventory verification+comparison+**wiki validation (10-15 core docs|70%+ archive|section-based navigation)** after all operations | **Modes**: Analysis(**0**,1,3,5,7,9) mcp-analyze+report generation | Implementation(2,4,6,8,9) mcp-code/architect+report reference | **Sequential**: **Wiki_Consolidation(0)→**Template→Content→Naming→Codebase→Index | **Compliance**: **Wiki-style consolidation (10:1 merge ratio)**+ultra-condensed format+maximum compression+**aggressive document merging (300+→10-15)**+standardized patterns+proper placement+documentation-code sync+document_standards via `/templates/document_standards.md` | **MANDATORY**: Metadata(auto-generated+validated+tracked)+**wiki metrics (core docs|archive rate|section depth|internal links|duplication)** | **Obsolete**: Deterministic removal+archiving+**70%+ post-consolidation archive target** | **Processing**: Complete inventory→**consolidation planning**→all docs together+context preservation+metadata validation+obsolete detection+**wiki consolidation**+report generation/reference+**wiki validation**+final verification
