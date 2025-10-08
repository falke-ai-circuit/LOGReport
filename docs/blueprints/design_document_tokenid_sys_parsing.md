# 🏗️ Design Document: [tokenid].sys File Parsing

> **Purpose:** *To outline the logic for loading, parsing, and IP address extraction from [tokenid].sys files, ensuring compatibility with existing parsing mechanisms and supporting AL/AP node differentiation.*

## 📋 Overview
**What:** Logic for parsing [tokenid].sys files | **Why:** Enhance Node configuration with IP address extraction | **Goal:** Provide a detailed design for correct IP address extraction and integration.

## 🎯 Requirements
| Type | Requirement | Priority | Target |
|------|-------------|----------|--------|
| Functional | Load [tokenid].sys files based on token ID | H | Correct file path resolution |
| Functional | Extract IP address (set XD_IP_ADDR=...) | H | Accurate IP address capture |
| Functional | Differentiate between AL and AP node handling | H | Node-specific parsing logic applied |
| Functional | Support parsing of multiple initial sys files | H | All specified files processed |
| Compatibility | Compatible with existing sys file parsing | H | Seamless integration |
| Compatibility | Compatible with existing token detection | H | No conflicts with token handling |

## 🔧 Architecture
```
[SysFileLoader] --(loads file paths)--> [SysFileParser] --(parses content)--> [Node Data (with IP)]
      ^                                       ^
      |                                       |
(token_ids, directory_path)             (config/sys_parsing_rules.json)
```
| Component | Role | Technology | Integration |
|-----------|------|------------|-------------|
| SysFileLoader | Resolves file paths for [tokenid].sys files | Python | Delegates parsing to SysFileParser |
| SysFileParser | Parses content, extracts node data and IP addresses | Python (re, json) | Uses regex patterns from config/sys_parsing_rules.json |
| config/sys_parsing_rules.json | Stores regex patterns and node type configurations | JSON | Loaded by SysFileParser |

## ⚡ Implementation Plan
| Phase | Duration | Goals | Deliverables | Dependencies |
|-------|----------|-------|--------------|--------------|
| **🎯 Foundation** | 1 week | Confirm existing components meet requirements | Design Document | Existing SysFileLoader, SysFileParser, config/sys_parsing_rules.json |
| **🚀 Features** | 2 weeks | Implement any necessary extensions to SysFileParser for IP extraction if not fully covered | Updated SysFileParser, Unit Tests | Phase 1 |
| **✨ Polish** | 1 week | Integrate with Node configuration window, handle multiple files | Integrated Node Config, Integration Tests | Phase 2 |

## 🧪 Testing
**Strategy:** Unit (100%) • Integration (file loading, parsing, IP extraction) • E2E (Node config window update)
**Gates:** P1→Unit tests for SysFileParser IP extraction • P2→Integration tests for SysFileLoader and SysFileParser interaction • P3→E2E tests for Node configuration window displaying correct IPs

## 📊 Resources & Timeline
| Resource | P1 | P2 | P3 | Total |
|----------|----|----|----| ------|
| **Team Size** | 1 | 1 | 1 | 1 |
| **Budget** | Low | Medium | Low | Medium |
| **Skills** | Python, Regex | Python, Regex, PyQt | Python, PyQt | Python, Regex, PyQt |

## ⚠️ Risks
| Risk | Impact | Prob | Mitigation |
|------|--------|------|------------|
| Design flaws leading to incorrect IP extraction | H | M | *Thorough design review, unit testing, and integration testing.* |
| Integration issues with existing parsing | M | M | *Careful analysis of existing `parse_sys_file` and `merge_node_data` functions, incremental integration.* |
| Edge cases in sys file formats not handled | M | M | *Comprehensive test cases covering various sys file structures and IP address formats.* |

## 🔗 Dependencies
**External:** None
**Internal:** `src/sys_file_loader.py` • `src/node_config_parser.py` • `config/sys_parsing_rules.json` • Existing Node configuration window components

## 📈 Success Metrics
**Technical:** IP extraction accuracy (100%) • File parsing success rate (100%) • Compatibility with existing components (100%)
**Business:** Improved user experience in Node configuration • Reduced manual IP entry errors

---
**📚 Refs:** *analysis_report_sys_file_parsing.md, token_detection_analysis.md, Global.DataProcessingPattern.Configuration.NodeConfigurationFromSysFile_Pattern*