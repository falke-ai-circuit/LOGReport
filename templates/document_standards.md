# 📝 | Type | Pattern | Location | Example | **Wiki Size** |
|------|---------|----------|---------|---------------|
| **ARCH** | `ARCH_[system].md` | `/docs/architecture/` | `ARCH_payment_system.md` | **800-1500 lines** |
| **BLUEPRINT** | `BLUEPRINT_[plan].md` | `/docs/blueprints/` | `BLUEPRINT_deployment.md` | **500-1000 lines** |
| **ROADMAP** | `ROADMAP_[scope].md` | `/docs/roadmaps/` | `ROADMAP_product_2025.md` | **600-1200 lines** |
| **TECH** | `TECH_[component].md` | `/docs/technical/` | `TECH_api_specs.md` | **1000-2000 lines** |
| **GUIDE** | `GUIDE_[feature].md` | `/docs/user/` | `GUIDE_auth_setup.md` | **500-1000 lines** |t Standar## 📚 Document-Specific Standards

| Type | **Wiki Structure (5-10 sections)** | Format Focus | Key Elements | **Consolidation From** |
|------|-----------|--------------|--------------|------------------------|
| **ARCH** | Overview → Architecture → Components → Design Decisions → Implementation → Performance → Best Practices → Troubleshooting → API Reference | Component tables + rationale + text diagrams + **comprehensive coverage** | System design, technical decisions, patterns, **consolidate all related architecture docs** | **9+ fragmented architecture docs → 1 comprehensive core** |
| **BLUEPRINT** | Overview → Objectives → Phases → Resources → Timeline → Metrics → Risks → Deliverables | Single table phases + compressed delivery + **detailed planning** | Planning, resources, deliverables, **consolidate related blueprints** | **5+ blueprint variants → 1 living plan** |
| **ROADMAP** | Vision → Strategy → Milestones → Timeline → Dependencies → Risks → Progress → Metrics | Timeline tables + tracking + inline objectives + **strategic depth** | Strategy, long-term vision, progress, **consolidate roadmap versions** | **3+ roadmap versions → 1 living roadmap** |
| **TECH** | Overview → Architecture → Specs → Configuration → API Reference → Examples → Troubleshooting → Performance → Security | Dense spec tables + code + compact configs + **comprehensive technical detail** | API specs, configurations, procedures, **consolidate all tech docs per component** | **7+ technical docs → 1 comprehensive reference** |
| **GUIDE** | Overview → Getting Started → Core Concepts → Step-by-Step Procedures → Advanced Usage → Tips & Best Practices → Troubleshooting → FAQ | Numbered procedures + inline tips + text descriptions + **complete user journey** | User workflows, features, practical guidance, **consolidate feature guides** | **6+ feature guides → 1 comprehensive user guide** |te

> **Purpose:** Standards for **wiki-style documentation**+naming+formatting+visual consistency+metadata tracking | **Format:** `[DocumentType]_[Subject].md` **(living docs, no version suffixes)** | **Audience:** Documentation writers | **Solves:** Inconsistent structure+poor naming+missing metadata+**fragmentation+duplication** | **Target**: **10-15 comprehensive core docs (500-2000 lines)+section-based navigation**

