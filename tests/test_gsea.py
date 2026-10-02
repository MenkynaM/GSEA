"""Locating GSEA and building its command line."""

from __future__ import annotations

import os

import pytest

from gsea_pipeline.errors import GseaNotFoundError
from gsea_pipeline.gsea import (
    DEFAULT_PARAMETERS,
    GSEA_HOME_ENV,
    GseaInstallation,
    build_command,
    candidate_homes,
    run_gsea,
)


@pytest.fixture
def installation(tmp_path):
    """A directory that looks like a GSEA install for this platform."""
    home = tmp_path / "GSEA_4.2.3"
    home.mkdir()
    (home / GseaInstallation(home).launcher.name).write_text("#!/bin/sh\n")
    return GseaInstallation(home)


def arguments(command):
    """The command's flag/value pairs as a dict."""
    tail = command[command.index("GSEA") + 1 :]
    return dict(zip(tail[::2], tail[1::2]))


def test_launcher_matches_the_platform(installation):
    expected = "gsea-cli.bat" if os.name == "nt" else "gsea-cli.sh"
    assert installation.launcher.name == expected


def test_discover_prefers_an_explicit_home(installation):
    assert GseaInstallation.discover(installation.home) == installation


def test_discover_falls_back_to_the_environment(installation, monkeypatch):
    monkeypatch.setenv(GSEA_HOME_ENV, str(installation.home))
    assert GseaInstallation.discover() == installation


def test_discover_rejects_a_directory_without_a_launcher(tmp_path):
    with pytest.raises(GseaNotFoundError, match="contains no gsea-cli"):
        GseaInstallation.discover(tmp_path)


def test_discover_without_any_installation_explains_what_to_do(monkeypatch):
    monkeypatch.delenv(GSEA_HOME_ENV, raising=False)
    monkeypatch.setattr("gsea_pipeline.gsea.candidate_homes", list)
    with pytest.raises(GseaNotFoundError, match=GSEA_HOME_ENV):
        GseaInstallation.discover()


def test_discover_picks_the_highest_version_and_warns(tmp_path, monkeypatch, caplog):
    """The original stopped and asked at an ``input()`` prompt, during import."""
    homes = []
    for name in ("GSEA_4.2.3", "GSEA_4.10.0"):
        home = tmp_path / name
        home.mkdir()
        (home / GseaInstallation(home).launcher.name).touch()
        homes.append(home)
    monkeypatch.delenv(GSEA_HOME_ENV, raising=False)
    monkeypatch.setattr("gsea_pipeline.gsea.candidate_homes", lambda: sorted(homes))

    with caplog.at_level("WARNING"):
        chosen = GseaInstallation.discover()
    assert chosen.home.name == "GSEA_4.10.0", "4.10 is newer than 4.2.3"
    assert GSEA_HOME_ENV in caplog.text


def test_candidate_homes_does_not_raise_on_this_machine():
    assert isinstance(candidate_homes(), list)


def test_command_starts_with_the_launcher_and_subcommand(installation, tmp_path):
    command = build_command(
        installation,
        res=tmp_path / "x.gct",
        cls="x.cls#P_versus_K",
        gmx=tmp_path / "x.gmt",
        chip=tmp_path / "x.chip",
        out=tmp_path / "out",
    )
    assert command[:2] == [str(installation.launcher), "GSEA"]
    assert arguments(command)["-res"] == str(tmp_path / "x.gct")
    assert arguments(command)["-cls"] == "x.cls#P_versus_K"
    assert arguments(command)["-chip"] == str(tmp_path / "x.chip")


def test_command_includes_the_defaults_and_the_output_directory(installation, tmp_path):
    command = build_command(
        installation,
        res=tmp_path / "x.gct",
        cls="x.cls#P_versus_K",
        gmx=tmp_path / "x.gmt",
        chip=tmp_path / "x.chip",
        out=tmp_path / "out",
    )
    args = arguments(command)
    assert args["-nperm"] == DEFAULT_PARAMETERS["-nperm"]
    assert args["-out"] == str(tmp_path / "out")


def test_parameters_override_the_defaults(installation, tmp_path):
    command = build_command(
        installation,
        res=tmp_path / "x.gct",
        cls="c",
        gmx=tmp_path / "g",
        chip=tmp_path / "c.chip",
        out=tmp_path / "out",
        parameters={"-nperm": "10", "-rpt_label": "sweep"},
    )
    args = arguments(command)
    assert args["-nperm"] == "10"
    assert args["-rpt_label"] == "sweep"


def test_every_value_is_a_separate_argument(installation, tmp_path):
    """``shell=True`` with a list made POSIX run the launcher with no arguments."""
    command = build_command(
        installation,
        res=tmp_path / "x.gct",
        cls="c",
        gmx=tmp_path / "g",
        chip=tmp_path / "c.chip",
        out=tmp_path / "out",
    )
    assert all(isinstance(part, str) for part in command)
    assert len(command) > 2 * len(DEFAULT_PARAMETERS)


def test_run_uses_cwd_rather_than_changing_the_process_directory(installation, tmp_path):
    calls = []
    before = os.getcwd()
    run_gsea(
        installation,
        res=tmp_path / "x.gct",
        cls="c",
        gmx=tmp_path / "g",
        chip=tmp_path / "c.chip",
        out=tmp_path / "out",
        runner=lambda command, **kwargs: calls.append((command, kwargs)),
    )
    assert os.getcwd() == before
    assert calls[0][1]["cwd"] == installation.home
    assert calls[0][1]["check"] is True


def test_run_creates_the_output_directory(installation, tmp_path):
    out = tmp_path / "nested" / "out"
    run_gsea(
        installation,
        res=tmp_path / "x.gct",
        cls="c",
        gmx=tmp_path / "g",
        chip=tmp_path / "c.chip",
        out=out,
        runner=lambda *a, **k: None,
    )
    assert out.is_dir()


def test_dry_run_does_not_execute(installation, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("should not run")

    command = run_gsea(
        installation,
        res=tmp_path / "x.gct",
        cls="c",
        gmx=tmp_path / "g",
        chip=tmp_path / "c.chip",
        out=tmp_path / "out",
        dry_run=True,
        runner=fail,
    )
    assert command[0] == str(installation.launcher) or command[0] == "cmd"
