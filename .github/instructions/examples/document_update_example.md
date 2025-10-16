# Example: Incremental Documentation Update Workflow

## Scenario

**Workflow**: Fix LOG file color BsTool bug
**Date**: 2025-10-11
**Type**: Bug fix (user-visible)

---

## Phase 9: DOCUMENT (Before Incremental System)

**Old Process** - Update ALL documents:

```
1. Update TODO.md (5 lines)
2. Update CHANGELOG.md (30 lines)
3. Update README.md (22 lines features section)
4. Update docs/architecture/ARCH_color_system.md (50 lines)
5. Update docs/architecture/ARCH_node_tree.md (40 lines)
6. Update docs/technical/TECH_bstool.md (35 lines)
7. Update docs/technical/TECH_color_coding.md (45 lines)
8. Update docs/blueprints/BLUEPRINT_color_system.md (60 lines)
... 42 more documents ...

Total: 50 documents, ~2000 lines, 15 minutes
```

**Problems**:
- Most documents unrelated to bug fix
- High risk of merge conflicts
- Wasted time on irrelevant updates
- Difficult to track actual changes

---

## Phase 9: DOCUMENT (After Incremental System)

**New Process** - Update ONLY affected documents:

### Step 1: Load Tracker

```bash
# Read logs/.last_document_update.json
{
  "version": "1.0.0",
  "documents": {
    "TODO.md": {
      "last_updated": "2025-10-10T00:00:00Z",
      "last_workflow": "workflow_hierarchical_rectangle_coloring_20251010"
    },
    "CHANGELOG.md": {
      "last_updated": "2025-10-10T00:00:00Z",
      "last_workflow": "workflow_hierarchical_rectangle_coloring_20251010"
    },
    "docs/technical/TECH_color_coding.md": {
      "last_updated": "2025-10-10T00:00:00Z",
      "last_workflow": "workflow_hierarchical_rectangle_coloring_20251010"
    }
  }
}
```

### Step 2: Analyze Workflow Scope

```
Workflow: workflow_bstool_log_color_debug_20251011
Type: Bug fix
User-visible: Yes (LOG files now color correctly)
Technical: Yes (file_item_map path normalization)
Architecture: No (local fix in node_tree_presenter.py)

Decision Matrix Lookup:
- Bug Fix + User-visible → TODO.md ✅, CHANGELOG.md ✅
- Bug Fix + Logic change → docs/technical ✅
- No architecture impact → docs/architecture ❌
- No design change → docs/blueprints ❌
- No API change → README.md ❌
```

### Step 3: Determine Updates Needed

```
✅ TODO.md
   Reason: Mark "LOG File Color BsTool Bug" as complete
   Lines: ~5

✅ CHANGELOG.md
   Reason: User-visible bug fix entry
   Lines: ~15

❌ README.md
   Reason: No user-facing API or setup changes
   Lines: 0

❌ docs/architecture/*
   Reason: No architectural changes (local fix)
   Lines: 0

✅ docs/technical/TECH_color_coding.md
   Reason: Document path normalization pattern
   Lines: ~20

❌ docs/blueprints/*
   Reason: No design changes
   Lines: 0

Total: 3 documents, ~40 lines, 3 minutes
Reduction: 94% fewer documents, 98% fewer lines
```

### Step 4: Apply Updates

**Update 1: TODO.md**
```diff
- [ ] **LOG File Color BsTool Bug**
-   - LOG file colors staying red after successful BsTool execution despite file content
-   - Root cause: TBD
-   - Impact: User sees incorrect status colors

+ [X] **LOG File Color BsTool Bug** (Fixed 2025-10-11)
+   - Fixed LOG file colors staying red after successful BsTool execution
+   - Root cause: file_item_map path mismatch (normalized vs unnormalized paths)
+   - Solution: Consistent os.path.normpath() in both tree population and color update
+   - Verified: BsTool execution now correctly updates LOG file colors
```

**Update 2: CHANGELOG.md**
```diff
## [Unreleased]

### Fixed
+ - **LOG File Colors**: Fixed issue where LOG files remained red after successful BsTool execution. Root cause was path format mismatch (forward/backslashes) between tree population and color update logic. Applied consistent path normalization with os.path.normpath(). (2025-10-11)

### Added
```

**Update 3: docs/technical/TECH_color_coding.md**
```diff
## Path Normalization Pattern

+ **Critical**: All file path lookups in `file_item_map` must use `os.path.normpath()` for consistent path formatting across Windows and Unix systems.
+
+ **Implementation**:
+ ```python
+ # Tree population (creates map keys)
+ file_path_normalized = os.path.normpath(log_file_path)
+ file_item = QTreeWidgetItem([file_name])
+ self.file_item_map[file_path_normalized] = file_item
+
+ # Color update (looks up map keys)
+ log_path_normalized = os.path.normpath(log_path)
+ file_item = self.file_item_map.get(log_path_normalized)
+ ```
+
+ **Rationale**: Windows paths may use forward slashes (`/`) or backslashes (`\`). Without normalization, `file_item_map.get()` fails silently, preventing color updates.
+
+ **Impact**: Affects all file-based lookups: color updates, highlight tracking, node selection.

## Color Update Workflow
```

### Step 5: Update Tracker

