# Documentation Consolidation Blueprint

## Taxonomy
```plaintext
docs/
├── ARCHITECTURAL/
│   ├── system_blueprints/
│   ├── component_designs/
│   └── roadmaps/
├── USER/
│   ├── guides/
│   ├── references/
│   └── troubleshooting/
└── TECHNICAL/
    ├── apis/
    ├── testing/
    └── internals/
```

## Relocation Mapping
| Current | New | Type |
|--------|-----|------|
| docs/architecture/ | ARCHITECTURAL/component_designs/ | ARCH |
| docs/blueprints/ | ARCHITECTURAL/system_blueprints/ | ARCH |
| docs/roadmaps/ | ARCHITECTURAL/roadmaps/ | ARCH |
| docs/guides/ | USER/guides/ | USER |
| docs/api/ | TECHNICAL/apis/ | TECH |
| docs/testing/ | TECHNICAL/testing/ | TECH |
| docs/token_processing.md | ARCHITECTURAL/component_designs/token_management/ | ARCH |

## Merge Logic
| Duplicate | Resolution |
|----------|------------|
| token_processing.md | Compare versions; preserve unique; prefer newer/detailed; manual if needed; save merged |

## Standardization
- Filenames: lowercase_with_underscores
- Headers: Title Case
- Metadata: type, created, updated at top

## Validation Checklist
| Item | Status |
|------|--------|
| Content checksum | [ ] |
| Link validation | [ ] |
| Taxonomy audit | [ ] |
| Broken links | [ ] |
| Accessibility | [ ] |
| Version history | [ ] |

## Safety Measures
| Measure | Details |
|---------|---------|
| Dry-run | All ops |
| Backup | Pre-consolidation |
| Atomic | Rollback capable |
| Logging | Progress/checkpoints |