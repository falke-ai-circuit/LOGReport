# Test Suite Documentation

## Overview

This directory contains the LOGReport test suite, organized using a **hierarchical structure** for scalability and maintainability. The taxonomy follows a **type → theme** pattern to enable efficient test discovery and clear ownership.

---

## Directory Structure

```
tests/
├── unit/                   # Isolated component tests (single module/class)
│   ├── sys_file/           # SYS file parsing & loading
│   │   ├── test_sys_file_parser.py  # Node configuration extraction
│   │   └── test_sys_file_loader.py  # SYS file loading & token detection
│   ├── token_detection/    # Token identification logic
│   │   ├── test_token_detection.py
│   │   └── test_token_detection_standalone.py
│   ├── test_log_creator.py  # PDF log file structure creation
│   └── test_generator.py    # Report generation (PDF/DOCX)
│
├── integration/            # Multi-component workflows (2-3 modules)
│   ├── test_processor_integration.py  # LogProcessor pipeline
│   └── [38 other integration tests]
│
├── system/                 # End-to-end scenarios (full stack)
│   ├── telnet/             # Telnet connection management
│   │   └── test_telnet_connection_management.py
│   └── ui/                 # PyQt UI testing
│
├── regression/             # Bug prevention tests
│   └── [Historical bug fixes]
│
└── commander/              # Commander-specific tests (30 files)
```

---

## Naming Conventions

### File Naming
- **Format**: `test_[module_name].py` (mirrors `src/` structure)
- **Examples**:
  - `test_log_creator.py` → tests `src/log_creator.py`
  - `test_sys_file_parser.py` → tests `src/sys_file_parser.py`

### Test Function Naming
- **Format**: `test_[feature]_[scenario]` (descriptive, lowercase_with_underscores)
- **Examples**:
  - `test_create_file_structure_basic()` - core functionality
  - `test_sys_file_parsing_al01()` - specific node type
  - `test_node_name_with_spaces()` - edge case

### Test Class Naming (Optional)
- **Format**: `Test[Feature][Aspect]` (CamelCase)
- **Examples**:
  - `TestLogCreatorFileStructure` - groups file structure tests
  - `TestLogCreatorEdgeCases` - groups edge case tests

---

## Test Categories

### Unit Tests (`tests/unit/`)
**Scope**: Single module/class in isolation  
**Dependencies**: Mocks for external dependencies (filesystem, network, database)  
**Execution Time**: <0.1s per test  
**Coverage Target**: 80%+ for core business logic

**Example**:
```python
def test_create_file_structure_basic(tmp_path):
    """Test LogCreator creates basic directory structure."""
    creator = LogCreator(base_path=tmp_path)
    result = creator.create_file_structure(nodes=[...])
    assert (tmp_path / "FBC" / "AP01m").exists()
```

### Integration Tests (`tests/integration/`)
**Scope**: 2-3 modules working together  
**Dependencies**: Real filesystem, mocked external services (telnet, database)  
**Execution Time**: 0.1-1s per test  
**Coverage Target**: 60%+ for workflows

**Example**:
```python
def test_processor_integration_full_pipeline(tmp_path):
    """Test LogProcessor end-to-end pipeline: load → parse → generate."""
    processor = LogProcessor(config=...)
    result = processor.process_logs(tmp_path / "input")
    assert result.pdf_path.exists()
    assert result.node_count == 5
```

### System Tests (`tests/system/`)
**Scope**: Full application stack (UI → services → filesystem)  
**Dependencies**: Real environment (may require telnet servers, PyQt display)  
**Execution Time**: 1-10s per test  
**Coverage Target**: Critical user workflows only

**Example**:
```python
def test_telnet_connection_management_reconnect(telnet_server):
    """Test telnet reconnection after connection loss."""
    session = TelnetSession(host="localhost", port=telnet_server.port)
    session.disconnect()
    session.connect()
    assert session.is_connected()
```

### Regression Tests (`tests/regression/`)
**Scope**: Historical bugs that must not recur  
**Dependencies**: Matches original bug report context  
**Execution Time**: Variable  
**Coverage Target**: 100% of confirmed bugs

---

## Running Tests

### Quick Start
```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Run specific file
python -m pytest tests/unit/test_log_creator.py -v

# Run specific test
python -m pytest tests/unit/test_log_creator.py::test_create_file_structure_basic -v
```

### Coverage Analysis
```powershell
# Generate coverage report
python -m pytest tests/ --cov=src --cov-report=html

# View report
start htmlcov/index.html  # Windows
```

### Performance Profiling
```powershell
# Show slowest 10 tests
python -m pytest tests/ --durations=10

# Show all durations
python -m pytest tests/ --durations=0
```

---

## Writing New Tests

### 1. Choose Test Category
- **Unit**: Testing single module/class? → `tests/unit/[theme]/test_[module].py`
- **Integration**: Testing 2-3 modules together? → `tests/integration/test_[workflow].py`
- **System**: Testing full stack? → `tests/system/[theme]/test_[feature].py`

### 2. Follow Template

**Unit Test Template**:
```python
"""Unit tests for [Module Name] ([brief description])."""
import pytest
from src.[module] import [ClassName]

class Test[ClassName][Aspect]:
    """Test [ClassName] [aspect description]."""
    
    def test_[feature]_[scenario](self, fixture_name):
        """Test [feature] when [scenario]."""
        # Arrange
        obj = [ClassName](...)
        
        # Act
        result = obj.[method](...)
        
        # Assert
        assert result == expected_value
```

