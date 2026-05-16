"""Tests for codervps.cli -- CLI command dispatch and argument parsing.

All CLI commands are now wired to real functions. Tests verify real behavior,
not stubs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codervps.cli import COMMANDS, build_parser, main


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---- Version ----


def test_main_version(capsys):
    rc = main(["--version"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "codervps 0.1.0"


def test_main_no_args_prints_help(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "codervps" in out


# ---- Unknown command ----


def test_main_unknown_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent"])
    assert exc_info.value.code != 0
    _ = capsys.readouterr()


# ---- COMMANDS dict ----


def test_commands_dict_has_four_entries():
    assert set(COMMANDS.keys()) == {
        "validate",
        "refresh-catalog",
        "render-generated",
        "build-matrix",
    }


def test_commands_are_callable():
    for name, handler in COMMANDS.items():
        assert callable(handler), f"{name} handler is not callable"


# ---- Validate command (real) ----


def test_validate_returns_zero(monkeypatch, tmp_path, capsys):
    """Real validate checks config files exist and are loadable."""
    # We need config files to exist for validate to pass
    monkeypatch.chdir(REPO_ROOT)
    rc = main(["validate"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert "OK" in out


# ---- Refresh-catalog command (real) ----


def test_refresh_catalog_writes_file(monkeypatch, tmp_path, capsys):
    """Real refresh-catalog writes catalog JSON."""
    monkeypatch.chdir(REPO_ROOT)
    out_path = tmp_path / "catalog.json"
    rc = main(["refresh-catalog", "--output", str(out_path), "--fixture-dir", "tests/fixtures"])
    capsys.readouterr()
    assert rc == 0
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["schema_version"] == 1
    assert "node" in data


def test_refresh_catalog_custom_output(tmp_path, monkeypatch, capsys):
    out_path = tmp_path / "custom" / "catalog.json"
    monkeypatch.chdir(REPO_ROOT)
    rc = main(["refresh-catalog", "--output", str(out_path), "--fixture-dir", "tests/fixtures"])
    assert rc == 0
    assert out_path.exists()


def test_refresh_catalog_discovery_error_exits_without_traceback(tmp_path, monkeypatch, capsys):
    from codervps.discovery import DiscoveryError

    def fail_refresh(*_args, **_kwargs):
        raise DiscoveryError("upstream timed out")

    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setattr("codervps.catalog.refresh_catalog", fail_refresh)
    with pytest.raises(SystemExit) as exc_info:
        main(["refresh-catalog", "--output", str(tmp_path / "catalog.json")])
    err = capsys.readouterr().err
    assert exc_info.value.code == 1
    assert "catalog refresh failed: upstream timed out" in err
    assert "Traceback" not in err


# ---- Render-generated command (pastured) ----


def test_render_generated_with_catalog(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO_ROOT)
    # Create a minimal catalog file
    catalog = tmp_path / "cat.json"
    catalog.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "base": {"tag": "ubuntu-noble-20260511"},
                "node": {"majors": {"24": {"version": "24.11.1"}}},
                "plugins": {"python": {}, "rust": {}, "go": {}, "cpp": {}},
                "tools": {},
            }
        )
    )
    out_dir = tmp_path / "gen"
    rc = main(["render-generated", "--catalog", str(catalog), "--output", str(out_dir)])
    assert rc == 0
    # Should have created generated tree
    assert (out_dir / "generated/catalog/toolchains.json").exists()
    assert (out_dir / "generated/manifest.json").exists()


def test_render_generated_missing_catalog_exits_nonzero(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["render-generated", "--catalog", str(tmp_path / "nonexistent.json")])
    assert exc_info.value.code == 1


def test_render_generated_with_write_images_json(tmp_path, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    catalog = tmp_path / "cat.json"
    images = tmp_path / "imgs.json"
    catalog.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plugins": {},
                "node": {"majors": {}},
            }
        )
    )
    images.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "images": [{"node_major": 24, "image": "ghcr.io/test:img"}],
            }
        )
    )
    out_dir = tmp_path / "gen"
    rc = main(
        [
            "render-generated",
            "--catalog",
            str(catalog),
            "--output",
            str(out_dir),
            "--images",
            str(images),
            "--write-images-json",
        ]
    )
    assert rc == 0
    assert (out_dir / "generated/catalog/images.json").exists()


def test_render_generated_unrecognized_flag_exits():
    with pytest.raises(SystemExit) as exc_info:
        main(["render-generated", "--nonexistent", "foo"])
    assert exc_info.value.code != 0


# ---- Build-matrix command (pastured) ----


def test_build_matrix_json_default(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    catalog = tmp_path / "cat.json"
    catalog.write_text(
        json.dumps(
            {
                "base": {"tag": "ubuntu-noble-20260511"},
                "node": {"majors": {"24": {"version": "24.11.1"}}},
            }
        )
    )
    rc = main(["build-matrix", "--catalog", str(catalog)])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    parsed = json.loads(out)
    assert isinstance(parsed, list)
    assert parsed[0]["node_major"] == 24


def test_build_matrix_github_output(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    catalog = tmp_path / "cat.json"
    catalog.write_text(
        json.dumps(
            {
                "base": {"tag": "ubuntu-noble-20260511"},
                "node": {"majors": {"24": {"version": "24.11.1"}}},
            }
        )
    )
    rc = main(["build-matrix", "--catalog", str(catalog), "--format", "github-output"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out.startswith("matrix=")
    json_str = out.removeprefix("matrix=")
    parsed = json.loads(json_str)
    assert isinstance(parsed, list)


def test_build_matrix_missing_catalog_exits_nonzero(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["build-matrix", "--catalog", str(tmp_path / "nonexistent.json")])
    assert exc_info.value.code == 1


# ---- Argument parser isolation ----


def test_build_parser_returns_argparse():
    p = build_parser()
    assert p.prog == "codervps"
    assert p.formatter_class.__name__ == "RawDescriptionHelpFormatter"


def test_parser_subcommands_registered():
    p = build_parser()
    subs = [a for a in p._actions if a.dest == "command"]
    assert len(subs) == 1
    assert set(subs[0].choices.keys()) == set(COMMANDS.keys())


def test_parser_help_contains_commands():
    p = build_parser()
    help_text = p.format_help()
    assert "validate" in help_text
    assert "refresh-catalog" in help_text
    assert "render-generated" in help_text
    assert "build-matrix" in help_text


# ---- All flags registered ----


def test_refresh_catalog_has_fixture_dir_flag():
    p = build_parser()
    args = p.parse_args(["refresh-catalog", "--fixture-dir", "foo/"])
    assert args.fixture_dir == "foo/"


def test_render_generated_has_images_flag():
    p = build_parser()
    args = p.parse_args(["render-generated", "--catalog", "c.json", "--images", "i.json"])
    assert args.images == "i.json"


def test_render_generated_has_write_images_json_flag():
    p = build_parser()
    args = p.parse_args(["render-generated", "--catalog", "c.json", "--write-images-json"])
    assert args.write_images_json is True


# ---- Exit code on errors ----


def test_refresh_catalog_bad_config_exits_nonzero(tmp_path, monkeypatch):
    """If config is missing, refresh-catalog should exit non-zero."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        main(["refresh-catalog", "--output", str(tmp_path / "out.json")])
    assert exc_info.value.code == 1
