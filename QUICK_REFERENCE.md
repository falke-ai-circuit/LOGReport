# Memory Optimization - Quick Reference Card

## 🚀 One-Command Optimization

```bash
# Project memory (6:1 ratios)
python scripts/unified_memory_optimizer.py project_memory.json

# Global memory (3:1 ratios)
python scripts/unified_memory_optimizer.py global_memory.json --target-ratio 3
```

## 📋 Mandatory Requirements

| Requirement | Project Memory | Global Memory |
|------------|----------------|---------------|
| **Hierarchy** | Entity→Cluster→Domain→Type (4-layer) | Entity→Cluster→Domain→Type (4-layer) |
| **Ratios** | Entity:Cluster ≥6:1, Cluster:Domain ≥6:1, Domain:Type ≥2:1 | Entity:Cluster ≥3:1, Cluster:Domain ≥3:1, Domain:Type ≥2:1 |
| **Condensation** | 80 chars MAX per observation | 80 chars MAX per observation |
| **Connectivity** | 100% (all entities connected) | 100% (all entities connected) |
| **Clustering** | Semantic by PURPOSE | Pattern-based universal |

## ✅ Validation Commands

```bash
# Full validation
python scripts/validate_both_memories.py

# Cluster quality check
python scripts/analyze_cluster_precision.py

# Quick status
python scripts/final_summary.py
```

## 📊 Current Status

### Project Memory
- **Size**: 74.24 KB (from 165.09 KB, -55%)
- **Ratios**: 7.3:1 | 11.0:1 | 2.0:1 ✅
- **Connectivity**: 100% ✅
- **Clusters**: 22 semantic clusters

### Global Memory
- **Size**: 27.23 KB (from 84.26 KB, -68%)
- **Ratios**: 3.3:1 | 2.6:1 | 2.5:1 ✅
- **Connectivity**: 100% ✅
- **Clusters**: 13 pattern-based clusters

## 🎯 Key Principles

1. **6:1 > 20:1** - Semantic precision beats aggressive consolidation
2. **Group by PURPOSE** - Services≠Methods≠Tests (not just "implementation")
3. **80 char limit** - Aggressive condensation with 22+ abbreviations
4. **100% connectivity** - No orphaned entities at any level
5. **Semantic clustering** - Clear purpose for each cluster

## 🔧 Common Tasks

### When to Re-optimize
- Memory exceeds size targets (100KB project, 40KB global)
- Connectivity drops below 95%
- Ratios drop below targets
- New patterns emerge

### After Manual Changes
```bash
python scripts/unified_memory_optimizer.py [file] --target-ratio [N]
python scripts/validate_both_memories.py
```

## 📁 Important Locations

| Item | Location |
|------|----------|
| **Workflow Doc** | `c:\Users\gorjovicgo\.kilocode\workflows\update_memory.md` |
| **Scripts** | `d:\_APP\LOGReport\scripts/` |
| **Backups** | `d:\_APP\LOGReport\backups/` |
| **Project Memory** | `d:\_APP\LOGReport\project_memory.json` |
| **Global Memory** | `d:\_APP\LOGReport\global_memory.json` |

## 🛠️ Tool Arsenal

| Tool | Purpose |
|------|---------|
| **unified_memory_optimizer.py** | PRIMARY - Full 4-phase optimization |
| **validate_both_memories.py** | Validation and reporting |
| **analyze_cluster_precision.py** | Cluster quality analysis |
| **final_summary.py** | Status reporting |

## ⚠️ Common Pitfalls

❌ **DON'T**:
- Target 20:1 ratios (creates "junk drawers")
- Group by naming patterns (Implementation.Everything)
- Exceed 80 chars per observation
- Leave orphaned entities
- Skip connectivity validation

✅ **DO**:
- Target 6:1 ratios for semantic precision
- Group by purpose (Services, Methods, Tests, UI)
- Use aggressive 80-char condensation
- Validate 100% connectivity
- Run validation after changes

## 📖 Documentation

See `MEMORY_OPTIMIZATION_COMPLETE.md` for full project details.

See `update_memory.md` workflow for comprehensive process documentation.

---

**Quick Status Check**: `python scripts/final_summary.py`

**Full Optimization**: `python scripts/unified_memory_optimizer.py [memory_file]`

**Validation**: `python scripts/validate_both_memories.py`
