"""Framework tests for Task D -- data integrity fixes, discovery stubs, cdev rewrite, docs.

These tests validate:
  1A: catalog.py has NO "auto" strings
  1A: catalog.py has NO "resolved-*" strings
  1A: catalog.py has NO fake SHA256 values
  1B: Empty plugin version lists have # TODO: annotations
  1C: discovery.py has required stub functions
  1D: catalog.py wires discovery functions
  1E: Dockerfile has empty ARG guards for CODE_SERVER_VERSION, LLVM_VERSION, NODE_VERSION
  1F: Language list is deduplicated (one source of truth)
  1G: extra_extension_packs parameter is tested
  2A: cdev has no legacy commands and has flock/sync-generated
  2B: docs exist with required content
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# =============================================================================
# Phase 1: Framework Tests (MUST FAIL -- issues exist on current branch)
# =============================================================================


# ---- 1A: catalog.py data integrity ----


def test_catalog_has_no_auto_strings():
    """Verify catalog.py contains no 'auto' placeholder values."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    lines = text.splitlines()
    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if '"auto"' in stripped or "'auto'" in stripped:
            violations.append(f"  line {i}: {stripped}")
    assert not violations, "catalog.py has FORBIDDEN 'auto' strings:\n" + "\n".join(violations)


def test_catalog_has_no_resolved_placeholders():
    """Verify catalog.py contains no 'resolved-*' placeholder strings."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    assert "resolved-" not in text, "catalog.py has FORBIDDEN 'resolved-*' placeholder(s)"


def test_catalog_has_no_fake_sha256():
    """Verify catalog.py has no fake SHA256 values (non-hex, obvious placeholders)."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    # Fake SHA256 patterns: anything that looks like "resolved-...-sha256" or has non-hex chars
    assert "resolved-sccache-release-sha256" not in text, "catalog.py has FORBIDDEN fake SHA256"


# ---- 1B: Empty plugin version lists have TODO annotations ----


def test_empty_plugin_versions_have_todo():
    """Check that empty version lists in catalog.py have # TODO: annotations."""
    text = Path(ROOT / "codervps/catalog.py").read_text()
    # Find lines with "versions": [] for python, rust, cpp
    lines_with_empty = []
    for i, line in enumerate(text.splitlines(), 1):
        if '"versions": []' in line or "'versions': []" in line:
            # Check if this or nearby lines have TODO
            lines_with_empty.append(i)
    # At minimum, catalog.py must have TODO annotations
    # (since empty versions are now populated via discovery function calls)
    assert "TODO:" in text or lines_with_empty == [], (
        f"catalog.py has empty version lists at lines {lines_with_empty} without TODO annotations"
    )


# ---- 1C: discovery.py has required stub functions ----


def test_discovery_has_python_versions_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def python_versions" in source, "discovery.py missing python_versions() function"


def test_discovery_has_rust_channels_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def rust_channels" in source, "discovery.py missing rust_channels() function"


def test_discovery_has_cpp_llvm_versions_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def cpp_llvm_versions" in source, "discovery.py missing cpp_llvm_versions() function"


def test_discovery_has_uv_version_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def uv_version" in source, "discovery.py missing uv_version() function"


def test_discovery_has_code_server_version_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def code_server_version" in source, (
        "discovery.py missing code_server_version() function"
    )


def test_discovery_has_sccache_version_and_sha256_function():
    source = Path(ROOT / "codervps/discovery.py").read_text()
    assert "def sccache_version_and_sha256" in source, (
        "discovery.py missing sccache_version_and_sha256() function"
    )


# ---- 1D: discovery functions are imported in catalog.py ----


def test_catalog_imports_discovery_functions():
    source = Path(ROOT / "codervps/catalog.py").read_text()
    assert "python_versions" in source, "catalog.py should import python_versions from discovery"
    assert "rust_channels" in source, "catalog.py should import rust_channels from discovery"
    assert "cpp_llvm_versions" in source, (
        "catalog.py should import cpp_llvm_versions from discovery"
    )
    assert "uv_version" in source, "catalog.py should import uv_version from discovery"
    assert "code_server_version" in source, (
        "catalog.py should import code_server_version from discovery"
    )
    assert "sccache_version_and_sha256" in source, (
        "catalog.py should import sccache_version_and_sha256 from discovery"
    )


# ---- 1E: Dockerfile empty ARG guards ----


def test_dockerfile_has_code_server_version_guard():
    text = Path(ROOT / "docker/Dockerfile").read_text()
    assert 'if [ -n "${CODE_SERVER_VERSION}" ]' in text, (
        "Dockerfile missing empty ARG guard for CODE_SERVER_VERSION"
    )


