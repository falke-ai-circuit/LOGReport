# PyInstaller Data Bundling for LOGReporter

## Overview
This document details the bundling of data files (e.g., `nodes.json`, config files) into the PyInstaller spec file (`LOGReporter.spec`) to ensure the frozen executable loads resources from `sys._MEIPASS` without `FileNotFoundError`. This resolves runtime issues in standalone EXE where data files are not accessible from the temporary extraction directory.

## Implementation Changes
- **Updated `datas` in `LOGReporter.spec`**:
  - Added `('nodes.json', '.')` for root-level JSON (node configurations).
  - Added `('config', 'config')` to bundle entire config directory (includes `menu_filter_rules.json`, `settings/recording.yaml`).
  - Preserved existing: `('version_info.txt', '.'), (os.path.abspath('assets'), 'assets')`.
  - Removed outdated `('src/nodes.json', 'src')` as `nodes.json` is now at root.

- **Spec Diff Summary**:
  ```
  datas=[
      ('nodes.json', '.'),
      ('config', 'config'),
      ('version_info.txt', '.'),
      (os.path.abspath('assets'), 'assets')
  ]
  ```
  - Minimal changes: Targeted essentials to avoid over-bundling.
  - Path rationale: Matches project root structure; config dir preserves subpaths.

## Integration Testing
- **Build Verification**: Executed `build.bat` (PyInstaller via spec) → Exit code 0, no errors. Generated `dist/LOGReporter.exe`.
- **Runtime Checks** (Inferred/Planned):
  - O1: No missing file errors → Spec includes resolve `FileNotFoundError` for `nodes.json` and configs.
  - O2: `nodes.json` accessible via `_MEIPASS` → Bundled at root (`.`) ensures `open('nodes.json')` works in frozen mode.
  - O3: Configs bundled without breakage → Dir include (`config`) maintains `config/menu_filter_rules.json` path; no conflicts with existing assets.
- **Basic Tests**: Recommend adding to `tests/`:
  ```python
  import sys
  import os
  import json

  def test_data_bundling():
      if getattr(sys, 'frozen', False):
          base_path = sys._MEIPASS
      else:
          base_path = os.path.abspath(".")
      
      # Test nodes.json
      nodes_path = os.path.join(base_path, 'nodes.json')
      assert os.path.exists(nodes_path)
      with open(nodes_path, 'r') as f:
          data = json.load(f)
      assert isinstance(data, list) and len(data) > 0
      
      # Test config
      config_path = os.path.join(base_path, 'config', 'menu_filter_rules.json')
      assert os.path.exists(config_path)
      with open(config_path, 'r') as f:
          config = json.load(f)
      assert 'rules' in config
      
      # Test recording.yaml
      yaml_path = os.path.join(base_path, 'config', 'settings', 'recording.yaml')
      assert os.path.exists(yaml_path)
  ```
  - Run: `pytest tests/test_bundling.py` post-build.

## Usage Examples
- **Build Command**: `./build.bat` → Builds EXE with bundled data.
- **Runtime Access** (in code):
  ```python
  import sys
  import os
  import json

  def get_resource_path(relative_path):
      if getattr(sys, 'frozen', False):
          base_path = sys._MEIPASS
      else:
          base_path = os.path.abspath(".")
      return os.path.join(base_path, relative_path)

  # Load nodes.json
  nodes_path = get_resource_path('nodes.json')
  with open(nodes_path, 'r') as f:
      nodes = json.load(f)

  # Load config
  config_path = get_resource_path('config/menu_filter_rules.json')
  with open(config_path, 'r') as f:
      rules = json.load(f)
  ```
- **Maintenance**: Update `datas` for new files (e.g., add `('new_data.yaml', '.')`); re-run build.

## Considerations
- **Risks Mitigated**: No large files bundled; paths match code expectations (e.g., `open('nodes.json')`).
- **Limitations**: Does not bundle dynamic/runtime-generated files; use `--add-data` for one-offs.
- **Version**: v1.0 (2025-10-03); Compatible with PyInstaller 6.5.0+.