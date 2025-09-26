# 📝 Document Standards Template

> **Purpose:** Comprehensive standards for document naming, formatting, and visual consistency across all documentation | **Format:** `[DocumentType]_[Subject]_[Version].md` | **Audience:** Documentation writers | **Solves:** Inconsistent document structure + poor naming conventions

## 📋 Document Naming Standards
**Pattern:** `[DocumentType]_[Subject]_[Version].md` | **Versioning:** v1,v2,v3 | **Subjects:** lowercase_with_underscores | **Extensions:** .md only

### Standard Types
| Type | Pattern | Location | Example |
|------|---------|----------|---------|
| **ARCH** | `ARCH_[system]_[v].md` | `/docs/architecture/` | `ARCH_payment_system_v1.md` |
| **BLUEPRINT** | `BLUEPRINT_[plan]_[v].md` | `/docs/blueprints/` | `BLUEPRINT_deployment_v1.md` |
| **ROADMAP** | `ROADMAP_[scope]_[v].md` | `/docs/roadmaps/` | `ROADMAP_product_2025_v2.md` |
| **TECH** | `TECH_[component]_[v].md` | `/docs/technical/` | `TECH_api_specs_v1.md` |
| **GUIDE** | `GUIDE_[feature]_[v].md` | `/docs/user/` | `GUIDE_auth_setup_v1.md` |

## 🎯 Format Standards

### Typography Rules
**H1:** `# Document Title` single per doc | **H2:** `## Section Name` major sections | **H3:** `### Subsection` max 3 levels | **Body:** Regular paragraphs | **Bold:** `**key concepts**` commands, filenames | **Code:** `inline code` for technical terms | **Links:** `[descriptive text](URL)` no raw URLs

### Lists & Structure
**Bullets:** `-` dash for main, `  -` nested (2 spaces) | **Numbered:** `1. 2. 3.` for sequences | **Mixed:** Combine when logical | **Spacing:** Single line between items | **Depth:** Max 2 levels

### Tables & Data
**Headers:** Always include, **bold headers** | **Alignment:** Left text, right numbers | **Spacing:** Blank line before/after | **Content:** Concise, abbreviations OK | **Complex:** Prefer tables over paragraphs

### Code & Examples
**Inline:** `code` for commands, variables | **Blocks:** ````language` with syntax highlighting | **Examples:** Concrete, working samples | **Output:** Show expected results when relevant

### Visual Elements
**Emojis:** Headers only (📋 📝 🔧 ⚙️ 🎯 ✅ ❌ ⚠️ 🏗️ 📐 🗺️) | **Separators:** `---` for major breaks | **Spacing:** Single between sections, double for major | **Line Length:** 80-100 chars | **Clean:** No trailing spaces

### Content Organization
**Flow:** Title → Overview → Main Sections → Examples → References | **Logical:** Group related info | **Progressive:** General first, details later | **Cross-Refs:** Link related docs | **Consistent:** Same type = same structure

## 📚 Document-Specific Standards

| Type | Structure | Format Focus | Key Elements |
|------|-----------|--------------|--------------|
| **ARCH** | Overview → Components → Decisions → Implementation | Component tables + rationale + text diagrams | System design, technical decisions, patterns |
| **BLUEPRINT** | Objective → Phases → Resources → Timeline → Metrics | Single table phases + compressed delivery | Planning, resources, deliverables |
| **ROADMAP** | Vision → Milestones → Timeline → Dependencies → Risks | Timeline tables + tracking + inline objectives | Strategy, long-term vision, progress |
| **TECH** | Overview → Specs → Config → Examples → Troubleshooting | Dense spec tables + code + compact configs | API specs, configurations, procedures |
| **GUIDE** | Getting Started → Steps → Tips → FAQ | Numbered procedures + inline tips + text descriptions | User workflows, features, practical guidance |

## ✅ Format Examples

### Header Hierarchy
```markdown
# Main Document Title
## Primary Section  
### Subsection (if needed)
Regular paragraph text follows...
```

### List Standards
```markdown
1. **Primary Step**: Description of main action
   - Sub-requirement or detail
   - Additional consideration
2. **Next Step**: Continue sequence
```

### Table Format
```markdown
| Column Header | Data Type | Example |
|---------------|-----------|---------|
| **Bold Header** | Description | `code_example` |
| Regular Entry | Details | Normal text |
```

### Code Documentation
```markdown
**Command**: `git commit -m "message"`
**Config**: `/path/to/config.yaml` 
**Variable**: `DATABASE_URL=localhost`

```bash
# Multi-line code block
command --option value
another-command
```
```

## 📊 Quality Standards
**Consistency:** Same type = same structure/format | **Clarity:** Technical accuracy + accessible language | **Completeness:** All necessary info, no redundancy | **Maintenance:** Version updates for significant changes

### Success Metrics
**Template Compliance:** 95%+ documents follow standards | **Search Efficiency:** 40% faster document discovery | **Consistency Score:** 90%+ structural similarity within types | **User Satisfaction:** Clear, navigable documentation