**Naming**: `[Type]_[Subject].md` **(NO version suffixes - living docs)** | **Versioning**: **Single living document (update in place, archive old versions if needed)** | **Subjects**: lowercase_with_underscores | **Extensions**: .md only | **SIZE**: **Comprehensive core docs (500-2000 lines)|Section-based (5-10 major sections)|Rich internal linking (80%+ #section links)** | **METADATA**: created_date|last_modified|last_accessed|word_count|reference_count|document_hash|obsolete_check_date|**section_count**|**internal_link_count** (AUTO-GENERATED+updated on access+used for obsolete detection+**wiki validation**) | **Template**: `metadata: {created_date: YYYY-MM-DD_HHMMSS, last_modified: YYYY-MM-DD_HHMMSS, last_accessed: YYYY-MM-DD_HHMMSS, word_count: int, reference_count: int, document_hash: "sha256", obsolete_check_date: YYYY-MM-DD_HHMMSS, section_count: int, internal_link_count: int}`
| Type | Pattern | Location | Example |
|------|---------|----------|---------|
| **ARCH** | `ARCH_[system]_[v].md` | `/docs/architecture/` | `ARCH_payment_system_v1.md` |
| **BLUEPRINT** | `BLUEPRINT_[plan]_[v].md` | `/docs/blueprints/` | `BLUEPRINT_deployment_v1.md` |
| **ROADMAP** | `ROADMAP_[scope]_[v].md` | `/docs/roadmaps/` | `ROADMAP_product_2025_v2.md` |
| **TECH** | `TECH_[component]_[v].md` | `/docs/technical/` | `TECH_api_specs_v1.md` |
| **GUIDE** | `GUIDE_[feature]_[v].md` | `/docs/user/` | `GUIDE_auth_setup_v1.md` |

## 🎯 Format Standards

**Wiki Organization**: **5-10 major sections per doc** | Section-based TOC at top | Deep hierarchical structure (H2→H3→H4) | **Rich internal linking (#section format)** | Comprehensive coverage (no shallow content <500 lines) | Living document (update in place, no version suffixes)

**Headers**: H1(`# Title` single per doc) | H2(`## Section` major **wiki navigation targets**) | H3(`### Subsection` detailed topics) | H4(`#### Detail` max depth) | **Section Links**: `[text](#section-name)` for internal navigation | **Cross-Doc Links**: `[text](Doc.md#section)` for wiki-style references | **Text**: Body(paragraphs) | Bold(`**key**` commands+filenames) | Code(`inline` technical terms) | Links(`[text](URL)` no raw URLs) | **Lists**: Bullets(`-` main, `  -` nested 2 spaces) | Numbered(`1. 2. 3.` sequences) | Mixed(combine when logical) | Spacing(single line) | Depth(max 2 levels) | **Tables**: Headers(always **bold**) | Alignment(left text, right numbers) | Spacing(blank line before/after) | Content(concise+abbreviations OK) | Complex(prefer tables) | **Code**: Inline(`code` commands+variables) | Blocks(```language` syntax highlighting) | Examples(concrete samples) | Output(show results)

**Visual**: Emojis(headers only: 📋 📝 🔧 ⚙️ 🎯 ✅ ❌ ⚠️ 🏗️ 📐 🗺️) | Separators(`---` major breaks) | Spacing(single between sections, double for major) | Line Length(80-100 chars) | Clean(no trailing spaces)

**Organization**: Flow(Title→Overview→Main→Examples→References) | Logical(group related) | Progressive(general first, details later) | Cross-Refs(link related docs) | Consistent(same type = same structure)

## 📚 Document-Specific Standards

| Type | Structure | Format Focus | Key Elements |
|------|-----------|--------------|--------------|
| **ARCH** | Overview → Components → Decisions → Implementation | Component tables + rationale + text diagrams | System design, technical decisions, patterns |
| **BLUEPRINT** | Objective → Phases → Resources → Timeline → Metrics | Single table phases + compressed delivery | Planning, resources, deliverables |
| **ROADMAP** | Vision → Milestones → Timeline → Dependencies → Risks | Timeline tables + tracking + inline objectives | Strategy, long-term vision, progress |
| **TECH** | Overview → Specs → Config → Examples → Troubleshooting | Dense spec tables + code + compact configs | API specs, configurations, procedures |
| **GUIDE** | Getting Started → Steps → Tips → FAQ | Numbered procedures + inline tips + text descriptions | User workflows, features, practical guidance |

## ✅ Format Examples

**Wiki TOC (Top of Document)**: `## Table of Contents` | `- [Overview](#overview)` | `- [Architecture](#architecture)` | `  - [Components](#components)` | `- [Configuration](#configuration)` | `- [API Reference](#api-reference)`

**Headers**: `# Main Title` | `## Primary Section` *(wiki navigation target)* | `### Subsection` | `#### Detail` | Regular text follows

**Internal Links**: `See [Architecture](#architecture) for details` | `Refer to [Configuration > Database](#database) section` | `Cross-doc: [Memory System](ARCH_memory_system.md#overview)`

**Lists**: `1. **Primary Step**: Description` | `   - Sub-requirement` | `   - Additional detail` | `2. **Next Step**: Continue`

**Tables**: `| Column Header | Data Type | Example |` | `| **Bold Header** | Description | \`code_example\` |` | `| Regular Entry | Details | Normal text |`

**Code**: **Command**: \`git commit -m "message"\` | **Config**: \`/path/to/config.yaml\` | **Variable**: \`DATABASE_URL=localhost\` | **Block**: \`\`\`bash\n# Multi-line\ncommand --option value\n\`\`\`

## 📊 Quality+Success

**Quality**: Consistency(same type=same structure/format) | Clarity(technical accuracy+accessible language) | Completeness(all necessary info+no redundancy) | **Comprehensiveness(500-2000 lines per core doc|5-10 major sections)** | Maintenance(**living documents - update in place, no version proliferation**) | **Wiki Navigation(80%+ section-based internal links)**

**Success**: Template Compliance(95%+follow standards) | **Wiki Consolidation(10-15 core docs total|70%+ archive rate)** | Search Efficiency(**60% faster with section-based navigation**) | Consistency Score(90%+structural similarity within types) | **Wiki Metrics(Section depth 5-10|Internal links 80%+|Duplication <5%)** | User Satisfaction(clear+navigable+**comprehensive coverage**)