# 📝 Document Standards Template

> **Purpose:** Standards for document naming+formatting+visual consistency+metadata tracking | **Format:** `[DocumentType]_[Subject]_[Version].md` | **Audience:** Documentation writers | **Solves:** Inconsistent structure+poor naming+missing metadata

**Naming**: `[Type]_[Subject]_[v].md` | **Versioning**: v1,v2,v3 | **Subjects**: lowercase_with_underscores | **Extensions**: .md only | **METADATA**: created_date|last_modified|last_accessed|word_count|reference_count|document_hash|obsolete_check_date (AUTO-GENERATED+updated on access+used for obsolete detection) | **Template**: `metadata: {created_date: YYYY-MM-DD_HHMMSS, last_modified: YYYY-MM-DD_HHMMSS, last_accessed: YYYY-MM-DD_HHMMSS, word_count: int, reference_count: int, document_hash: "sha256", obsolete_check_date: YYYY-MM-DD_HHMMSS}`
| Type | Pattern | Location | Example |
|------|---------|----------|---------|
| **ARCH** | `ARCH_[system]_[v].md` | `/docs/architecture/` | `ARCH_payment_system_v1.md` |
| **BLUEPRINT** | `BLUEPRINT_[plan]_[v].md` | `/docs/blueprints/` | `BLUEPRINT_deployment_v1.md` |
| **ROADMAP** | `ROADMAP_[scope]_[v].md` | `/docs/roadmaps/` | `ROADMAP_product_2025_v2.md` |
| **TECH** | `TECH_[component]_[v].md` | `/docs/technical/` | `TECH_api_specs_v1.md` |
| **GUIDE** | `GUIDE_[feature]_[v].md` | `/docs/user/` | `GUIDE_auth_setup_v1.md` |

## 🎯 Format Standards

**Headers**: H1(`# Title` single per doc) | H2(`## Section` major) | H3(`### Subsection` max 3 levels) | **Text**: Body(paragraphs) | Bold(`**key**` commands+filenames) | Code(`inline` technical terms) | Links(`[text](URL)` no raw URLs) | **Lists**: Bullets(`-` main, `  -` nested 2 spaces) | Numbered(`1. 2. 3.` sequences) | Mixed(combine when logical) | Spacing(single line) | Depth(max 2 levels) | **Tables**: Headers(always **bold**) | Alignment(left text, right numbers) | Spacing(blank line before/after) | Content(concise+abbreviations OK) | Complex(prefer tables) | **Code**: Inline(`code` commands+variables) | Blocks(```language` syntax highlighting) | Examples(concrete samples) | Output(show results)

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

**Headers**: `# Main Title` | `## Primary Section` | `### Subsection` | Regular text follows

**Lists**: `1. **Primary Step**: Description` | `   - Sub-requirement` | `   - Additional detail` | `2. **Next Step**: Continue`

**Tables**: `| Column Header | Data Type | Example |` | `| **Bold Header** | Description | \`code_example\` |` | `| Regular Entry | Details | Normal text |`

**Code**: **Command**: \`git commit -m "message"\` | **Config**: \`/path/to/config.yaml\` | **Variable**: \`DATABASE_URL=localhost\` | **Block**: \`\`\`bash\n# Multi-line\ncommand --option value\n\`\`\`

## 📊 Quality+Success

**Quality**: Consistency(same type=same structure/format) | Clarity(technical accuracy+accessible language) | Completeness(all necessary info+no redundancy) | Maintenance(version updates for significant changes)

**Success**: Template Compliance(95%+follow standards) | Search Efficiency(40% faster discovery) | Consistency Score(90%+structural similarity within types) | User Satisfaction(clear+navigable)