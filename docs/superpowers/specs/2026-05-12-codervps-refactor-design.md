# CoderVPS Refactor Design

Date: 2026-05-12

## Goal

Refactor CoderVPS into a GitHub-built, plugin-driven Coder workspace system that balances disk usage with startup time. The VPS should run Coder and pull prebuilt images; it should not build images locally, run the catalog generator, or need the GitHub CLI.

## Non-Goals

- Do not build custom non-Coder Ubuntu base images in the first version.
- Do not persist `/home/coder`.
- Do not share toolchain or compiler caches across workspaces.
- Do not support ARM images in the first version.
- Do not commit `.vsix` binaries to git.
- Do not keep legacy `cdev` patch/build behavior.

## Confirmed Decisions

- Use a pluginized Python generator managed by `uv`.
- Use only official Coder base images. If official Ubuntu 22.04 Coder base tags are not available, do not self-build Ubuntu 22.04 for first version.
- Resolve and pin the official Coder base date tag during monthly automation.
- Build one image matrix: official Coder base date x Node `24/22/20/18/16`.
- Node is a base-image parameter, not a language plugin.
- Use human-readable GHCR tags with date and Node major. Do not require digest references in Coder templates.
- First version supports four language plugins: Python, Rust, Go, and C/C++.
- Language and version selections are immutable after workspace creation.
- Each workspace owns one persistent Docker volume mounted at `/workspace`.
- The persistent volume is deleted only through normal Coder workspace deletion. Orphan deletion is not a supported normal workflow.
- `generated` branch is the directly publishable branch for Coder templates and generated catalog data.
- `.vsix` files are managed on the VPS filesystem, not in git.
- `cdev` becomes a thin VPS operations helper.

## Source References

- Coder Dynamic Parameters support conditional inputs, multi-select, and local JSON/locals instead of HTTP fetching at workspace build time: https://coder.com/docs/admin/templates/extending-templates/dynamic-parameters
- Coder resource persistence recommends `start_count` for ephemeral resources and immutable workspace IDs plus `ignore_changes = all` for persistent resources: https://coder.com/docs/admin/templates/extending-templates/resource-persistence
- Coder workspace deletion runs Terraform destroy and deletes persistent and ephemeral resources; orphan deletion is an exceptional escape hatch: https://coder.com/docs/user-guides/workspace-lifecycle
- Coder image management recommends managing images intentionally through templates: https://coder.com/docs/admin/templates/managing-templates/image-management
- Coder's official images repository recommends `codercom/example-base` for new deployments and documents `enterprise-*` as a backward-compatible prefix: https://github.com/coder/images
- Docker Hub exposes date-pinned `codercom/example-base` Ubuntu tags such as `ubuntu-noble-YYYYMMDD`: https://hub.docker.com/r/codercom/example-base/tags
- Node release metadata is the source of supported and EOL release-line status: https://github.com/nodejs/Release
- uv supports managed Python installs, version requests, and free-threaded CPython 3.13+: https://docs.astral.sh/uv/concepts/python-versions/
- Go release downloads are discoverable from Go's JSON endpoint: https://go.dev/dl/?mode=json
- apt.llvm.org provides Ubuntu Noble LLVM/clangd package channels and current default packages: https://apt.llvm.org/
- Docker volumes live outside a container's lifecycle and are not removed automatically when containers are removed: https://docs.docker.com/engine/storage/volumes/
- Docker prune commands are explicitly destructive for unused data and volume pruning must not be used for Coder-managed workspace volumes: https://docs.docker.com/engine/manage-resources/pruning/
- Docker documents the Docker daemon socket as a protected control surface, so workspaces must not mount the host socket in version 1: https://docs.docker.com/engine/security/protect-access/
- Terraform `.tf.json` is supported for generated configuration and has specific JSON mappings for lifecycle meta-arguments: https://developer.hashicorp.com/terraform/language/syntax/json
- Terraform `ignore_changes` can protect persistent resources from update drift but does not prevent destroy when the resource is intentionally destroyed: https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle
- GitHub Actions concurrency must be used to serialize generated-branch publishing: https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency
- GHCR supports publishing from Actions with `GITHUB_TOKEN` when the package is associated with the workflow repository: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- Docker Buildx/build-push action supports build args, tags, platforms, cache settings, and push control from workflow YAML: https://github.com/docker/build-push-action
- uv recommends the official `astral-sh/setup-uv` action for GitHub Actions and documents pinning uv versions: https://docs.astral.sh/uv/guides/integration/github/
- code-server supports version-pinned installation and standalone releases: https://coder.com/docs/code-server/install
- rustup components such as `rustfmt`, `clippy`, and `rust-src` are managed per toolchain and may vary by toolchain availability: https://rust-lang.github.io/rustup/concepts/components.html
- rustup profiles explain the difference between minimal/default component sets: https://rust-lang.github.io/rustup/concepts/profiles.html
- rustup environment variables such as `RUSTUP_HOME` control installation roots: https://ehuss.github.io/rustup/environment-variables.html
- `gopls` documents its own Go-version support window and final versions for older Go releases: https://go.dev/gopls/
- Go module docs define `go install module@version` behavior for installing tools like `gopls` and `dlv`: https://go.dev/ref/mod

