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
- Toolchain versions should be refreshable from authoritative sources whenever
  practical, instead of being hardcoded by hand.

## Documentation Expectations

- Prefer official, current documentation for Coder, base images, Node.js, uv,
  Rust, Go, LLVM, and other toolchains.
- Record important assumptions in the plan or design document with source links
  when the information can change over time.
- Keep the legacy `cdev` script understandable while it is still present, but do
  not expand it into the new architecture without a plan.
