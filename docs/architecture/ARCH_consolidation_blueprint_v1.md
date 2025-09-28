# Documentation Consolidation Blueprint

## 1. Taxonomy Structure
```plaintext
docs/
├── ARCHITECTURAL/        # System design and planning
│   ├── system_blueprints/  # High-level designs
│   ├── component_designs/  # Individual component specs
│   └── roadmaps/           # Implementation plans
├── USER/                 # Usage documentation
│   ├── guides/             # How-to guides
│   ├── references/         # Command/API references
│   └── troubleshooting/    # Problem resolution
└── TECHNICAL/            # Implementation details
    ├── apis/              # API documentation
    ├── testing/           # Test procedures
    └── internals/         # System internals
```

## 2. File Relocation Mapping
| Current Location | New Location | Type |
|------------------|--------------|------|
| docs/architecture/ | ARCHITECTURAL/component_designs/ | ARCHITECTURAL |
| docs/blueprints/ | ARCHITECTURAL/system_blueprints/ | ARCHITECTURAL |
| docs/roadmaps/ | ARCHITECTURAL/roadmaps/ | ARCHITECTURAL |
| docs/guides/ | USER/guides/ | USER |
| docs/api/ | TECHNICAL/apis/ | TECHNICAL |
| docs/testing/ | TECHNICAL/testing/ | TECHNICAL |
| docs/token_processing.md | ARCHITECTURAL/component_designs/token_management/ | ARCHITECTURAL |

## 3. Merge Logic
**Duplicate Resolution:**
- For `token_processing.md` duplicates:
  1. Compare both versions
  2. Preserve unique content
  3. Resolve conflicts by:
     - Preferring newer timestamps
     - Selecting more detailed sections
     - Manual arbitration if needed
  4. Save merged version in ARCHITECTURAL/component_designs/token_management/

**Standardization Rules:**
1. All filenames: lowercase_with_underscores
2. Section headers: Title Case
3. Metadata block at top: type, created, updated

## 4. Validation Checklist
- [ ] Content checksum verification
- [ ] Internal link validation
- [ ] Taxonomy compliance audit
- [ ] Broken link scan
- [ ] Accessibility test
- [ ] Version history preservation

## 5. Safety Measures
- Dry-run mode for all operations
- Pre-consolidation backup
- Atomic operations with rollback
- Progress logging with checkpointing