## Branch Model

`main` is the source branch. It contains:

- `pyproject.toml`, `uv.lock`, and generator source.
- `codervps/` Python package.
- `codervps/plugins/{python,rust,go,cpp}/`.
- `config/toolchains.toml`.
- `config/extensions.toml`.
- `docker/Dockerfile`.
- `runtime/` shell modules.
- GitHub Actions workflows.
- Tests and documentation.

`generated` is the publishable branch. It contains:

- `generated/catalog/toolchains.json`.
- `generated/catalog/images.json`.
- `generated/manifest.json`.
- `templates/devbox/main.tf.json`.
- `templates/devbox/startup.sh`.
- `templates/devbox/runtime/startup.sh`.
- `templates/devbox/runtime/lib/actions.sh`.
- `templates/devbox/runtime/lib/extensions.sh`.
- `templates/devbox/runtime/plugins/python.sh`.
- `templates/devbox/runtime/plugins/rust.sh`.
- `templates/devbox/runtime/plugins/go.sh`.
- `templates/devbox/runtime/plugins/cpp.sh`.
- `templates/devbox/extensions/core.txt`.
- `templates/devbox/extensions/{python,rust,go,cpp}.txt`.
- `templates/devbox/extensions/packs/*.txt`.
- `templates/devbox/vsix/{core,python,rust,go,cpp,packs}/` directory structure and README files only.

The monthly workflow runs from `main`, writes generated output, pushes images, then updates `generated`. The VPS consumes `generated`; it does not run the generator.

## High-Level Data Flow

1. Source configuration and plugins define supported languages, defaults, overrides, and extension packs.
2. The generator discovers upstream metadata and creates `toolchains.json`.
3. The generator renders `main.tf.json`, runtime files, extension files, and directory structure.
4. GitHub Actions builds GHCR images from `docker/Dockerfile` using build args from `toolchains.json`.
5. After all images are pushed, the workflow writes `images.json`.
6. Coder uses `main.tf.json` and `images.json` from `generated`.
7. Workspace startup reads immutable selections and executes plugin runtime actions into `/workspace/.cdev`.

## Python Generator

The generator is a `uv` project. The project must avoid syntax that requires Python 3.12 or 3.13. `requires-python` must target a broad supported range such as `>=3.11`, while `.python-version` may stay at the developer's local default.

Primary CLI commands:

- `codervps refresh-catalog`
- `codervps render-template`
- `codervps render-dockerfile-context`
- `codervps build-matrix`
- `codervps validate`

The generator produces structured data first and shell/Terraform output second. Plugins do not directly write Terraform or large shell scripts.

## Plugin Interface

Plugins are Python classes or Protocol implementations backed by dataclasses.

Core interface:

```python
class ToolchainPlugin(Protocol):
    id: str
    label: str

    def discover(self, ctx: DiscoveryContext) -> PluginCatalog:
        raise NotImplementedError

    def image_requirements(self, catalog: PluginCatalog) -> ImageRequirements:
        raise NotImplementedError

    def coder_parameters(self, catalog: PluginCatalog) -> list[ParameterSpec]:
        raise NotImplementedError

    def runtime_plan(self, selection: Selection) -> RuntimePlan:
        raise NotImplementedError
```

