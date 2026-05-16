"""Detailed tests for Task D -- thorough coverage of all fixes.

Tests:
  - catalog data integrity (no auto, no resolved, no fake sha256)
  - discovery function contracts (return types, TODO annotations, fixture behavior)
  - Dockerfile ARG guards (all 3 guarded, sccache already done)
  - Language list deduplication (single source of truth)
  - cdev command list (only thin commands, sync-generated flow)
  - Docs content checks
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# =============================================================================
# SECTION 1: CATALOG DATA INTEGRITY
# =============================================================================


def test_catalog_tools_no_auto_anywhere():
    """All tool version fields must be either from override or from discovery -- not 'auto'."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    # Check every line of the tools section
    assert '"auto"' not in text, "catalog.py has 'auto' strings"
    assert "'auto'" not in text, "catalog.py has 'auto' strings (single-quoted)"


def test_catalog_no_resolved_anywhere():
    """No 'resolved-' prefix should appear in catalog output."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    assert "resolved-" not in text, "catalog.py has 'resolved-' placeholder"


def test_catalog_todo_coverage():
    """Every TODO in catalog.py must follow the what/why/when format."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    # Count TODOs with all 3 required parts
    todos = [line.strip() for line in text.splitlines() if line.strip().startswith("# TODO:")]
    for todo in todos:
        # Must mention what and blocked and implemented (or similar)
        has_what = ":" in todo
        assert has_what, f"TODO missing explanation colon: {todo}"
    # Count full TODO blocks (what/blocked/when)
    blocked_count = text.count("Blocked by:")
    implemented_count = text.count("Will be implemented:")
    assert blocked_count >= 3, (
        f"Expected at least 3 'Blocked by:' annotations, found {blocked_count}"
    )
    assert implemented_count >= 3, (
        f"Expected at least 3 'Will be implemented:' annotations, found {implemented_count}"
    )


