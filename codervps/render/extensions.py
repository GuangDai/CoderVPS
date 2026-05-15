"""Render extension list files and VSIX directory README markers.

Writes marketplace extension IDs (one per line, sorted) for core, each enabled
language, and each configured extension pack. Creates VSIX directory README.md
files as placeholders -- actual .vsix binaries are managed on the VPS filesystem
only and are never committed to git.
"""

from __future__ import annotations

from pathlib import Path

from codervps.models import ExtensionsConfig

_LANGUAGES = ["python", "rust", "go", "cpp"]


def render_extensions(cfg: ExtensionsConfig, output_dir: Path) -> None:
    """Write extension list files and VSIX directory README markers.

    Produces:
        output_dir/
          extensions/
            core.txt
            python.txt, rust.txt, go.txt, cpp.txt
            packs/<pack-name>.txt
          vsix/
            core/README.md
            python/README.md, rust/README.md, go/README.md, cpp/README.md
            packs/<pack-name>/README.md

    All extension IDs are sorted for deterministic output. No .vsix binaries
    are created -- only README.md markers.
    """
    ext_dir = output_dir / "extensions"
    vsix_dir = output_dir / "vsix"

    # Write core extensions (sorted)
    ext_dir.mkdir(parents=True, exist_ok=True)
    (ext_dir / "core.txt").write_text("\n".join(sorted(cfg.core_marketplace)) + "\n")

    # Write language extensions (sorted)
    for lang in _LANGUAGES:
        marketplace = sorted(cfg.language_marketplace.get(lang, []))
        (ext_dir / f"{lang}.txt").write_text("\n".join(marketplace) + "\n")

    # Write pack extension lists (sorted)
    packs_dir = ext_dir / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    for pack_name, pack in cfg.packs.items():
        (packs_dir / f"{pack_name}.txt").write_text("\n".join(sorted(pack.marketplace)) + "\n")

    # Write VSIX README markers (no .vsix files)
    categories = ["core"] + _LANGUAGES
    for cat in categories:
        cat_dir = vsix_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        readme = cat_dir / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {cat} VSIX extensions\n\n"
                f"Place {cat} .vsix files here.\n"
                ".vsix files are not committed to git.\n"
            )

    # Write pack VSIX README markers
    vsix_packs_dir = vsix_dir / "packs"
    for pack_name in cfg.packs:
        pack_dir = vsix_packs_dir / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)
        readme = pack_dir / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {pack_name} VSIX extensions\n\n"
                f"Place {pack_name} .vsix files here.\n"
                ".vsix files are not committed to git.\n"
            )
