# CoderVPS Agent Instructions

This repository is a refactor project for a Coder-based VPS development
environment. Treat the existing scripts and templates as legacy context, not as
the final architecture.

## Required Workflow

- Read the relevant documentation and the current refactor plan before changing
  code. Do not implement from memory when a plan or design document exists.
- If there is no real git repository, initialize one before project work.
- At the start of every work session, check the working tree. If files are
  modified or untracked, track and commit them before making new changes.
- Keep commits small and intentional. Commit documentation, plans, and code
  changes separately when that makes review easier.
- Never overwrite, revert, or discard user changes unless explicitly requested.

## Deletion Safety

- Delete files only with `/bin/rm`.
- On this VPS, `/bin/rm` is the required safe-rm entry point. Do not use plain
  `rm`, `trash`, `gio trash`, `find -delete`, `git clean`, editor delete
  actions, or other deletion helpers.
- Before any deletion, confirm the path is inside this project and is not a user
  workspace or persistent data directory.

## Refactor Direction

- The project should become configurable rather than profile-only. Users should
  be able to select languages and then select only the version/tool options that
  apply to those languages.
- Coder images should be built in GitHub and pulled by Coder. The image matrix
  should cover supported Coder Ubuntu bases and the intended Node.js LTS
  channels.
- Runtime persistence should be minimal. Keep external persistence focused on
  the workspace directory; avoid persisting toolchain internals unless a plan
  explicitly justifies it.
- Treat compiler and package-manager caches as disposable by default. Prefer
  project-scoped caches inside the workspace when persistence is needed. Do not
  add cross-workspace shared caches unless the plan explains the isolation,
  cleanup, and correctness risks.
- Do not assume nested workspaces or workspace-inside-workspace layouts are
  valid. Validate this with Coder behavior before designing around it.
- Toolchain versions should be refreshable from authoritative sources whenever
  practical, instead of being hardcoded by hand.
- Version catalogs must include legacy and EOL toolchain versions when the
  upstream source still exposes installable artifacts. Mark them as legacy/EOL
  in the UI or metadata, but do not remove them only because they are no longer
  supported.
- Every generated image must include the system baseline needed for development
  on that OS family: Git, certificates, shell utilities, SSH client, sudo/user
  setup, archive tools, and the distro's base build/development package set
  such as Ubuntu `build-essential`, `pkg-config`, `make`, CMake, and Ninja where
  appropriate. Language-specific heavyweight toolchains remain configurable, but
  the base development substrate is mandatory.
- Language manager and bootstrap tools must be baked into images, not installed
  from scratch during workspace startup. Examples include `uv`/`uvx` for Python
  management, Rust bootstrap tooling such as `rustup` and an image-provided
  Rust compiler/toolchain baseline, and equivalent installers or resolvers for
  other configurable languages. Workspace startup may resolve and install the
  user-selected concrete language versions, but it should not spend time
  installing the managers themselves.

## Documentation Expectations

- Prefer official, current documentation for Coder, base images, Node.js, uv,
  Rust, Go, LLVM, and other toolchains.
- Record important assumptions in the plan or design document with source links
  when the information can change over time.
- Keep the legacy `cdev` script understandable while it is still present, but do
  not expand it into the new architecture without a plan.
