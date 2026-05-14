"""CoderVPS runtime action executor.

Reads a JSON action plan, executes each action with idempotency guarantees,
and enforces workspace path isolation.
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

# Default runtime root; overridable via CDEV_RUNTIME_ROOT env var.
CDEV_RUNTIME_ROOT = Path(os.environ.get("CDEV_RUNTIME_ROOT", "/workspace/.cdev"))
STATE_ROOT = CDEV_RUNTIME_ROOT / "state"
TMP_ROOT = CDEV_RUNTIME_ROOT / "tmp"


def inside_allowed_root(path: str) -> bool:
    """Return True if *path* is within a writable workspace area."""
    resolved = Path(path).resolve().as_posix()
    return (
        resolved.startswith("/workspace/.cdev/")
        or resolved == "/workspace/.cdev"
        or resolved.startswith("/home/coder/.local/share/code-server/")
        or resolved.startswith("/home/coder/.config/code-server/")
    )


def require_workspace_path(path: str) -> Path:
    """Validate and return a workspace-resident path.

    Raises SystemExit if the path is outside the allowed workspace roots.
    """
    if not inside_allowed_root(path):
        raise SystemExit(f"refusing non-workspace path: {path}")
    return Path(path)


def state_marker(action_id: str) -> Path:
    """Return the marker file path that records completion of an action."""
    return STATE_ROOT / f"{action_id}.done"


def verify_sha256(path: Path, expected: str) -> None:
    """Verify the SHA-256 digest of *path* matches *expected*.

    Raises SystemExit on mismatch.
    """
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(
            f"sha256 mismatch for {path}: expected {expected}, got {digest}"
        )


def action_download(url: str, dest: str, sha256: str | None) -> None:
    """Download *url* to *dest*, optionally verifying SHA-256.

    Uses a ``.part`` temporary file and atomic ``os.replace()``.
    """
    final = require_workspace_path(dest)
    part = final.with_name(final.name + ".part")
    final.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url, timeout=120) as response, part.open("wb") as fh:
        shutil.copyfileobj(response, fh)

    if sha256:
        verify_sha256(part, sha256)

    os.replace(part, final)


def action_extract_tar(src: str, dest: str, strip_components: int = 0) -> None:
    """Extract a tar archive from *src* to *dest* using atomic rename."""
    source = require_workspace_path(src)
    final = require_workspace_path(dest)
    final.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="extract-", dir=CDEV_RUNTIME_ROOT / "tmp"
    ) as tmpdir:
        with tarfile.open(source) as archive:
            # Safety: check all member paths stay inside tmpdir
            tmp_resolved = Path(tmpdir).resolve()
            for member in archive.getmembers():
                target = (Path(tmpdir) / member.name).resolve()
                if not str(target).startswith(str(tmp_resolved) + os.sep):
                    raise SystemExit(
                        f"refusing unsafe archive path: {member.name}"
                    )
            archive.extractall(tmpdir)

        extracted = Path(tmpdir)
        if strip_components:
            children = [p for p in extracted.iterdir()]
            if len(children) == 1 and children[0].is_dir():
                extracted = children[0]

        os.replace(extracted, final)


def execute_plan(plan_path: Path) -> int:
    """Execute every action in the plan at *plan_path*.

    Actions are idempotent -- a completion marker is written after each
    action succeeds, and previously-completed actions are skipped.
    """
    plan = json.loads(plan_path.read_text())
    STATE_ROOT.mkdir(parents=True, exist_ok=True)

    for action in plan.get("actions", []):
        action_id = action["id"]
        marker = state_marker(action_id)

        # Idempotency: skip if already done
        if marker.exists():
            continue

        # Check creates hint
        creates = action.get("creates")
        if creates and Path(creates).exists():
            marker.touch()
            continue

        kind = action["type"]

        if kind == "ensure_dir":
            path = action["values"]["path"]
            require_workspace_path(path).mkdir(parents=True, exist_ok=True)

        elif kind == "download":
            action_download(
                action["values"]["url"],
                action["values"]["dest"],
                action["values"].get("sha256"),
            )

        elif kind == "extract_tar":
            action_extract_tar(
                action["values"]["src"],
                action["values"]["dest"],
                int(action["values"].get("strip_components", 0)),
            )

        elif kind == "run":
            subprocess.run(
                action["command"], check=bool(action.get("critical", True))
            )

        elif kind == "verify_command":
            subprocess.run(
                action["command"], check=bool(action.get("critical", True))
            )

        elif kind == "path_prepend":
            # path_prepend and env are declarative -- they are rendered into
            # the env.sh file by startup.sh.  No runtime work here.
            pass

        elif kind == "env":
            # env set is handled by startup.sh writing env.sh
            pass

        elif kind == "symlink":
            src = action["values"]["src"]
            dest = require_workspace_path(action["values"]["dest"])
            if dest.is_symlink() or dest.exists():
                dest.unlink()
            dest.symlink_to(src)

        elif kind == "write_file":
            dest = require_workspace_path(action["values"]["dest"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = action["values"].get("content", "")
            dest.write_text(str(content))

        else:
            raise SystemExit(f"unknown action type: {kind}")

        marker.touch()

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: run_actions.py <plan.json>", file=sys.stderr)
        raise SystemExit(2)
    plan_file = Path(sys.argv[1])
    raise SystemExit(execute_plan(plan_file))