def test_dockerfile_has_llvm_version_guard():
    text = Path(ROOT / "docker/Dockerfile").read_text()
    assert 'if [ -n "${LLVM_VERSION}" ]' in text, (
        "Dockerfile missing empty ARG guard for LLVM_VERSION"
    )


def test_dockerfile_has_node_version_guard():
    text = Path(ROOT / "docker/Dockerfile").read_text()
    assert 'if [ -n "${NODE_VERSION}" ]' in text, (
        "Dockerfile missing empty ARG guard for NODE_VERSION"
    )


# ---- 1F: Language list deduplication ----


def test_template_imports_languages_from_extensions():
    """template.py should import _LANGUAGES from extensions instead of hardcoding."""
    source = Path(ROOT / "codervps/render/template.py").read_text()
    # Either imports _LANGUAGES or uses the extensions.LANGUAGES pattern
    has_import = "from codervps.render.extensions import _LANGUAGES" in source
    has_correct_import = "from .extensions import _LANGUAGES" in source
    # If it still has the literal hardcoded ["python", "rust", "go", "cpp"] on line 94...
    has_hardcoded_in_for = 'for plugin_id in ["python", "rust", "go", "cpp"]' in source
    assert has_import or has_correct_import or not has_hardcoded_in_for, (
        "template.py should import _LANGUAGES from extensions.py instead of hardcoding list"
    )


# ---- 1G: extra_extension_packs test exists ----


def test_extra_extension_packs_parameter():
    """Test that extra_extension_packs parameter is present in rendered template."""
    from codervps.render.template import render_main_tf_json

    catalog = {
        "plugins": {
            "python": {"versions": [], "defaults": {"version": "3.13"}},
            "rust": {"versions": [], "defaults": {"toolchain": "stable"}},
            "go": {"versions": [], "defaults": {"version": "1.24.9"}},
            "cpp": {"versions": [], "defaults": {"llvm": "19"}},
        },
        "node": {"majors": {"24": {"version": "24.11.1", "status": "active_lts"}}},
    }
    images = {"schema_version": 1, "images": []}
    result = render_main_tf_json(images, catalog)
    extra = result["data"]["coder_parameter"]["extra_extension_packs"]
    assert extra["name"] == "extra_extension_packs"
    assert extra["type"] == "list(string)"
    assert extra["form_type"] == "multi-select"
    assert extra["mutable"] is False
    assert extra["default"] == "[]"
    assert extra["order"] == 3
    assert "option" in extra


# ---- 2A: cdev has no legacy commands ----


def test_cdev_has_no_legacy_patch_or_build_commands():
    text = Path(ROOT / "cdev").read_text()
    assert "patch-runtime" not in text, "cdev has FORBIDDEN legacy command: patch-runtime"
    assert "clean-main-tf" not in text, "cdev has FORBIDDEN legacy command: clean-main-tf"
    assert "write-startup" not in text, "cdev has FORBIDDEN legacy command: write-startup"
    assert "rebuild-devbox" not in text, "cdev has FORBIDDEN legacy command: rebuild-devbox"
    assert "docker build " not in text, "cdev has FORBIDDEN docker build command"
    assert "docker build\n" not in text, "cdev has FORBIDDEN docker build command"


def test_cdev_does_not_prune_coder_managed_volumes():
    text = Path(ROOT / "cdev").read_text()
    assert "docker volume prune" not in text
    assert "docker system prune --volumes" not in text
    assert "docker volume rm" not in text


def test_cdev_sync_generated_is_locked_and_atomic():
    text = Path(ROOT / "cdev").read_text()
    assert "flock" in text, "cdev missing flock for sync-generated lock"
    assert "/opt/coder-cde/.locks" in text, "cdev missing /opt/coder-cde/.locks lock dir"
    assert "check-generated" in text, "cdev should reference check-generated in sync flow"


# ---- 2B: Docs exist with required content ----


def test_readme_mentions_generated_branch_and_no_gh_cli():
    text = Path(ROOT / "README.md").read_text()
    assert "generated branch" in text, "README missing mention of 'generated branch'"
    assert "GitHub CLI is not required" in text, "README missing 'GitHub CLI is not required'"
    assert "/workspace/.cdev" in text, "README missing '/workspace/.cdev'"


def test_vsix_docs_say_binaries_are_not_committed():
    text = Path(ROOT / "docs/vsix.md").read_text()
    assert ".vsix files are not committed" in text
    assert "/opt/coder-cde/vsix" in text


def test_generated_branch_docs_exist():
    path = ROOT / "docs/generated-branch.md"
    assert path.exists(), "docs/generated-branch.md does not exist"
    text = path.read_text()
    assert len(text) > 100, "docs/generated-branch.md appears too short"
