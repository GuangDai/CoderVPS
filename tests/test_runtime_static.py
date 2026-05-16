"""Static tests for runtime shell scripts and Python action executor."""

from __future__ import annotations

from pathlib import Path


def _all_sh_text() -> str:
    """Concatenate all .sh files under runtime/."""
    if not Path("runtime").exists():
        return ""
    return "\n".join(path.read_text() for path in Path("runtime").rglob("*.sh"))


def _run_actions_text() -> str:
    """Read the Python action executor."""
    path = Path("runtime/lib/run_actions.py")
    if not path.exists():
        return ""
    return path.read_text()


# ---- Workspace isolation in shell scripts ----


def test_runtime_does_not_use_shared_cache_root():
    text = _all_sh_text()
    assert "/opt/cde/cache" not in text
    assert "CDE_CACHE_ROOT" not in text


def test_runtime_uses_workspace_cdev_root():
    text = _all_sh_text()
    assert "/workspace/.cdev" in text


def test_runtime_uses_cdev_runtime_root_variable():
    text = _all_sh_text()
    assert "CDEV_RUNTIME_ROOT" in text


# ---- Startup lock and atomic guards ----


def test_runtime_has_startup_lock_and_atomic_install_guards():
    startup = Path("runtime/startup.sh").read_text()
    runner = _run_actions_text()
    assert "startup.lock" in startup
    assert "flock" in startup
    assert "selection.sha256" in startup
    assert ".part" in runner
    assert "os.replace" in runner
    assert "TMP_ROOT" in runner
    assert "STATE_ROOT" in runner


# ---- Action executor requires workspace paths ----


def test_run_actions_has_require_workspace_path():
    text = _run_actions_text()
    assert "require_workspace_path" in text


def test_run_actions_has_inside_allowed_root():
    text = _run_actions_text()
    assert "inside_allowed_root" in text


def test_run_actions_rejects_non_workspace_paths():
    text = _run_actions_text()
    assert "refusing non-workspace path" in text


# ---- All 9 action types ----


def test_run_actions_supports_all_nine_action_types():
    text = _run_actions_text()
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
        # Should appear as a string literal check
        assert at in text, f"Action type '{at}' not found in run_actions.py"


# ---- Download integrity (atomic, checksum) ----


def test_run_actions_download_uses_part_files():
    text = _run_actions_text()
    assert ".part" in text
    assert "verify_sha256" in text


def test_run_actions_does_not_skip_auto_sha256_verification():
    text = _run_actions_text()
    assert 'sha256 != "auto"' not in text


def test_run_actions_download_atomic_rename():
    text = _run_actions_text()
    assert "os.replace" in text
    assert "part" in text.lower()


# ---- Extract safety (tar path traversal protection) ----


def test_run_actions_extract_checks_path_traversal():
    text = _run_actions_text()
    assert "refusing unsafe archive path" in text
    assert "resolve" in text


def test_run_actions_extract_uses_tempdir():
    text = _run_actions_text()
    assert "tempfile" in text or "mkdtemp" in text


# ---- Idempotency via state markers ----


def test_run_actions_idempotent_via_state_markers():
    text = _run_actions_text()
    assert "state_marker" in text
    assert ".done" in text
    assert "marker.exists()" in text


def test_run_actions_creates_check_for_idempotency():
    text = _run_actions_text()
    assert "creates" in text
    assert "Path(creates).exists()" in text


# ---- CDEV_RUNTIME_ROOT configurable via env ----


def test_run_actions_reads_cdev_runtime_root_from_env():
    text = _run_actions_text()
    assert "CDEV_RUNTIME_ROOT" in text
    assert "os.environ.get" in text


def test_startup_script_sets_cdev_runtime_root_default():
    startup = Path("runtime/startup.sh").read_text()
    assert 'CDEV_RUNTIME_ROOT="${CDEV_RUNTIME_ROOT:-/workspace/.cdev}"' in startup


# ---- Actions.sh uses variable path ----


def test_actions_sh_uses_variable_paths():
    actions_sh = Path("runtime/lib/actions.sh").read_text()
    assert "CDEV_RUNTIME_ROOT" in actions_sh
    assert "RUNTIME_LIB_DIR" in actions_sh


def test_actions_sh_calls_python_executor():
    actions_sh = Path("runtime/lib/actions.sh").read_text()
    assert "run_actions.py" in actions_sh
    assert "python3" in actions_sh


# ---- env.sh generation ----


def test_startup_generates_env_sh():
    startup = Path("runtime/startup.sh").read_text()
    assert "env.sh" in startup


# ---- Plugin shell files exist and have correct structure ----


def test_all_plugin_sh_files_exist():
    plugins_dir = Path("runtime/plugins")
    for name in ["python", "rust", "go", "cpp"]:
        path = plugins_dir / f"{name}.sh"
        assert path.exists(), f"Missing runtime plugin: {path}"


def test_plugin_sh_files_are_valid():
    plugins_dir = Path("runtime/plugins")
    for path in plugins_dir.glob("*.sh"):
        content = path.read_text()
        assert "#!/usr/bin/env bash" in content
        assert "set -Eeuo pipefail" in content
        assert "runtime plugin loaded" in content


# ---- No shared paths ----


def test_runtime_scripts_no_host_docker_socket():
    text = _all_sh_text()
    assert "/var/run/docker.sock" not in text


def test_runtime_scripts_no_volume_prune():
    text = _all_sh_text()
    assert "docker volume prune" not in text
    assert "docker system prune" not in text


def test_runtime_scripts_no_apt_install():
    text = _all_sh_text()
    assert "apt install" not in text
    assert "apt-get install" not in text


# ---- Error handling ----


def test_run_actions_has_error_handling():
    text = _run_actions_text()
    assert "SystemExit" in text
    assert "critical" in text


def test_startup_has_immutable_selection_guard():
    startup = Path("runtime/startup.sh").read_text()
    assert "immutable workspace selection changed" in startup


# ---- action ordering: ensure_dir before download ----


def test_run_actions_ensure_dir_supports_mkdir():
    text = _run_actions_text()
    assert "parents=True" in text
    assert "exist_ok=True" in text


# ---- path_prepend wires PATH ----


def test_run_actions_path_prepend():
    text = _run_actions_text()
    assert 'os.environ["PATH"]' in text


# ---- env action type ----


def test_run_actions_env_set():
    text = _run_actions_text()
    assert 'kind == "env"' in text


# ---- symlink action type ----


def test_run_actions_symlink():
    text = _run_actions_text()
    assert 'kind == "symlink"' in text
    assert "symlink_to" in text


# ---- write_file action type ----


def test_run_actions_write_file():
    text = _run_actions_text()
    assert 'kind == "write_file"' in text
    assert "write_text" in text