Important DTOs:

- `DiscoveryContext`: date, architecture, base image metadata, config overrides, HTTP/cache helper.
- `PluginCatalog`: versions, defaults, status labels, download metadata, parameter metadata.
- `ImageRequirements`: apt packages, bootstrap tools, Docker build args, prebundled assets.
- `ParameterSpec`: Coder parameter type, options, default, order, condition, mutability.
- `RuntimePlan`: environment, actions, verification, diagnostics.

First-version plugins:

- Python
- Rust
- Go
- C/C++

Future languages should be added by implementing the same interface and enabling the plugin in `config/toolchains.toml`.

## Runtime Action Model

Runtime work is expressed as structured actions, not opaque command strings.

Supported action types in the first version:

- `ensure_dir`
- `download`
- `extract_tar`
- `run`
- `path_prepend`
- `env`
- `symlink`
- `write_file`
- `verify_command`

Every action must have:

- `id`
- `type`
- idempotency via `creates` or verification
- `critical`
- a deterministic log path under `/workspace/.cdev/logs`

Example action plan:

```json
{
  "plugin": "go",
  "selection": {
    "version": "1.22.12",
    "tools": ["gopls"]
  },
  "actions": [
    {
      "id": "download-go",
      "type": "download",
      "url": "https://go.dev/dl/go1.22.12.linux-amd64.tar.gz",
      "sha256": "sha256-from-go-metadata",
      "dest": "/workspace/.cdev/downloads/go1.22.12.tar.gz"
    },
    {
      "id": "extract-go",
      "type": "extract_tar",
      "src": "/workspace/.cdev/downloads/go1.22.12.tar.gz",
      "dest": "/workspace/.cdev/toolchains/go/1.22.12",
      "strip_components": 1,
      "creates": "/workspace/.cdev/toolchains/go/1.22.12/bin/go"
    },
    {
      "id": "activate-go",
      "type": "path_prepend",
      "path": "/workspace/.cdev/toolchains/go/1.22.12/bin"
    },
    {
      "id": "verify-go",
      "type": "verify_command",
      "command": ["go", "version"],
      "contains": "go1.22.12"
    }
  ]
}
```

## Source Configuration

Use TOML for source configuration so Python can read it with the standard library.

`config/toolchains.toml`:

```toml
[project]
arch = "linux/amd64"

[node]
majors = [24, 22, 20, 18, 16]

[plugins]
enabled = ["python", "rust", "go", "cpp"]

[versions.override]
uv = ""
code_server = ""
sccache = ""
rust_bootstrap = ""
llvm_prebundle = ""

[python]
min_minor = "3.6"
max_minor = "latest"
default = "3.13"
default_tools = ["ruff", "debugpy"]
optional_tools = ["ipython", "jupyter"]

[rust]
stable_minor_count = 30
default = "stable"
default_components = ["rustfmt", "clippy", "rust-src"]
use_sccache = true

[go]
minor_count = 20
default = "latest"
default_tools = ["gopls"]

[cpp]
default_llvm = "latest"
prebundle = "latest"
default_tools = ["xmake", "ccache"]
```

`config/extensions.toml`:

```toml
[core]
marketplace = ["EditorConfig.EditorConfig", "redhat.vscode-yaml"]

[language.python]
marketplace = ["ms-python.python", "ms-python.debugpy", "charliermarsh.ruff"]

[language.rust]
marketplace = ["rust-lang.rust-analyzer", "vadimcn.vscode-lldb"]

[language.go]
marketplace = ["golang.Go"]

[language.cpp]
marketplace = [
  "llvm-vs-code-extensions.vscode-clangd",
  "vadimcn.vscode-lldb",
  "tboox.xmake-vscode"
]

[packs.leetcode]
label = "LeetCode"
marketplace = ["leetcode.vscode-leetcode"]
vsix_globs = ["packs/leetcode/*.vsix"]
```

