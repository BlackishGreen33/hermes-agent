"""Discovered locations distinguish per-profile copies without importing plugins (#141469)."""

import argparse
import importlib.metadata
import json
from pathlib import Path

import pytest
from rich.console import Console

from hermes_cli import plugins_cmd
from hermes_cli.subcommands.plugins import build_plugins_parser
from hermes_constants import reset_hermes_home_override, set_hermes_home_override


def _run(*argv):
    parser = argparse.ArgumentParser()
    build_plugins_parser(parser.add_subparsers(), cmd_plugins=plugins_cmd.plugins_command)
    args = parser.parse_args(["plugins", *argv])
    plugins_cmd.plugins_command(args)


@pytest.fixture
def offline_discovery(monkeypatch, tmp_path):
    monkeypatch.setattr("hermes_cli.plugins.get_bundled_plugins_dir", lambda: tmp_path / "bundled")
    monkeypatch.setattr(importlib.metadata, "entry_points", list)
    monkeypatch.setattr("hermes_cli.plugins_cmd_catalog.resolved_removed_entries", list)
    monkeypatch.setattr(plugins_cmd, "_console", lambda: Console(width=400, color_system=None))


@pytest.mark.parametrize("output", ["json", "paths", "plain-paths", "show", "default", "plain"])
def test_profile_copies_report_the_discovered_location(output, offline_discovery, tmp_path, capsys):
    locations = []
    for profile in ("first", "second"):
        home = tmp_path / "profiles" / profile
        plugin = home / "plugins" / "profile[copy]"
        plugin.mkdir(parents=True)
        (plugin / "plugin.yaml").write_text(
            "name: profile-copy\nversion: '1.0.0'\ndescription: Profile copy\n", encoding="utf-8"
        )
        (plugin / "__init__.py").write_text(
            "from pathlib import Path\nPath(__file__).with_name('imported').touch()\n"
            "raise AssertionError('listing imported the plugin')\n", encoding="utf-8"
        )
        (home / "config.yaml").write_text("plugins:\n  enabled: [profile-copy]\n", encoding="utf-8")
        token = set_hermes_home_override(home)
        try:
            argv = {
                "json": ("list", "--json"),
                "paths": ("list", "--paths"),
                "plain-paths": ("list", "--plain", "--paths"),
                "show": ("show", "profile-copy"),
                "default": ("list",),
                "plain": ("list", "--plain"),
            }[output]
            _run(*argv)
            text = capsys.readouterr().out
            if output == "json":
                assert json.loads(text) == [{
                    "name": "profile-copy", "status": "enabled", "version": "1.0.0",
                    "description": "Profile copy", "source": "user", "removed": None,
                    "location": str(plugin),
                }]
            elif output in {"default", "plain"}:
                assert "Discovered location" not in text
                assert str(plugin) not in text
                if output == "plain":
                    assert text == f"{'enabled':12} {'user':8} {'1.0.0':8} profile-copy\n"
            else:
                assert str(plugin) in text
                if output in {"paths", "show"}:
                    assert "Discovered location" in text
            assert not (plugin / "imported").exists()
            locations.append(str(plugin))
        finally:
            reset_hermes_home_override(token)
    assert locations[0] != locations[1]


@pytest.mark.parametrize("source,location", [("entrypoint", "not_imported.plugin:register"), ("user", None)])
def test_entrypoint_and_unknown_locations_stay_metadata(source, location, offline_discovery, monkeypatch, capsys):
    monkeypatch.setattr(plugins_cmd, "_discover_all_plugins", lambda: [
        ("example", "1.0.0", "", source, location, "example")
    ])
    _run("list", "--json")
    assert json.loads(capsys.readouterr().out)[0]["location"] == location
    _run("list", "--plain", "--paths")
    assert capsys.readouterr().out.rstrip().endswith(f"example {location or 'unknown'}")
    _run("show", "example")
    text = capsys.readouterr().out
    assert f"Discovered location: {location or 'unknown'}" in text
    assert "Runs in:" not in text


@pytest.mark.platforms("posix")
def test_directory_locations_are_absolute_without_resolving_symlinks(offline_discovery, tmp_path, monkeypatch, capsys):
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "linked").symlink_to(target, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(plugins_cmd, "_discover_all_plugins", lambda: [
        ("linked", "1.0.0", "", "user", Path("linked"), "linked")
    ])
    _run("list", "--json")
    assert json.loads(capsys.readouterr().out)[0]["location"] == str(tmp_path / "linked")
