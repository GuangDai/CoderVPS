# CoderVPS

Pluginized Coder-based VPS development environment with GitHub-built images
and isolated workspace runtimes.

## Branch Model

- **`master`** -- source code: Python generator (`codervps/`), config (`config/`),
  Dockerfile (`docker/`), runtime shell modules (`runtime/`), tests, workflows.
- **`generated`** -- publishable output: rendered Terraform JSON, catalogs,
  extension lists, images.json, runtime files. The VPS consumes this branch;
  it does not run the generator.

## Build Pipeline

A GitHub Actions workflow runs monthly (or manually via `workflow_dispatch`) to:

1. Check out `master`, install dependencies, run tests.
2. Refresh the toolchain catalog (`toolchains.json`).
3. Render the full generated branch tree.
4. Build and push five `linux/amd64` Docker images to GHCR.
5. Write `images.json` after all images succeed.
6. Publish the generated output to the `generated` branch.

GitHub CLI is not required on the VPS. The VPS consumes what the
workflow publishes.

## GHCR Tag Pattern

Images are tagged as:

```
ghcr.io/guangdai/codervps-devbox:noble-YYYYMMDD-node<major>
```

Example shape: `noble-YYYYMMDD-node24`

Date tags are immutable. The Coder template uses tags from `images.json`, not
floating `latest` tags.

Toolchain and base-image metadata is resolved by `refresh-catalog`; see
[`docs/catalog-discovery.md`](docs/catalog-discovery.md) for the authoritative
sources and sccache asset policy.

For a full GitHub-to-VPS operator walkthrough, see
[`docs/deployment-guide.md`](docs/deployment-guide.md).

## VPS Operations (`cdev`)

The `cdev` script is a thin VPS helper. Key commands:

```bash
cdev info                        # configuration summary
cdev doctor                      # full health check
cdev ps                          # Docker Compose service status
cdev logs [service]              # tail logs
cdev restart [service]           # restart services
cdev template-dir                # print active template directory
cdev push-template               # push template to Coder
cdev sync-generated <dir>        # atomically update template from generated tree
cdev check-generated [dir]       # validate a generated template tree
cdev check-images [dir]          # verify images exist in registry
cdev list-workspace-volumes      # list Coder-managed volumes (never deletes)
cdev install-self                # install cdev to /usr/local/bin
```

`sync-generated` writes into a temporary directory, validates with
`check-generated`, then atomically switches the live template directory
under an `flock` lock at `/opt/coder-cde/.locks`.

`cdev` does **not** build Docker images, patch template source files, or run
the catalog generator. Those actions happen in GitHub Actions.

## Workspace Lifecycle

- Each workspace owns one persistent Docker volume mounted at `/workspace`.
  All toolchain data, caches, and downloads live under `/workspace/.cdev`.
- Language and version selections are immutable after workspace creation.
- Normal Coder workspace deletion destroys the volume through Terraform destroy.
- The volume uses `lifecycle { ignore_changes = all }` to prevent accidental
  drift -- but `prevent_destroy` is **not** used, so normal deletion works.
- The host Docker socket is not mounted into workspaces (v1).

### Volume Cleanup

`docker volume prune`, `docker system prune --volumes`, and `docker volume rm`
are **not** normal cleanup tools for Coder-managed workspace volumes. Stopped
Coder workspaces may have no running container attached to their persistent
volume, so Docker sees the volume as unused even though Terraform still manages
it. Running prune would destroy active workspace data.

List volumes by Coder labels for diagnostics:

```bash
cdev list-workspace-volumes
```

This command is read-only. Manual volume deletion is a recovery operation and
should only be performed when the corresponding Coder workspace has already
been deleted from Coder.

## Workspace Directory Layout

```
/workspace/
  <user projects>
  .cdev/
    selection.json
    runtime-plan.json
    env.sh
    downloads/
    tmp/
    toolchains/
      python/
      rust/
      go/
      llvm/
    cache/
      uv/
      cargo/
      go/
      ccache/
      sccache/
    locks/
      startup.lock
    state/
    logs/
```