Extra extension packs are immutable workspace creation parameters. User-installed extensions inside code-server are not managed by this system.

## Generated Catalogs

`toolchains.json` stores version and tool metadata:

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-12T00:00:00Z",
  "arch": "linux/amd64",
  "base": {
    "source": "codercom/example-base",
    "ubuntu": "noble",
    "tag": "ubuntu-noble-20260511"
  },
  "node": {
    "majors": {
      "24": {"version": "24.11.1", "status": "active_lts"},
      "22": {"version": "22.21.0", "status": "maintenance_lts"},
      "20": {"version": "20.19.5", "status": "eol"}
    }
  },
  "plugins": {
    "python": {"versions": [], "defaults": {}},
    "rust": {"versions": [], "defaults": {}},
    "go": {"versions": [], "defaults": {}},
    "cpp": {"versions": [], "defaults": {}}
  },
  "tools": {
    "uv": {"version": "resolved-uv-version"},
    "code_server": {"version": "resolved-code-server-version"},
    "sccache": {"version": "resolved-sccache-version"},
    "llvm_prebundle": {"version": "resolved-llvm-version"}
  }
}
```

`images.json` maps Coder parameters to GHCR tags:

```json
{
  "schema_version": 1,
  "images": [
    {
      "base_key": "noble",
      "base_tag": "ubuntu-noble-20260511",
      "node_major": 24,
      "node_version": "24.11.1",
      "image": "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24"
    }
  ]
}
```

Catalogs are committed to the `generated` branch, not `main`.

`generated/manifest.json` records the data lineage for the generated branch:

```json
{
  "schema_version": 1,
  "source_commit": "main-commit-sha",
  "workflow_run_id": "github-actions-run-id",
  "generator_version": "0.1.0",
  "generated_at": "2026-05-12T00:00:00Z",
  "coder_base": {
    "source": "codercom/example-base",
    "tag": "ubuntu-noble-20260511"
  },
  "node_versions": {
    "24": "24.11.1"
  },
  "tool_versions": {
    "uv": "resolved-uv-version",
    "code_server": "resolved-code-server-version",
    "sccache": "resolved-sccache-version",
    "llvm_prebundle": "resolved-llvm-version"
  },
  "image_tags": [
    "ghcr.io/guangdai/codervps-devbox:noble-20260511-node24"
  ]
}
```

## Runtime Source Layout

Runtime shell files are maintained as source in `main` and copied into generated templates. The root `templates/devbox/startup.sh` is a thin Coder entrypoint that exports the Coder selection values and calls `runtime/startup.sh`. The runtime entrypoint loads `runtime/lib/actions.sh`, `runtime/lib/extensions.sh`, and selected plugin modules from `runtime/plugins/`.

The Python generator may write selection JSON and action-plan JSON, but it must not synthesize large opaque shell scripts from scratch.

## Image Strategy

The image matrix is:

- official Coder base pinned date tag
- Node majors `24`, `22`, `20`, `18`, `16`
- architecture `linux/amd64`

GHCR image package:

- `ghcr.io/guangdai/codervps-devbox`

Example tags:

- `noble-20260511-node24`
- `noble-20260511-node22`
- `noble-20260511-node20`
- `noble-20260511-node18`
- `noble-20260511-node16`

Old date tags must not be moved. The template uses the tag listed in `images.json`. Convenience latest tags may exist, but Coder templates must not depend on them.

The Dockerfile is source-controlled, not fully generated. It accepts build args for:

- Coder base image pinned tag
- Node patch version
- uv version
- code-server version
- rustup or Rust bootstrap version
- sccache version
- latest LLVM/clangd prebundle version

Every image must include:

- Git
- certificates
- shell utilities
- SSH client
- sudo/user setup
- archive tools
- Ubuntu `build-essential`
- `pkg-config`
- `make`
- CMake
- Ninja
- baseline C/C++ tools
- xmake
- ccache
- uv/uvx
- rustup and Rust bootstrap
- sccache
- code-server
- Node for the selected major/latest patch
- latest LLVM/clangd bundle for fast C/C++ default startup

Concrete old language versions are not baked into the image. They are installed into the workspace volume when selected.

## GitHub Actions

Triggers:

- monthly schedule
- manual `workflow_dispatch`

No `gh` CLI is required on the VPS.

Workflow:

1. Checkout `main`.
2. `uv sync`.
3. Run tests.
4. Refresh catalog.
5. Render generated template output.
6. Build and push five `linux/amd64` images.
7. Write `images.json` only after all images succeed.
8. Commit generated output to `generated`.

Fail-safe rules:

- If official Coder base, Node versions, or critical tool versions cannot be resolved, fail and do not update `generated`.
- If any image build fails, do not update `images.json`.
- If any first-version plugin catalog refresh fails, fail the workflow. Version 1 has no partial catalog fallback.
- Overrides in `config/toolchains.toml` can pin tool versions when upstream latest is broken.

## Coder Template

Use `main.tf.json`, fully generated from structured data.

Workspace parameters:

- `node_major`: immutable, options `24/22/20/18/16`.
- `languages`: immutable multi-select, options `python/rust/go/cpp`.
- Python parameters appear only when Python is selected.
- Rust parameters appear only when Rust is selected.
- Go parameters appear only when Go is selected.
- C/C++ parameters appear only when C/C++ is selected.
- `extra_extension_packs`: immutable multi-select from `config/extensions.toml`.

Parameters are generated with Coder Dynamic Parameters and local JSON/catalog data. The template must not fetch HTTP metadata during workspace creation.

## Workspace Persistence And Isolation

Data isolation is a hard standard.

Rules:

- Do not share persistent volumes across workspaces.
- Do not share toolchains or caches across workspaces.
- Do not name volumes with usernames or workspace names.
- Use immutable `data.coder_workspace.me.id` in persistent resource names.
- Use one Terraform-managed Docker volume per workspace.
- Mount it at `/workspace`.
- Do not persist `/home/coder`.
- Do not write host directories from startup scripts.
- Do not write shared `/opt/cde/cache`.
- Mount `/opt/cde` resources read-only.
- Add labels containing owner and workspace id for diagnostics.
- Do not provide a "keep volume" option.
- Do not mount the host Docker socket in version 1. A Docker socket mount gives the workspace broad host control and can break volume/image isolation.
- Do not run `docker volume prune`, `docker system prune --volumes`, or equivalent cleanup commands as part of normal operations. Stopped Coder workspaces may have no running container attached to their persistent volume, so Docker sees the volume as unused even though Terraform still manages it.
- On the first successful startup, write `/workspace/.cdev/selection.json` and `/workspace/.cdev/selection.sha256`. On later starts, recompute the selection hash and fail before installing tools if immutable parameters changed unexpectedly.

Terraform resource shape:

- `docker_container.workspace` uses `count = data.coder_workspace.me.start_count`.
- `docker_volume.workspace` has no `count`, so it persists while the workspace is stopped.
- `docker_volume.workspace` uses `lifecycle { ignore_changes = all }`.
- Normal Coder workspace deletion destroys the volume through Terraform destroy.

Workspace directory layout:

```text
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
      startup.log
      toolchains/
