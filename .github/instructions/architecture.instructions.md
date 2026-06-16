---
applyTo: '**'
description: 'Project architecture reference for LOGReport - folder structure, component layers, and code organization patterns.'
---

# Architecture & Structure

Project organization for LOGReport (Log Processing & Reporting Tool).

## When This Applies
- Adding new files or components
- Navigating unfamiliar parts of codebase
- Deciding where to place new code
- Moving or reorganizing code

## Root Structure

| Folder | Purpose |
|--------|---------|
| `src/` | Main application source code |
| `src/commander/` | Commander module (node management, services) |
| `docker/` | Container configurations for noVNC |
| `docs/` | Documentation by type |
| `tests/` | Test files |
| `config/` | Configuration files |
| `.github/` | AKIS framework + workflows |
| `log/workflow/` | Session logs |

## Root Files
- .py: main.py, setup.py
- .json: nodes.json, package.json
- .md: README, CHANGELOG, TASKS, TODO
- config: docker-compose.yml, requirements.txt

## Layers

| Layer | Tech | Location |
|-------|------|----------|
| GUI | PyQt5 | `src/gui.py`, `src/node_config_dialog.py` |
| Processing | Python | `src/processor.py`, `src/generator.py` |
| Commander | Python | `src/commander/` |
| Infra | Docker, noVNC | `docker/`, `docker-compose.yml` |
| Agent | AKIS framework | `.github/` |

## File Placement

| Type | Location |
|------|----------|
| Source | `src/` |
| Commander modules | `src/commander/` |
| Tests | `tests/` |
| Docs | `docs/` |
| Logs | `log/workflow/` |
| Config | `config/` |

## Finding Related Code

| Component | Location |
|-----------|----------|
| Main GUI | `src/gui.py` |
| Node Config Dialog | `src/node_config_dialog.py` |
| Log Processing | `src/processor.py` |
| Report Generation | `src/generator.py` |
| Commander Services | `src/commander/services/` |
| Node Management | `src/commander/node_manager.py` |
| Parsers | `src/commander/utils/` |

## ⚠️ Critical Gotchas

| Pattern | Issue | Solution |
|---------|-------|----------|
| PyQt5 | QAction location | Import from QtWidgets, not QtGui |
| PyQt5 | Enum format | Use `Qt.white` not `Qt.GlobalColor.white` |
| Docker | noVNC access | Append `/vnc.html` to URL |
| Codespaces | External access | Set port visibility to Public |