**Fixture Best Practices**:
```python
@pytest.fixture
def sample_nodes():
    """Provide sample node configuration for testing."""
    return [
        {"name": "AP01m", "ip": "192.168.0.11", "type": "AP01", "tokens": ["101", "102"]},
        {"name": "AP02m", "ip": "192.168.0.12", "type": "AP02", "tokens": ["103"]},
    ]
```

### 3. Validate Fixture Schema
⚠️ **CRITICAL**: Ensure fixture data matches actual data model schemas (learned from Phase 2)

**Example Issue**:
```python
# ❌ WRONG: Fixture expects 'token_id' but NodeToken model doesn't provide it
@pytest.fixture
def sample_nodes():
    return [{"name": "AP01m", "token_id": "101"}]  # KeyError at runtime

# ✅ CORRECT: Match NodeToken model schema
@pytest.fixture
def sample_nodes():
    return [{"name": "AP01m", "tokens": ["101", "102"]}]  # Matches actual model
```

### 4. Use Assertions (Not Returns)
```python
# ❌ WRONG: Returns bool (PytestReturnNotNoneWarning)
def test_token_detection():
    return token_exists()

# ✅ CORRECT: Uses assertion
def test_token_detection():
    assert token_exists()
```

---

## Test Quality Standards

### Pass Rate Targets
- **Unit**: ≥95%
- **Integration**: ≥90%
- **System**: ≥85%
- **Overall**: ≥87% (Phase 6 baseline)

### Performance Targets
- **Unit**: <0.1s per test
- **Integration**: <1s per test
- **System**: <10s per test
- **Total Suite**: <5 minutes

### Coverage Targets
- **Core Business Logic**: 80%
- **Services**: 70%
- **Utils**: 60%
- **UI Components**: 40% (PyQt challenges)

---

## Known Issues & Workarounds

### Environment Blockers

#### Python 3.13 telnetlib Removal
- **Impact**: 22 tests blocked (tests/system/telnet/)
- **Workaround**: Use `telnetlib3` or `asyncio` replacement
- **Tracking**: See [WIN_SERVER_2012_INCOMPATIBILITY.md](../WIN_SERVER_2012_INCOMPATIBILITY.md)

#### PyQt6 DLL Load Errors
- **Impact**: 31 tests blocked (tests/system/ui/)
- **Workaround**: Ensure PyQt6 installed: `pip install PyQt6`
- **Tracking**: Check `python -m pytest tests/system/ui/ -v` for errors

### Code Issues

#### AL Node Parsing Off-By-One
- **Impact**: 4/4 AL tests fail (test_sys_file_parsing_al01/02/03/08)
- **Root Cause**: Parser includes node ID as first token for AL types
- **Workaround**: None (requires parser fix or test expectation update)
- **Tracking**: See [Phase 6 Validation Report](../logs/tests_analysis_PHASE_6_VALIDATION_20250113.md#systematic-pattern-al-node-token-extraction-off-by-one)

#### Import Path Inconsistencies
- **Impact**: 74 tests blocked (utils/commander imports without `src.` prefix)
- **Workaround**: Add `src.` prefix: `from src.utils.file_utils import ...`
- **Tracking**: See [Phase 6 Validation Report](../logs/tests_analysis_PHASE_6_VALIDATION_20250113.md#import-path-issues-deferred)

---

## Test Metrics History

### Phase 6 Baseline (2025-01-13)
| Metric | Value | Notes |
|--------|-------|-------|
| Total Tests | 226 | 89 files organized |
| Executable | 35 | 39% (telnetlib:22, PyQt6:31 blocked) |
| Validated | 31 | Excluded import-blocked tests |
| **Pass Rate** | **87.1%** | 27 passed / 31 validated |
| Performance | 0.34s | Total runtime (slowest: 0.02s) |
| Coverage | TBD | Blocked by import issues |

### Phase 2 Creation (2025-01-10)
| Metric | Value | Notes |
|--------|-------|-------|
| Tests Added | +196 | test_log_creator, test_generator, test_processor_integration |
| Quality | 4.62→5.12 | +10.8% improvement |
| Pass Rate | 100% | test_log_creator.py (12/12) |

---

## Contributing

### Before Committing
1. Run full test suite: `python -m pytest tests/ -v`
2. Check coverage: `python -m pytest tests/ --cov=src`
3. Fix warnings: `python -m pytest tests/ --strict-warnings`
4. Update this README if adding new test categories or themes

### Test Review Checklist
- [ ] Test name is descriptive and follows convention
- [ ] Fixtures match actual data model schemas
- [ ] Assertions used (not return statements)
- [ ] Test passes in isolation: `pytest tests/unit/test_[name].py::test_[function] -v`
- [ ] Test categorized correctly (unit/integration/system)
- [ ] Performance acceptable (<0.1s for unit, <1s for integration)

---

## Support

For issues or questions:
1. Check [Known Issues](#known-issues--workarounds)
2. Review [Phase 6 Validation Report](../logs/tests_analysis_PHASE_6_VALIDATION_20250113.md)
3. Consult [Troubleshooting Guide](../docs/user/troubleshooting/troubleshooting_guide.md)