```

## Language Plugin Behavior

### Python

- Use uv-managed Python installs.
- Catalog covers CPython `3.14` down to `3.6` where uv exposes artifacts for linux/amd64.
- Support free-threaded/no-GIL variants only when available, primarily CPython 3.13+.
- Default tools: `ruff` and `debugpy`.
- Optional tools profile may include `ipython` and `jupyter`, but default remains minimal.
- Install into `/workspace/.cdev/toolchains/python` and cache under `/workspace/.cdev/cache/uv`.

### Rust

- Catalog includes `stable`, `beta`, `nightly`, custom, and latest 30 stable minors.
- Image includes rustup, Rust bootstrap, and sccache.
- Startup installs/activates selected toolchain under `/workspace/.cdev/toolchains/rust`.
- Default components: `rustfmt`, `clippy`, `rust-src`.
- Do not install rust-analyzer binary; the VS Code extension provides editor integration.
- Use sccache by default when Rust is selected.

### Go

- Catalog includes latest 20 Go minors from Go metadata.
- Startup installs selected Go under `/workspace/.cdev/toolchains/go/<version>`.
- Default tool is `gopls`.
- The Go plugin must select a `gopls` version compatible with the selected Go version. It must not blindly use `gopls@latest` for old Go versions because the official gopls support policy only tracks recent Go versions and documents final gopls versions for older Go releases.
- `dlv` is optional.
- Custom exact versions are allowed when metadata exposes downloadable artifacts.

### C/C++

- Base image includes GCC/G++, build essentials, CMake, Ninja, xmake, ccache, and latest LLVM/clangd bundle.
- C/C++ plugin exposes LLVM/clangd version choices from the generated catalog.
- If the selected LLVM version is prebundled, startup activates it quickly.
- If the selected LLVM version is older, startup installs into `/workspace/.cdev/toolchains/llvm/<version>` and reuses it on restart.
- Older LLVM installs must use a generated bundle manifest with the required `.deb` package dependency closure, package checksums, and an activation path. Runtime must not call root-level `apt install`. Extracting a single `clangd-N` package is not enough because LLVM packages have shared-library dependencies.
- xmake follows the C/C++ plugin and is installed in the image.

## Extensions And VSIX

Extension sources:

- `core`: always installed.
- language bundles: installed based on selected languages.
- extra packs: selected at workspace creation.

Marketplace extension IDs and VSIX globs are defined in `config/extensions.toml`.

Generated branch includes:

```text
templates/devbox/extensions/
  core.txt
  python.txt
  rust.txt
  go.txt
  cpp.txt
  packs/
    <pack>.txt
