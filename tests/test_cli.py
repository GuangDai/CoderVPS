"""Tests for codervps.cli -- CLI skeleton, command dispatch, and argument parsing."""

from __future__ import annotations

import pytest

from codervps.cli import COMMANDS, build_parser, main


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
    # RawDescriptionHelpFormatter preserves line breaks
    assert "codervps" in out


# ---- Unknown command ----


def test_main_unknown_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent"])
    assert exc_info.value.code != 0
    # argparser error goes to stderr for unknown subparser
    _ = capsys.readouterr()


# ---- COMMANDS dict has exactly 4 entries ----


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


# ---- Validate command ----


def test_validate_returns_zero(capsys):
    rc = main(["validate"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert "not implemented" in out


# ---- Refresh-catalog command stub ----


def test_refresh_catalog_default_output(tmp_path, monkeypatch, capsys):
    # Use a temp directory as cwd so build/ is created there
    monkeypatch.chdir(tmp_path)
    rc = main(["refresh-catalog"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert "not implemented" in out
    assert (tmp_path / "build").is_dir()


def test_refresh_catalog_custom_output(tmp_path, capsys):
    out_path = tmp_path / "custom" / "catalog.json"
    rc = main(["refresh-catalog", "--output", str(out_path)])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert "not implemented" in out
    assert out_path.parent.is_dir()


# ---- Render-generated command stub ----


def test_render_generated_missing_catalog_exits_nonzero(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["render-generated", "--catalog", str(tmp_path / "nonexistent.json")])
    assert exc_info.value.code == 1


def test_render_generated_with_catalog(tmp_path, capsys):
    # Create a minimal catalog file
    catalog = tmp_path / "cat.json"
    catalog.write_text("{}")
    out_dir = tmp_path / "gen"
    rc = main(["render-generated", "--catalog", str(catalog), "--output", str(out_dir)])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert "not implemented" in out
    assert out_dir.is_dir()


# ---- Build-matrix command stub ----


def test_build_matrix_json_default(tmp_path, capsys):
    catalog = tmp_path / "cat.json"
    catalog.write_text("{}")
    rc = main(["build-matrix", "--catalog", str(catalog)])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "[]"


def test_build_matrix_github_output(tmp_path, capsys):
    catalog = tmp_path / "cat.json"
    catalog.write_text("{}")
    rc = main(["build-matrix", "--catalog", str(catalog), "--format", "github-output"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == "matrix=[]"


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
    # subparsers action is in _actions
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


# ---- Exit code on errors ----


def test_main_validate_error_path():
    # nonexistent subcommand covered by test_main_unknown_command_exits_nonzero
    pass
