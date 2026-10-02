"""The command line interface, which replaces five ``__main__`` blocks."""

from __future__ import annotations

import logging

import pytest

from gsea_pipeline.cli import main
from gsea_pipeline.gsea import GSEA_HOME_ENV, GseaInstallation

from .conftest import FakeResponse, FakeSession
from .sample_data import (
    CHIP_INDEX_HTML,
    GENE_SET_HTML,
    GSEA_INDEX_HTML,
    GSEA_REPORT_HTML,
)

HEADER = ["", "", "", "", "name", "", "", "", "", "count"]


def run(argv, data_dir):
    return main(["--data-dir", str(data_dir), *argv])


def test_help_is_available(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "prepare" in capsys.readouterr().out


def test_no_command_is_an_error():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0


def test_prepare_writes_the_inputs_and_reports_them(proline_file, layout, capsys):
    assert run(["prepare"], layout.root) == 0
    out = capsys.readouterr().out
    assert "3 features, 3 samples, phenotypes Z/C" in out
    assert (layout.gct / "sample.gct").is_file()
    assert (layout.phenotypes / "sample.cls").is_file()


def test_prepare_accepts_explicit_sources(proline_file, layout, tmp_path):
    assert run(["prepare", str(proline_file)], tmp_path / "elsewhere") == 0
    assert (tmp_path / "elsewhere" / "gct" / "sample.gct").is_file()


def test_prepare_formats_are_selectable(proline_file, layout):
    assert run(["prepare", "--format", "wide"], layout.root) == 0
    assert (layout.wide / "sample.csv").is_file()
    assert not layout.gct.exists()


def test_prepare_with_nothing_to_do_exits_nonzero(layout):
    assert run(["prepare"], layout.root) == 1


def test_prepare_reports_a_malformed_table_without_a_traceback(layout, capsys):
    layout.raw.mkdir(parents=True)
    (layout.raw / "bad.csv").write_text("#;a;b\nX;1\n", encoding="utf8")
    assert run(["prepare"], layout.root) == 1
    assert "expected 2 values" in capsys.readouterr().err


def test_run_without_gsea_exits_nonzero(layout, monkeypatch, capsys):
    monkeypatch.delenv(GSEA_HOME_ENV, raising=False)
    monkeypatch.setattr("gsea_pipeline.gsea.candidate_homes", list)
    status = run(
        ["run", "--res", "a.gct", "--cls", "a.cls", "--gmx", "a.gmt", "--chip", "a.chip"],
        layout.root,
    )
    assert status == 1
    assert "no GSEA installation" in capsys.readouterr().err


def test_dry_run_prints_the_command_for_each_comparison(layout, tmp_path, capsys, monkeypatch):
    home = tmp_path / "GSEA_4.2.3"
    home.mkdir()
    (home / GseaInstallation(home).launcher.name).touch()
    monkeypatch.setenv(GSEA_HOME_ENV, str(home))

    cls = tmp_path / "a.cls"
    cls.write_text("3 2 1\n# P K\nP P K\n", encoding="utf8")

    status = run(
        [
            "run",
            "--res", "a.gct",
            "--cls", str(cls),
            "--gmx", "a.gmt",
            "--chip", "a.chip",
            "--set", "nperm=10",
            "--dry-run",
        ],
        layout.root,
    )
    assert status == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2, "one command per ordered phenotype pair"
    assert "#P_versus_K" in lines[0]
    assert "#K_versus_P" in lines[1]
    assert "-nperm 10" in lines[0]


def test_a_malformed_parameter_override_is_reported(layout, tmp_path, monkeypatch, capsys):
    home = tmp_path / "GSEA_4.2.3"
    home.mkdir()
    (home / GseaInstallation(home).launcher.name).touch()
    monkeypatch.setenv(GSEA_HOME_ENV, str(home))
    cls = tmp_path / "a.cls"
    cls.write_text("2 2 1\n# P K\nP K\n", encoding="utf8")

    status = run(
        [
            "run", "--res", "a.gct", "--cls", str(cls),
            "--gmx", "a.gmt", "--chip", "a.chip",
            "--set", "nperm", "--dry-run",
        ],
        layout.root,
    )
    assert status == 1
    assert "FLAG=VALUE" in capsys.readouterr().err


def test_chips_lists_the_available_annotations(layout, monkeypatch, capsys):
    monkeypatch.setattr(
        "gsea_pipeline.cli.list_chip_files", lambda **kwargs: ["Human_A.chip", "Human_B.chip"]
    )
    assert run(["chips"], layout.root) == 0
    assert capsys.readouterr().out.splitlines() == ["Human_A.chip", "Human_B.chip"]


def test_chips_download_fills_the_chips_directory(layout, monkeypatch, capsys):
    session = FakeSession(
        [FakeResponse(text=CHIP_INDEX_HTML), FakeResponse(content_chunks=(b"x",)), FakeResponse(content_chunks=(b"y",))]
    )
    monkeypatch.setattr(
        "gsea_pipeline.cli.list_chip_files", lambda **kwargs: ["Human_A.chip"]
    )
    monkeypatch.setattr(
        "gsea_pipeline.cli.download_chip_files",
        lambda names, dest, **kwargs: [dest / n for n in names],
    )
    assert run(["chips", "--download"], layout.root) == 0
    assert "1 annotation files" in capsys.readouterr().out
    assert session.requests == []


def test_chips_with_no_match_exits_nonzero(layout, monkeypatch):
    monkeypatch.setattr("gsea_pipeline.cli.list_chip_files", lambda **kwargs: [])
    assert run(["chips"], layout.root) == 1


@pytest.fixture
def report_tree(layout):
    directory = layout.gsea_output / "my_analysis.Gsea.1"
    directory.mkdir(parents=True)
    (directory / "index.html").write_text(GSEA_INDEX_HTML, encoding="utf8")
    (directory / "gsea_report_for_P_1.html").write_text(GSEA_REPORT_HTML, encoding="utf8")
    for name in ("HALLMARK_COAGULATION", "HALLMARK_HYPOXIA"):
        (directory / f"{name}.html").write_text(GENE_SET_HTML, encoding="utf8")
    return directory


def test_report_summarises_every_run(report_tree, layout, capsys):
    assert run(["report"], layout.root) == 0
    out = capsys.readouterr().out
    assert "2 gene sets at FDR < 25%" in out
    assert "P: 4/19 upregulated" in out
    assert "K: 15/19 upregulated" in out


def test_report_export_writes_the_gene_set_tables(report_tree, layout, capsys):
    assert run(["report", "--export"], layout.root) == 0
    assert "exported 2 gene set tables" in capsys.readouterr().out
    assert (report_tree / "converted" / "HALLMARK_COAGULATION.csv").is_file()


def test_report_without_any_run_exits_nonzero(layout):
    assert run(["report"], layout.root) == 1


def test_tally_writes_its_report(layout, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "gsea_pipeline.proteins.read_spreadsheet_rows",
        lambda path: iter([HEADER, [*[""] * 4, "VIM", *[""] * 4, 7]]),
    )
    target = tmp_path / "results.txt"
    assert run(["tally", "book.xlsx", "-o", str(target)], layout.root) == 0
    assert "VIM\t7\t1" in target.read_text(encoding="utf8")
    assert "1 proteins written" in capsys.readouterr().out


def test_tally_prints_to_stdout_without_an_output_path(layout, monkeypatch, capsys):
    monkeypatch.setattr(
        "gsea_pipeline.proteins.read_spreadsheet_rows",
        lambda path: iter([HEADER, [*[""] * 4, "VIM", *[""] * 4, 7]]),
    )
    assert run(["tally", "book.xlsx"], layout.root) == 0
    assert "VIM" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("flag", "level"), [("-q", logging.WARNING), ("-v", logging.DEBUG)]
)
def test_verbosity_flags_set_the_log_level(proline_file, layout, flag, level):
    run([flag, "prepare"], layout.root)
    assert logging.getLogger("gsea_pipeline").level == level