templates/devbox/vsix/
  core/
  python/
  rust/
  go/
  cpp/
  packs/
    <pack-name>/
```

The VPS stores actual `.vsix` files under `/opt/coder-cde/vsix/<category-or-pack>/`. They are not committed to git.

## cdev Role

`cdev` becomes a thin VPS helper.

Keep or add:

- `cdev info`
- `cdev doctor`
- `cdev ps`
- `cdev logs`
- `cdev restart`
- `cdev template-dir`
- `cdev push-template`
- `cdev sync-generated`
- `cdev check-generated`
- `cdev check-images`
- `cdev list-workspace-volumes`
- `cdev install-self`

Remove or deprecate:

- `patch-runtime`
- `clean-main-tf`
- `write-startup`
- `rebuild-devbox`
- local Docker image builds
- local catalog refresh
- template source patching

Script deletion must be path-scoped, explicit, and covered by tests when it can
touch generated templates or workspace data. The `/bin/rm` safe-rm rule is an
agent/operator command rule for this VPS, not a product implementation rule.

## Testing Strategy

Python generator tests:

- TOML config parsing.
- Plugin discovery with mocked upstream data.
- Catalog schema validation.
- Override precedence.
- `main.tf.json` structural validation.
- Runtime action plan generation.
- Golden tests: fixed fake catalog to fixed generated output.

Runtime shell tests:

- action executor idempotency.
- extension list composition.
- all cache/toolchain paths remain under `/workspace/.cdev`.
- no writes to `/opt/cde/cache`, host paths, or shared cache roots.

Workflow tests:

- dry-run generated output without pushing images.
- build matrix validation.
- fail-safe behavior when metadata resolution or image build fails.

Static checks:

- `uv run pytest`.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `shellcheck` for runtime scripts where available.

## Risk Review Addendum

This section records the design review performed after the first implementation plan was written.

### Data Flow And Atomicity

- `toolchains.json` and `images.json` must be generated as a matched pair. `images.json` is written only after every image in the matrix has been built and pushed successfully.
- Generated manifests must include the source commit SHA, workflow run id, generator version, Coder base tag, Node patch versions, tool versions, and the image tags produced.
- The monthly workflow must use a GitHub Actions concurrency group so two runs cannot publish the `generated` branch at the same time.
- Publishing the `generated` branch must use `--force-with-lease`, not plain `--force`.
- Generated-branch cleanup must never delete `.git`; any cleanup command must exclude `.git` and operate only inside the temporary generated-branch checkout.
- Date tags such as `noble-20260511-node24` are immutable. Before pushing, the workflow must check whether each tag already exists in GHCR. If it exists, the workflow fails unless a manual workflow input explicitly allows rebuilding that exact tag.
- Coder templates consume date tags from `images.json`; they do not use floating `latest` tags.

### Runtime Integrity

- Startup must acquire an exclusive lock under `/workspace/.cdev/locks/startup.lock` before running toolchain actions.
- Downloads must use `*.part` files and be atomically renamed only after checksum verification.
- Extract actions must unpack into a temporary directory under `/workspace/.cdev/tmp`, verify the tool, then atomically rename into `/workspace/.cdev/toolchains/...`.
- The action executor must reject any write path outside `/workspace/.cdev`, except for code-server user config under the ephemeral `/home/coder` runtime home.
- Runtime actions must be idempotent and must record completion markers under `/workspace/.cdev/state`.
- A failed critical action must stop startup before changing PATH to a partially installed toolchain.

### Data Isolation

- Every cache path must be explicitly set to `/workspace/.cdev/cache/...` or intentionally left ephemeral under `/home/coder`.
- Python must set `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `UV_TOOL_DIR`, and `UV_TOOL_BIN_DIR`.
- Rust must set `RUSTUP_HOME`, `CARGO_HOME`, `CARGO_INSTALL_ROOT`, and `SCCACHE_DIR`.
- Go must set `GOROOT` through the selected install path, `GOBIN`, `GOCACHE`, `GOMODCACHE`, and `GOPATH` under `/workspace/.cdev`.
- C/C++ must set `CCACHE_DIR` and activate selected LLVM paths without writing to `/usr`.
- Node package-manager caches may be ephemeral, but if persisted they must use `/workspace/.cdev/cache/node`.

