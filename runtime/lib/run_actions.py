"""Runtime action executor for CoderVPS workspace startup.

Executes a JSON runtime plan with 9 action types. All writes are strictly
scoped to paths under /workspace/.cdev (except for code-server user config).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

CDEV_RUNTIME_ROOT = Path(os.environ.get("CDEV_RUNTIME_ROOT", "/workspace/.cdev"))
STATE_ROOT = CDEV_RUNTIME_ROOT / "state"
TMP_ROOT = CDEV_RUNTIME_ROOT / "tmp"


def inside_allowed_root(path: str) -> bool:
    """Check if a path is within the allowed workspace roots."""
    resolved = Path(path).resolve().as_posix()
    return (
        resolved.startswith((CDEV_RUNTIME_ROOT / "").as_posix())
        or resolved == CDEV_RUNTIME_ROOT.as_posix()
        or resolved.startswith("/home/coder/.local/share/code-server/")
        or resolved.startswith("/home/coder/.config/code-server/")
    )


def require_workspace_path(path: str) -> Path:
    """Validate that the path is within the allowed workspace root."""
    if not inside_allowed_root(path):
        raise SystemExit(f"refusing non-workspace path: {path}")
    return Path(path)


def state_marker(action_id: str) -> Path:
    """Return the path to the state marker file for an action."""
    return STATE_ROOT / f"{action_id}.done"


def verify_sha256(path: Path, expected: str) -> None:
    """Verify a file's SHA256 checksum. Exits on mismatch."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"sha256 mismatch for {path}: expected {expected}, got {digest}")


def download(url: str, dest: str, sha256: str | None) -> None:
    """Download a file to dest using .part atomic rename. Optionally verify SHA256."""
    final = require_workspace_path(dest)
    part = final.with_name(final.name + ".part")
    final.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=120) as response, part.open("wb") as fh:
        shutil.copyfileobj(response, fh)
    if sha256:
        verify_sha256(part, sha256)
    os.replace(part, final)


def extract_tar(src: str, dest: str, strip_components: int = 0) -> None:
    """Extract a tarball into dest using a temp directory with atomic rename."""
    source = require_workspace_path(src)
    final = require_workspace_path(dest)
    final.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="extract-", dir=str(TMP_ROOT))
    try:
        with tarfile.open(source) as archive:
            tmp_resolved = Path(tmp_dir).resolve()
            for member in archive.getmembers():
                target = (Path(tmp_dir) / member.name).resolve()
                if not str(target).startswith(str(tmp_resolved) + os.sep):
                    raise SystemExit(f"refusing unsafe archive path: {member.name}")
            archive.extractall(tmp_dir)
        extracted = Path(tmp_dir)
        if strip_components:
            children = [p for p in extracted.iterdir()]
            if len(children) == 1 and children[0].is_dir():
                extracted = children[0]
        os.replace(extracted, final)
    finally:
        if Path(tmp_dir).exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def run(plan_path: Path) -> int:
    plan = json.loads(plan_path.read_text())
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    for action in plan.get("actions", []):
        action_id = action["id"]
        marker = state_marker(action_id)
        if marker.exists():
            continue

        creates = action.get("creates")
        if creates and Path(creates).exists():
            marker.touch()
            continue

        kind = action["type"]
        critical = bool(action.get("critical", True))

        if kind == "ensure_dir":
            path = action["values"]["path"]
            require_workspace_path(path).mkdir(parents=True, exist_ok=True)

        elif kind == "download":
            vals = action["values"]
            download(vals["url"], vals["dest"], vals.get("sha256"))

        elif kind == "extract_tar":
            vals = action["values"]
            extract_tar(
                vals["src"],
                vals["dest"],
                int(vals.get("strip_components", 0)),
            )

        elif kind == "run":
            result = subprocess.run(action["command"], check=False)
            if result.returncode != 0 and critical:
                raise SystemExit(f"critical action {action_id} failed: {result.returncode}")

        elif kind == "verify_command":
            result = subprocess.run(action["command"], check=False)
            if result.returncode != 0 and critical:
                raise SystemExit(
                    f"verification failed for {action_id}: {result.returncode}"
                )

        elif kind == "path_prepend":
            path = action["values"]["path"]
            os.environ["PATH"] = f"{path}{os.pathsep}{os.environ.get('PATH', '')}"

        elif kind == "env":
            for key, val in action["values"].items():
                if key != "path" and key != "type":
                    os.environ[key] = str(val)

        elif kind == "symlink":
            vals = action["values"]
            src = vals["src"]
            dest = require_workspace_path(vals["dest"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.symlink_to(src)

        elif kind == "write_file":
            vals = action["values"]
            dest = require_workspace_path(vals["dest"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(vals.get("content", ""))

        else:
            raise SystemExit(f"unknown action type: {kind}")

        marker.touch()

    return 0


if __name__ == "__main__":
    raise SystemExit(run(Path(sys.argv[1])))
