# Generated Branch

The `generated` branch contains the publishable output of the CoderVPS generator.
It is the branch consumed by the VPS -- it does not contain source code, config,
or the generator itself.

## Directory Structure

```
generated/
  catalog/
    toolchains.json      # resolved tool and language versions
    images.json          # image tag -> GHCR reference mapping
  manifest.json          # data lineage: source commit, workflow run, versions
templates/
  devbox/
    main.tf         # rendered Coder Terraform HCL template
    startup.sh           # Coder entrypoint script
    runtime/
      startup.sh         # runtime entrypoint
      lib/
        actions.sh       # action executor dispatcher
        run_actions.py   # Python action executor
        extensions.sh    # extension installer
      plugins/
        python.sh, rust.sh, go.sh, cpp.sh
    extensions/
      core.txt, python.txt, rust.txt, go.txt, cpp.txt
      packs/<pack>.txt
    vsix/
      core/README.md, python/README.md, ...
      packs/<pack>/README.md
```

## Publishing Flow

1. The monthly GitHub Actions workflow checks out `master`.
2. `uv run codervps refresh-catalog --output build/toolchains.json`
3. `uv run codervps render-generated --catalog build/toolchains.json --output build/generated`
4. Images are built and pushed to GHCR.
5. `images.json` is written only after all images succeed.
6. The generated tree is committed to the `generated` branch via `--force-with-lease`.

Catalog discovery sources and fixture rules are documented in
[`catalog-discovery.md`](catalog-discovery.md). Generated catalog values should
come from those sources or explicit config overrides, not placeholders.

## Safety Rules

- The `generated` branch is pushed with `--force-with-lease`, never bare `--force`.
- Cleanup commands exclude `.git` to preserve the repository.
- Date tags are immutable -- the workflow checks tag existence before pushing.
- A concurrency group prevents two workflow runs from publishing simultaneously.