### Lifecycle And Operations

- `ignore_changes = all` protects persistent volume attributes from accidental drift, but it does not protect against intentional Terraform destroy. This is correct because normal Coder workspace deletion must remove the workspace volume.
- Do not use Terraform `prevent_destroy` for the workspace volume. It would block normal Coder Delete workspace cleanup.
- `cdev` must not offer a cleanup command that deletes Coder-managed volumes. It may list suspicious orphaned volumes by label, but deletion remains a manual recovery operation.
- `cdev sync-generated` must write into a temporary directory, validate structure, and then atomically switch the template directory. It must use a lock under `/opt/coder-cde/.locks`.
- `cdev push-template` must only push a validated generated template tree.

### Supply Chain And Download Integrity

- Prefer package-manager signatures or official checksums for all build-time and runtime downloads.
- Node tarballs must be verified against Node's official `SHASUMS256.txt`.
- Go tarballs must be verified against `go.dev/dl` metadata.
- sccache releases must use release checksums when available; if a checksum is unavailable for a platform, the generator must fail unless an override explicitly accepts that version.
- code-server must be installed with an explicit version. The implementation may use the official install script with `--version`, but the safer path is to download a release package or archive and verify it when official checksums are available.
- xmake installation must prefer a packaged or pinned release path. If the shell installer is used, it must be version-pinned and treated as a build-time only operation.
- apt.llvm.org packages rely on the repository signing key and apt metadata. Runtime extraction of old LLVM bundles must use a generated checksum manifest.

## Implementation Constraints

- Official Coder base tag discovery must use the configured Coder base repository, defaulting to `codercom/example-base`, and must resolve a concrete pinned Ubuntu Noble date tag before building images. `codercom/enterprise-base` may be used only as an explicit compatibility override.
- code-server latest-version discovery must use the official code-server release source or the official installer metadata, and the result must be overridable in `config/toolchains.toml`.
- Latest LLVM/clangd is installed into the image from apt.llvm.org packages. Older selected LLVM/clangd versions are installed under `/workspace/.cdev/toolchains/llvm/<version>` from generated bundle manifests that include the required `.deb` dependency closure and checksums. Runtime may extract packages with `dpkg-deb -x`, but it must not run root-level `apt install` during workspace startup.
- Version 1 must fail clearly rather than publishing partial generated output.
