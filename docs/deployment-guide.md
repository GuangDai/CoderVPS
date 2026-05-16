# Deployment Guide

This guide walks through publishing CoderVPS from GitHub and deploying it on a
single local VPS. It assumes the source branch is `master` and the generated
branch is `generated`.

## GitHub repository setup

1. Create or fork the GitHub repository.
2. Push this source tree to the `master` branch.
3. In repository settings, enable GitHub Actions.
4. In repository settings, enable packages for GHCR.
5. Keep the `generated` branch protected from manual edits if your workflow
   allows branch rules. The workflow should be the only normal writer.

The VPS does not need GitHub CLI. GitHub Actions builds images and publishes
the generated branch.

## GitHub Actions

The workflow in `.github/workflows/generate.yml` is the release pipeline:

1. Install Python dependencies with uv.
2. Run tests.
3. Run `codervps refresh-catalog`.
4. Run `codervps render-generated`.
5. Build one GHCR image per Node.js major.
6. Write `images.json` only after image builds succeed.
7. Push the generated tree with `--force-with-lease`.

Run it manually from GitHub Actions when you want fresh versions immediately.
The scheduled run refreshes versions dynamically from upstream metadata:
Node.js, Go, Python runtimes, Rust channels, LLVM, uv, code-server, sccache,
and the Coder Ubuntu base tag.

## GHCR

Generated images are pushed to GHCR as:

```text
ghcr.io/guangdai/codervps-devbox:noble-YYYYMMDD-node<major>
```

If you fork the repository, update the image repository used by the workflow and
template generation before relying on the images in Coder.

Checklist:

1. The workflow has permission to write packages.
2. GHCR images are visible to the VPS.
3. The image tags in `generated/catalog/images.json` exist.
4. The Coder template uses `images.json`; it does not use floating `latest`.

## generated branch

The generated branch is publishable output, not source code. It should contain:

```text
generated/catalog/toolchains.json
generated/catalog/images.json
generated/manifest.json
templates/devbox/main.tf
templates/devbox/runtime/
templates/devbox/extensions/
templates/devbox/vsix/
```

When debugging generation locally:

```bash
env UV_CACHE_DIR=.uv-cache uv run codervps refresh-catalog --output build/toolchains.json
env UV_CACHE_DIR=.uv-cache uv run codervps render-generated --catalog build/toolchains.json --output build/generated
env UV_CACHE_DIR=.uv-cache uv run codervps build-matrix --catalog build/toolchains.json --format json
```

Use fixture mode when you only want a network-free smoke test:

```bash
env UV_CACHE_DIR=.uv-cache uv run codervps refresh-catalog --fixture-dir tests/fixtures --output build/toolchains.fixture.json
env UV_CACHE_DIR=.uv-cache uv run codervps render-generated --catalog build/toolchains.fixture.json --output build/generated-fixture
```

## Local VPS prerequisites

Install these on the VPS:

1. Docker Engine with Compose plugin.
2. Coder server.
3. Terraform support required by Coder templates.
4. Network access to GHCR.
5. A persistent host directory such as `/opt/coder-cde`.

Create host directories:

```bash
sudo mkdir -p /opt/coder-cde/templates /opt/coder-cde/extensions /opt/coder-cde/vsix /opt/coder-cde/.locks
sudo chown -R "$USER":"$USER" /opt/coder-cde
```

Install the helper:

```bash
./cdev install-self
cdev doctor
```

## Install Coder

Use the official Coder install path for your OS. After Coder starts:

1. Create the first admin user.
2. Confirm the deployment access URL is correct.
3. Confirm Docker workspaces can pull GHCR images.
4. Confirm Coder can run Terraform provision jobs.

The template in this repository intentionally does not mount the host Docker
socket into workspaces.

## Template sync

Get the latest generated branch output onto the VPS. One simple path is:

```bash
git clone --branch generated <your-repo-url> /tmp/codervps-generated
cdev check-generated /tmp/codervps-generated
cdev sync-generated /tmp/codervps-generated
cdev push-template
```

`cdev sync-generated` stages the new tree, validates it, and switches the live
template directory under an `flock` lock. It is safer than manually editing
files under `/opt/coder-cde/templates`.

## VSIX

Marketplace extension IDs are generated into the template. Local `.vsix`
binaries are operator-managed and are not committed to git.

Put files here on the VPS:

```text
/opt/coder-cde/vsix/core/
/opt/coder-cde/vsix/python/
/opt/coder-cde/vsix/rust/
/opt/coder-cde/vsix/go/
/opt/coder-cde/vsix/cpp/
/opt/coder-cde/vsix/packs/<pack-name>/
```

The generated template mounts these directories read-only into workspaces at
`/opt/cde/vsix`.

## Creating a workspace

In the Coder UI:

1. Pick the CoderVPS template.
2. Pick the Node.js major.
3. Enable the languages you want with the `Enable Python`, `Enable Go`,
   `Enable Rust`, and `Enable C/C++` checkboxes.
4. For enabled Python, choose a runtime such as `CPython 3.13.13`,
   `CPython 3.13.13 free-threaded`, `PyPy 3.11.15`, or `GraalPy 3.12.0`.
5. Pick optional tools.
6. Create the workspace.

Selections are immutable after workspace creation. Create a new workspace when
you need a different base image or language runtime.

## Troubleshooting

Check local helper status:

```bash
cdev doctor
cdev info
cdev ps
cdev logs
```

Check generated output before syncing:

```bash
cdev check-generated /path/to/generated-tree
cdev check-images /path/to/generated-tree
```

Check Coder-managed volumes without deleting anything:

```bash
cdev list-workspace-volumes
```

Do not run `docker volume prune` on a Coder host unless you have already
confirmed the target workspaces were deleted in Coder. Stopped workspaces can
look unused to Docker while still containing active user data.

If Python runtime installation fails, check the selected value in
`/home/coder/.cdev/selection.json` and the startup logs. Runtime values should
look like `cpython@3.13.13`, `cpython@3.13.13+freethreaded`, `pypy@3.11.15`,
or `graalpy@3.12.0`.