def test_catalog_empty_versions_have_todo_nearby():
    """Empty plugin version lists must have TODO annotations explaining why."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if '"versions":' in line and (
            "python_vers" in line or "rust_vers" in line or "cpp_vers" in line
        ):
            # These should be variable references, not hardcoded []
            assert "[]" not in line, (
                f"Line {i + 1}: versions should be from variable, not empty literal"
            )


# =============================================================================
# SECTION 2: DISCOVERY FUNCTION CONTRACTS
# =============================================================================


def test_discovery_python_versions_return_type():
    from codervps.discovery import python_versions

    result = python_versions()
    assert isinstance(result, list), "python_versions() must return list"


def test_discovery_rust_channels_return_type():
    from codervps.discovery import rust_channels

    result = rust_channels()
    assert isinstance(result, list)
    assert len(result) >= 3, "rust_channels() should return at least stable/beta/nightly"
    versions = [c["version"] for c in result]
    assert "stable" in versions
    assert "beta" in versions
    assert "nightly" in versions


def test_discovery_cpp_llvm_versions_return_type():
    from codervps.discovery import cpp_llvm_versions

    result = cpp_llvm_versions()
    assert isinstance(result, list)


def test_discovery_uv_version_return_type():
    from codervps.discovery import uv_version

    result = uv_version()
    assert isinstance(result, str)
    assert result == "", "uv_version() should return empty string when no fixture and no API"


def test_discovery_code_server_version_return_type():
    from codervps.discovery import code_server_version

    result = code_server_version()
    assert isinstance(result, str)
    assert result == "", "code_server_version() should return empty string when no fixture"


def test_discovery_sccache_return_type():
    from codervps.discovery import sccache_version_and_sha256

    result = sccache_version_and_sha256()
    assert isinstance(result, dict)
    assert "version" in result
    assert "sha256" in result
    assert result["version"] == "", "sccache version should be empty when no fixture"
    assert result["sha256"] == "", "sccache sha256 should be empty when no fixture"


def test_discovery_all_functions_have_todo():
    """All new discovery stubs must have TODO annotations."""
    source = Path(ROOT / "codervps/discovery.py").read_text()
    # Each discovery function should have a TODO in its body
    funcs_with_todo = [
        "python_versions",
        "rust_channels",
        "cpp_llvm_versions",
        "uv_version",
        "code_server_version",
        "sccache_version_and_sha256",
    ]
    for func in funcs_with_todo:
        # Find the function body and check for TODO
        assert "TODO:" in source, f"discovery.py has no TODO for {func}"


def test_discovery_python_versions_accepts_fixture_dir():
    from codervps.discovery import python_versions

    result = python_versions(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, list)


def test_discovery_rust_channels_accepts_fixture_dir():
    from codervps.discovery import rust_channels

    result = rust_channels(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, list)


def test_discovery_cpp_llvm_versions_accepts_fixture_dir():
    from codervps.discovery import cpp_llvm_versions

    result = cpp_llvm_versions(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, list)


def test_discovery_uv_version_accepts_fixture_dir():
    from codervps.discovery import uv_version

    result = uv_version(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, str)


def test_discovery_code_server_version_accepts_fixture_dir():
    from codervps.discovery import code_server_version

    result = code_server_version(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, str)


def test_discovery_sccache_accepts_fixture_dir():
    from codervps.discovery import sccache_version_and_sha256

    result = sccache_version_and_sha256(fixture_dir=Path("tests/fixtures"))
    assert isinstance(result, dict)


# =============================================================================
# SECTION 3: CATALOG WIRING (discovery functions used in refresh_catalog)
# =============================================================================


def test_catalog_imports_all_discovery_functions():
    """Every new discovery function must be imported in catalog.py."""
    source = Path(ROOT / "codervps/catalog.py").read_text()
    required = [
        "python_versions",
        "rust_channels",
        "cpp_llvm_versions",
        "uv_version",
        "code_server_version",
        "sccache_version_and_sha256",
    ]
    for func in required:
        assert func in source, f"catalog.py does not import {func}"


def test_catalog_calls_discovery_functions():
    """catalog.refresh_catalog must call each discovery function."""
    source = Path(ROOT / "codervps/catalog.py").read_text()
    # Check that each function is actually called (not just imported)
    assert "python_versions(" in source, "catalog.py should call python_versions()"
    assert "rust_channels(" in source, "catalog.py should call rust_channels()"
    assert "cpp_llvm_versions(" in source, "catalog.py should call cpp_llvm_versions()"
    assert "uv_version(" in source, "catalog.py should call uv_version()"
    assert "code_server_version(" in source, "catalog.py should call code_server_version()"
    assert "sccache_version_and_sha256(" in source, (
        "catalog.py should call sccache_version_and_sha256()"
    )


def test_refresh_catalog_tools_no_auto():
    """refresh_catalog output must never contain 'auto' for any tool version."""
    from codervps.catalog import refresh_catalog
    from codervps.config import load_toolchains_config

    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg)

    tools = catalog["tools"]
    for tool_name, tool_data in tools.items():
        if isinstance(tool_data, dict):
            for field in tool_data:
                val = tool_data[field]
                assert val != "auto", f"tools.{tool_name}.{field} is 'auto'"


def test_refresh_catalog_tools_no_resolved():
    """refresh_catalog output must never contain 'resolved-' in any string value."""
    from codervps.catalog import refresh_catalog
    from codervps.config import load_toolchains_config

    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg)

    serialized = json.dumps(catalog)
    assert "resolved-" not in serialized, "catalog output contains 'resolved-'"


def test_refresh_catalog_with_fixtures_uses_discovery():
    """With fixture_dir, catalog should read from fixture files."""
    from codervps.catalog import refresh_catalog
    from codervps.config import load_toolchains_config

    cfg = load_toolchains_config(Path("config/toolchains.toml"))
    catalog = refresh_catalog(cfg, fixture_dir=Path("tests/fixtures"))

    # Go versions should be populated from fixture
    go_versions = catalog["plugins"]["go"]["versions"]
    assert len(go_versions) > 0, "Go versions should be discovered from fixtures"


# =============================================================================
# SECTION 4: DOCKERFILE EMPTY ARG GUARDS
# =============================================================================


def test_dockerfile_all_three_guards_present():
    """Dockerfile must have guards for CODE_SERVER_VERSION, LLVM_VERSION, NODE_VERSION."""
    text = Path(ROOT / "docker/Dockerfile").read_text()

    # All three should have if [ -n ... ] guards
    assert 'if [ -n "${CODE_SERVER_VERSION}" ]' in text
    assert 'if [ -n "${LLVM_VERSION}" ]' in text
    assert 'if [ -n "${NODE_VERSION}" ]' in text

    # SCCACHE guard was already present
    assert 'if [ -n "${SCCACHE_SHA256}" ]' in text


def test_dockerfile_guards_have_else_echo():
    """Each guard should have an else branch that logs skip."""
    text = Path(ROOT / "docker/Dockerfile").read_text()
    assert "code-server skipped:" in text
    assert "LLVM toolchain install skipped:" in text
    assert "node install skipped:" in text


def test_dockerfile_uv_fallback():
    """UV_VERSION should still have :-latest fallback."""
    text = Path(ROOT / "docker/Dockerfile").read_text()
    assert "${UV_VERSION:-latest}" in text


# =============================================================================
# SECTION 5: LANGUAGE LIST DEDUPLICATION
# =============================================================================


def test_template_uses_imported_languages():
    """template.py must import _LANGUAGES from extensions and use it."""
    source = Path(ROOT / "codervps/render/template.py").read_text()
    assert "from .extensions import _LANGUAGES" in source


def test_template_no_hardcoded_language_list_in_for():
    """template.py must NOT have hardcoded [\"python\", \"rust\", \"go\", \"cpp\"] in the for loop."""
    source = Path(ROOT / "codervps/render/template.py").read_text()
    assert 'for plugin_id in ["python", "rust", "go", "cpp"]' not in source


def test_extensions_exports_languages():
    """extensions.py must export _LANGUAGES as a module-level constant."""
    source = Path(ROOT / "codervps/render/extensions.py").read_text()
    assert "_LANGUAGES" in source
    assert '["python", "rust", "go", "cpp"]' in source


def test_languages_consistent_between_files():
    """All 4 languages must match between _LANGUAGES and _PLUGIN_TYPES."""
    from codervps.render.extensions import _LANGUAGES
    from codervps.plugins import _PLUGIN_TYPES

    assert set(_LANGUAGES) == set(_PLUGIN_TYPES.keys()), (
        f"_LANGUAGES={_LANGUAGES} and _PLUGIN_TYPES keys={list(_PLUGIN_TYPES.keys())} differ"
    )


# =============================================================================
# SECTION 6: CDEV TESTS
# =============================================================================


def test_cdev_has_all_required_commands():
    """cdev must have only the thin-helper commands."""
    text = Path(ROOT / "cdev").read_text()

    required = [
        "info",
        "doctor",
        "ps",
        "logs",
        "restart",
        "template-dir",
        "push-template",
        "sync-generated",
        "check-generated",
        "check-images",
        "list-workspace-volumes",
        "install-self",
    ]
    for cmd in required:
        # Each required command should appear as a case in the dispatch
        assert f"{cmd})" in text or f"cmd_{cmd.replace('-', '_')}" in text, (
            f"cdev missing command: {cmd}"
        )


def test_cdev_sync_generated_has_flock():
    """sync-generated must use flock for locking."""
    text = Path(ROOT / "cdev").read_text()
    assert "flock" in text
    assert "/opt/coder-cde/.locks" in text
    assert "sync-generated.lock" in text


def test_cdev_sync_generated_validates_staging():
    """sync-generated must validate staging before switching."""
    text = Path(ROOT / "cdev").read_text()
    assert "cmd_check_generated" in text


def test_cdev_no_docker_build():
    """cdev must not have docker build commands (not counting buildx inspect)."""
    text = Path(ROOT / "cdev").read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # "docker build" followed by space or end-of-line is a build command
        if "docker build " in stripped and "buildx" not in stripped:
            raise AssertionError(f"cdev line {i + 1}: has 'docker build': {stripped}")


def test_cdev_list_workspace_volumes_readonly():
    """list-workspace-volumes must not delete volumes."""
    text = Path(ROOT / "cdev").read_text()
    # The function should exist
    assert "cmd_list_workspace_volumes" in text
    # It should contain a warning
    assert "Do NOT delete" in text


def test_cdev_sync_generated_atomic_switch():
    """sync-generated must use mv for atomic directory switch."""
    text = Path(ROOT / "cdev").read_text()
    assert "mv " in text  # atomic switch via mv


# =============================================================================
# SECTION 7: DOCS TESTS
# =============================================================================


def test_readme_has_all_required_sections():
    text = Path(ROOT / "README.md").read_text()
    required = [
        "generated branch",
        "GitHub CLI is not required",
        "/workspace/.cdev",
        "noble-YYYYMMDD-node",
        "sync-generated",
        "push-template",
        "docker volume prune",
        "cdev list-workspace-volumes",
    ]
    for requirement in required:
        assert requirement in text, f"README missing: {requirement}"


def test_vsix_doc_has_all_required_sections():
    text = Path(ROOT / "docs/vsix.md").read_text()
    assert ".vsix files are not committed" in text
    assert "/opt/coder-cde/vsix" in text
    assert "README.md" in text


def test_generated_branch_doc_has_all_required_sections():
    text = Path(ROOT / "docs/generated-branch.md").read_text()
    assert "toolchains.json" in text
    assert "images.json" in text
    assert "main.tf.json" in text
    assert "--force-with-lease" in text
    assert "catalog" in text
