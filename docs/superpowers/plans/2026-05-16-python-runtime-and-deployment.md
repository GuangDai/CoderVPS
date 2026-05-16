# Python Runtime and Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Python runtime selection more expressive, set VS Code Web to open in tabs, and add a complete deployment guide.

**Architecture:** Discovery parses uv's JSON output into stable uv request strings plus metadata. Template and plugin code consume the same catalog fields. Documentation explains GitHub and VPS deployment without adding runtime behavior.

**Tech Stack:** Python, pytest, ruff, uv, Coder Terraform JSON.

---

### Task 1: Python Runtime Catalog

**Files:**
- Modify: `codervps/discovery.py`
- Modify: `codervps/catalog.py`
- Modify: `codervps/plugins/python.py`
- Modify: `tests/fixtures/python-downloads.json`
- Test: `tests/test_catalog.py`
- Test: `tests/test_plugins.py`

- [ ] Write tests that expect CPython, free-threaded CPython, PyPy, and GraalPy catalog entries with `request`, `uv_key`, `implementation`, `version`, and `variant`.
- [ ] Run those tests and verify they fail against the old minor-only catalog.
- [ ] Implement `python_versions()` to select one latest entry per implementation/minor/variant and generate stable uv request strings.
- [ ] Update `PythonPlugin` so Coder options and runtime actions use `request`.
- [ ] Run the targeted tests and then the full suite.

### Task 2: Coder App Tab Opening

**Files:**
- Modify: `codervps/render/template.py`
- Test: `tests/test_template_renderer.py`

- [ ] Write a test asserting `coder_app.code_server.open_in == "tab"`.
- [ ] Run the test and verify it fails.
- [ ] Add `open_in` to the rendered app.
- [ ] Run the targeted test and full suite.

### Task 3: Deployment Guide

**Files:**
- Create: `docs/deployment-guide.md`
- Modify: `README.md`
- Test: `tests/test_taskd_detailed.py`

- [ ] Write documentation tests for GitHub setup, GHCR, generated branch, VPS, Coder template update, VSIX, and troubleshooting.
- [ ] Run the docs test and verify it fails.
- [ ] Add the operator guide and link it from the README.
- [ ] Run docs tests and full validation.

### Task 4: Validation and Commit

**Files:**
- All touched files

- [ ] Run `env UV_CACHE_DIR=.uv-cache uv run pytest -q`.
- [ ] Run `env UV_CACHE_DIR=.uv-cache uv run ruff check codervps tests`.
- [ ] Run `env UV_CACHE_DIR=.uv-cache uv run ruff format --check codervps tests`.
- [ ] Run fixture catalog, matrix, and render-generated commands.
- [ ] Run real upstream catalog refresh if network is available.
- [ ] Commit the final implementation.
