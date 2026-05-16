# VSIX Extensions

VSIX (.vsix) extension files are managed on the VPS filesystem and are never
committed to git.

## Directory Layout

On the VPS:

```
/opt/coder-cde/vsix/
  core/           # always-installed extensions
  python/         # Python language extensions
  rust/           # Rust language extensions
  go/             # Go language extensions
  cpp/            # C/C++ language extensions
  packs/
    <pack-name>/  # extra extension pack VSIX files
```

In the generated branch:

```
templates/devbox/vsix/
  core/README.md, python/README.md, rust/README.md, go/README.md, cpp/README.md
  packs/<pack-name>/README.md
```

Only README.md marker files exist in git. .vsix files are not committed.
The VPS operator places `.vsix` files in the corresponding directories under
`/opt/coder-cde/vsix/`, and the workspace startup process installs them from
there.

Workspace containers see these directories as read-only mounts at
`/opt/cde/vsix/`.

## Rationale

- `.vsix` files are large binaries that should not bloat the git repository.
- They are managed by the VPS operator, not the generator.
- The README files in git serve as documentation markers for the directory
  structure.
- Extension marketplace IDs (defined in `config/extensions.toml`) are the
  primary extension source; VSIX files are an override/supplement mechanism.
