# Catalog Discovery

`codervps refresh-catalog` resolves toolchain and image metadata from upstream
sources each time the generated branch is refreshed. The source tree must not
contain fake versions, fake hashes, or `"auto"` placeholders for values that are
consumed by image builds or runtime installers.

## Upstream Sources

- Coder Ubuntu base images: Docker Hub `codercom/example-base` tags. The catalog
  selects the newest date-pinned tag matching `ubuntu-<codename>-YYYYMMDD` and
  ignores floating tags such as `ubuntu-noble`.
- Node.js: `https://nodejs.org/dist/index.json`.
- Go: `https://go.dev/dl/?mode=json&include=all`; the Linux amd64 archive
  SHA256 is copied into each Go version entry.
- Python: `uv python list --only-downloads --all-versions --output-format json`.
  The catalog keeps the latest downloadable Linux x86_64 GNU entry per
  implementation/minor/variant for CPython, PyPy, and GraalPy. Runtime values
  use stable uv request strings such as `cpython@3.13.13`,
  `cpython@3.13.13+freethreaded`, `pypy@3.11.15`, and `graalpy@3.12.0`.
  The raw uv list key is stored only as `uv_key` metadata for traceability.
- Rust: `https://static.rust-lang.org/dist/channel-rust-stable.toml`; stable,
  beta, nightly, and recent stable minor channels are derived from the stable
  manifest.
- LLVM: `https://apt.llvm.org/`; the Ubuntu suite page is parsed for the current
  snapshot toolchain and published versioned toolchains.
- uv, code-server, and sccache: GitHub latest release metadata from
  `astral-sh/uv`, `coder/code-server`, and `mozilla/sccache`.

## sccache Asset Policy

The Dockerfile does not guess the sccache release target. Discovery chooses an
asset for the configured architecture and stores the exact asset filename,
target triple, and release SHA256 in the catalog. For `linux/amd64`, discovery
prefers a GNU target if the release publishes one and otherwise uses the
available musl target. The build receives the filename through `SCCACHE_ASSET`
and verifies the digest before installing.

This keeps the musl decision localized to discovery data. If upstream starts
publishing a better Linux amd64 asset, the next catalog refresh can switch
without editing the Dockerfile.

## Fixture Rules

Tests use fixtures under `tests/fixtures/` so they do not depend on network
availability. Fixture values must be real metadata copied from the upstream
shape, including real 64-character SHA256 values where the value is consumed by
downloads.
