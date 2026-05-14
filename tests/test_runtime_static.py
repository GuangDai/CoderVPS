"""Static analysis tests for runtime shell and Python action executor."""

from __future__ import annotations

from pathlib import Path

_RUNTIME = Path("runtime")


def _all_runtime_text() -> str:
    """Concatenate all runtime source files."""
    parts: list[str] = []
    for path in sorted(_RUNTIME.rglob("*")):
        if path.is_file():
            parts.append(path.read_text())
    return "\n".join(parts)


# ============================================================================
# Path safety
# ============================================================================


def test_runtime_does_not_use_shared_cache_root():
    text = _all_runtime_text()
    assert "/opt/cde/cache" not in text
    assert "CDE_CACHE_ROOT" not in text


def test_runtime_uses_workspace_cdev_root():
    text = _all_runtime_text()
    assert "/workspace/.cdev" in text


# ============================================================================
# Startup lock and atomic install
# ============================================================================


def test_runtime_has_startup_lock_and_atomic_install_guards():
    startup = Path("runtime/startup.sh").read_text()
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "startup.lock" in startup
    assert "flock" in startup
    assert "selection.sha256" in startup
    assert ".part" in runner
    assert "os.replace" in runner
    # TMP_ROOT is derived from CDEV_RUNTIME_ROOT with a "tmp" suffix
    assert 'TMP_ROOT = CDEV_RUNTIME_ROOT / "tmp"' in runner
    # STATE_ROOT uses CDEV_RUNTIME_ROOT with a "state" suffix
    assert 'STATE_ROOT = CDEV_RUNTIME_ROOT / "state"' in runner


def test_startup_has_exclusive_flock():
    startup = Path("runtime/startup.sh").read_text()
    assert "flock -n" in startup


def test_startup_trap_cleans_temp_selection():
    startup = Path("runtime/startup.sh").read_text()
    assert "trap" in startup
    assert "selection.new.json" in startup


def test_startup_checks_immutable_selection():
    startup = Path("runtime/startup.sh").read_text()
    assert "CDEV_SELECTION_JSON" in startup
    assert "immutable workspace selection changed" in startup


# ============================================================================
# run_actions.py feature tests
# ============================================================================


def test_run_actions_has_all_nine_action_types():
    runner = Path("runtime/lib/run_actions.py").read_text()
    action_types = [
        "ensure_dir",
        "download",
        "extract_tar",
        "run",
        "path_prepend",
        "env",
        "symlink",
        "write_file",
        "verify_command",
    ]
    for at in action_types:
        assert f'kind == "{at}"' in runner, f"missing action type: {at}"


def test_run_actions_has_require_workspace_path():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "require_workspace_path" in runner
    assert "inside_allowed_root" in runner
    assert "refusing non-workspace path" in runner


def test_run_actions_has_sha256_verification():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "verify_sha256" in runner
    assert "hashlib.sha256" in runner


def test_run_actions_uses_state_markers():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "state_marker" in runner
    assert ".done" in runner


def test_run_actions_has_idempotency_skip():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "marker.exists()" in runner


def test_run_actions_has_creates_check():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert '"creates"' in runner


def test_run_actions_atomic_extract_tar():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert "os.replace(extracted, final)" in runner
    assert "TemporaryDirectory" in runner


def test_run_actions_critical_flag():
    runner = Path("runtime/lib/run_actions.py").read_text()
    assert '"critical"' in runner
    assert 'bool(action.get("critical", True))' in runner


# ============================================================================
# CDEV_RUNTIME_ROOT configurability
# ============================================================================


def test_actions_sh_has_cdev_runtime_root():
    text = Path("runtime/lib/actions.sh").read_text()
    assert "CDEV_RUNTIME_ROOT" in text


def test_startup_sh_has_cdev_runtime_root():
    text = Path("runtime/startup.sh").read_text()
    assert "CDEV_RUNTIME_ROOT" in text


def test_run_actions_py_has_cdev_runtime_root():
    text = Path("runtime/lib/run_actions.py").read_text()
    assert "CDEV_RUNTIME_ROOT" in text


# ============================================================================
# Runtime plugin stubs
# ============================================================================


def test_runtime_plugin_stubs_exist():
    for lang in ["python", "rust", "go", "cpp"]:
        path = _RUNTIME / "plugins" / f"{lang}.sh"
        assert path.is_file(), f"missing runtime plugin: {path}"
        content = path.read_text()
        assert f"runtime plugin loaded: {lang}" in content


def test_runtime_plugin_stubs_are_bash():
    for lang in ["python", "rust", "go", "cpp"]:
        path = _RUNTIME / "plugins" / f"{lang}.sh"
        text = path.read_text()
        assert text.startswith("#!/usr/bin/env bash")


def test_runtime_plugin_stubs_have_error_flags():
    for lang in ["python", "rust", "go", "cpp"]:
        path = _RUNTIME / "plugins" / f"{lang}.sh"
        text = path.read_text()
        assert "set -Eeuo pipefail" in text


# ============================================================================
# actions.sh delegation
# ============================================================================


def test_actions_sh_delegates_to_python():
    text = Path("runtime/lib/actions.sh").read_text()
    assert "run_actions.py" in text
    assert "python3" in text


def test_actions_sh_validates_plan_exists():
    text = Path("runtime/lib/actions.sh").read_text()
    assert "runtime plan not found" in text


# ============================================================================
# Startup env.sh generation
# ============================================================================


def test_startup_writes_env_sh():
    text = Path("runtime/startup.sh").read_text()
    assert "env.sh" in text
    assert 'export PATH="/workspace/.cdev/bin:$PATH"' in text