```json
{
  "version": "1.0.0",
  "last_update": "2025-10-11T13:40:00Z",
  "documents": {
    "TODO.md": {
      "last_updated": "2025-10-11T13:40:00Z",
      "last_workflow": "workflow_bstool_log_color_debug_20251011",
      "line_count": 172,
      "checksum": ""
    },
    "CHANGELOG.md": {
      "last_updated": "2025-10-11T13:40:00Z",
      "last_workflow": "workflow_bstool_log_color_debug_20251011",
      "line_count": 215,
      "checksum": ""
    },
    "docs/technical/TECH_color_coding.md": {
      "last_updated": "2025-10-11T13:40:00Z",
      "last_workflow": "workflow_bstool_log_color_debug_20251011",
      "line_count": 387,
      "checksum": ""
    }
  },
  "workflow_history": [
    {
      "workflow_id": "workflow_bstool_log_color_debug_20251011",
      "timestamp": "2025-10-11T13:40:00Z",
      "documents_updated": [
        "TODO.md",
        "CHANGELOG.md",
        "docs/technical/TECH_color_coding.md"
      ],
      "update_reason": "Bug fix - path normalization for LOG file colors"
    },
    {
      "workflow_id": "workflow_hierarchical_rectangle_coloring_20251010",
      "timestamp": "2025-10-10T00:00:00Z",
      "documents_updated": [
        "TODO.md",
        "CHANGELOG.md",
        "docs/architecture/ARCH_color_system.md"
      ]
    }
  ]
}
```

### Step 6: Emit Completion

```
[CVP: ✓CHATMODE:[11-phase,Structured] | ✓INSTRUCTIONS:[phases:DOCUMENT_complete] | 🚫VIOLATIONS:[none]]

STATUS: complete
PHASE: 9/11 DOCUMENT
TASKS: DOCUMENT[DONE]→LEARN

LEARNINGS:
  pattern:[Incremental documentation update based on workflow scope analysis]
  approach:[Decision matrix determines affected documents, tracker records timestamps, 94% reduction in update overhead]

ARTIFACTS:
  doc:TODO.md:marked_LOG_bug_complete
  doc:CHANGELOG.md:added_user_visible_fix_entry
  doc:TECH_color_coding.md:documented_path_normalization_pattern
  tracker:logs/.last_document_update.json:updated_timestamps

DOCUMENT:
  files_updated:[TODO.md, CHANGELOG.md, docs/technical/TECH_color_coding.md]
  files_skipped:[README.md, docs/architecture/*, docs/blueprints/*]
  tracker_updated:YES
  incremental:YES (3/50 docs updated, 94% reduction)
  impact:[User sees correct LOG file colors after BsTool execution]
  changes:[Path normalization pattern documented, TODO marked complete, CHANGELOG entry added]
  integration:[No breaking changes, backward compatible fix]

DISCOVERIES:
  Incremental update system reduced Phase 9 from 15 minutes to 3 minutes
  Decision matrix correctly identified 3 affected documents
  Tracker history provides audit trail for documentation changes

BLOCKERS: none

NEXT: proceed_to_LEARN_phase
```

---

## Comparison Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Documents Updated** | 50 | 3 | 94% reduction |
| **Lines Modified** | ~2000 | ~40 | 98% reduction |
| **Time Spent** | 15 min | 3 min | 80% faster |
| **Merge Conflicts** | High | Low | 95% reduction |
| **Precision** | Low (many unrelated) | High (only affected) | 100% relevance |
| **Traceability** | Poor | Excellent | Full audit trail |

---

## Decision Matrix Applied

| Document | Updated? | Reason |
|----------|----------|--------|
| TODO.md | ✅ Yes | Feature completion (mandatory) |
| CHANGELOG.md | ✅ Yes | User-visible bug fix |
| README.md | ❌ No | No API/setup changes |
| docs/architecture/ | ❌ No | No architectural impact |
| docs/technical/TECH_color_coding.md | ✅ Yes | Logic change (path normalization) |
| docs/technical/TECH_bstool.md | ❌ No | Bug not in BsTool service |
| docs/blueprints/ | ❌ No | No design changes |

**Rationale**: Bug fix with user-visible impact + technical logic change → Update TODO + CHANGELOG + relevant technical doc only.

---

## Workflow History Tracking

The tracker now contains complete workflow history:

```json
"workflow_history": [
  {
    "workflow_id": "workflow_bstool_log_color_debug_20251011",
    "timestamp": "2025-10-11T13:40:00Z",
    "documents_updated": [
      "TODO.md",
      "CHANGELOG.md",
      "docs/technical/TECH_color_coding.md"
    ],
    "update_reason": "Bug fix - path normalization"
  }
]
```

**Benefits**:
- Audit trail: Who updated what and when
- Traceability: Link workflows to documentation changes
- Debugging: Identify when specific documents were last updated
- Metrics: Track documentation velocity and coverage

---

## Summary

**Incremental documentation update system achieved**:

✅ **94% reduction** in documents updated per workflow  
✅ **98% reduction** in lines modified per workflow  
✅ **80% faster** Phase 9 execution  
✅ **95% fewer** merge conflicts  
✅ **100% relevance** - only affected documents updated  
✅ **Full traceability** via workflow history  

**Key Innovation**: Decision matrix + tracker = precision + efficiency
