"""Tests for codervps.render.extensions -- extension list and VSIX rendering."""

from __future__ import annotations

from pathlib import Path

from codervps.config import load_extensions_config
from codervps.render.extensions import _LANGUAGES, render_extensions


# ---- Framework tests (Phase 1) ----


def test_module_exists():
    """Framework: render_extensions and _LANGUAGES are importable."""
    assert callable(render_extensions)
    assert isinstance(_LANGUAGES, list)
    assert (
        "python" in _LANGUAGES
        and "rust" in _LANGUAGES
        and "go" in _LANGUAGES
        and "cpp" in _LANGUAGES
    )


def test_render_extensions_signature():
    """Framework: render_extensions accepts ExtensionsConfig and output_dir."""
    cfg = load_extensions_config(Path("config/extensions.toml"))
    # Smoke call — should not raise
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        render_extensions(cfg, out)


# ---- Detailed tests (Phase 3) ----


def test_render_extensions_creates_core_list(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    core = (tmp_path / "extensions/core.txt").read_text()
    lines = core.strip().splitlines()
    assert lines[0] == "EditorConfig.EditorConfig"
    assert "redhat.vscode-yaml" in lines


def test_render_extensions_creates_language_lists(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    assert (tmp_path / "extensions/core.txt").read_text().splitlines()[
        0
    ] == "EditorConfig.EditorConfig"
    assert "ms-python.python" in (tmp_path / "extensions/python.txt").read_text()
    assert "rust-lang.rust-analyzer" in (tmp_path / "extensions/rust.txt").read_text()
    assert "golang.Go" in (tmp_path / "extensions/go.txt").read_text()
    assert "llvm-vs-code-extensions.vscode-clangd" in (tmp_path / "extensions/cpp.txt").read_text()


def test_render_extensions_creates_pack_lists(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    # LeetCode pack should have its extension list
    leetcode = (tmp_path / "extensions/packs/leetcode.txt").read_text()
    assert "leetcode.vscode-leetcode" in leetcode


def test_render_extensions_creates_vsix_readme_markers(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    assert (tmp_path / "vsix/core/README.md").exists()
    assert (tmp_path / "vsix/python/README.md").exists()
    assert (tmp_path / "vsix/rust/README.md").exists()
    assert (tmp_path / "vsix/go/README.md").exists()
    assert (tmp_path / "vsix/cpp/README.md").exists()
    assert (tmp_path / "vsix/packs/leetcode/README.md").exists()


def test_vsix_readme_says_no_commit(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    readme = (tmp_path / "vsix/core/README.md").read_text()
    assert ".vsix files are not committed" in readme


def test_vsix_readme_uses_fstrings_not_literal_name(tmp_path):
    """Regression test for R2 bug where {name} appeared literally in README."""
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    readme = (tmp_path / "vsix/core/README.md").read_text()
    assert "{name}" not in readme
    # Also check pack README
    pack_readme = (tmp_path / "vsix/packs/leetcode/README.md").read_text()
    assert "{name}" not in pack_readme
    assert "leetcode" in pack_readme.lower()


def test_no_vsix_binaries_created(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    vsix_files = list(tmp_path.rglob("*.vsix"))
    assert len(vsix_files) == 0


def test_extension_lists_are_sorted(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    for txt_file in (tmp_path / "extensions").rglob("*.txt"):
        lines = txt_file.read_text().strip().splitlines()
        if len(lines) > 1:
            assert lines == sorted(lines), f"{txt_file.name} should be sorted"


def test_extension_lists_end_with_newline(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    for txt_file in (tmp_path / "extensions").rglob("*.txt"):
        text = txt_file.read_text()
        assert text.endswith("\n"), f"{txt_file.name} should end with newline"
        # Empty extension lists still produce a trailing newline
        assert len(text) > 0


def test_all_four_languages_have_txt_files(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    for lang in _LANGUAGES:
        assert (tmp_path / f"extensions/{lang}.txt").exists(), f"Missing {lang}.txt"


def test_all_four_languages_have_vsix_readme(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    for lang in _LANGUAGES:
        assert (tmp_path / f"vsix/{lang}/README.md").exists(), f"Missing vsix/{lang}/README.md"


def test_empty_language_has_empty_txt_file(tmp_path):
    """Language with no marketplace entries produces file with just newline."""
    from codervps.models import ExtensionsConfig

    cfg = ExtensionsConfig(core_marketplace=[], language_marketplace={"python": []}, packs={})
    render_extensions(cfg, tmp_path)
    txt = (tmp_path / "extensions/python.txt").read_text()
    assert txt == "\n"


def test_idempotent_rendering(tmp_path):
    cfg = load_extensions_config(Path("config/extensions.toml"))
    render_extensions(cfg, tmp_path)
    first_files = {}
    for p in sorted(tmp_path.rglob("*")):
        if p.is_file():
            first_files[str(p.relative_to(tmp_path))] = p.read_bytes()

    # Render again
    render_extensions(cfg, tmp_path)
    for p in sorted(tmp_path.rglob("*")):
        if p.is_file():
            key = str(p.relative_to(tmp_path))
            assert p.read_bytes() == first_files[key], f"Non-deterministic: {key}"
