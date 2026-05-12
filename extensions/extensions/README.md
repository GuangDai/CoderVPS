# Extension catalog

These files are mounted into every Coder workspace at `/opt/cde/extensions`.

Profiles:
- `core`: installs `core.txt`
- `rust`: installs `core.txt + rust.txt`
- `cpp`: installs `core.txt + cpp.txt`
- `go`: installs `core.txt + go.txt`
- `python`: installs `core.txt + python.txt`
- `full`: installs all lists

Put manually downloaded `.vsix` files into `/opt/coder-cde/vsix`, then restart a workspace.
The startup script fingerprints these files and lists; changed catalogs are installed on next workspace start.
