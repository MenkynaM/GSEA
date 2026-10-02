"""Reading GSEA's HTML output, including the two bugs the old scraper had."""

from __future__ import annotations

import csv

import pytest

from gsea_pipeline.errors import ReportParsingError
from gsea_pipeline.reports import (
    export_gene_set_tables,
    find_reports,
    gene_set_names,
    gene_set_table,
    summarise_index,
)

from .sample_data import GENE_SET_HTML, GSEA_INDEX_HTML, GSEA_REPORT_HTML


@pytest.fixture
def report_dir(tmp_path):
    """A directory shaped like one GSEA report."""
    directory = tmp_path / "my_analysis.Gsea.1655363774792"
    directory.mkdir()
    (directory / "index.html").write_text(GSEA_INDEX_HTML, encoding="utf8")
    (directory / "gsea_report_for_P_1.html").write_text(GSEA_REPORT_HTML, encoding="utf8")
    for name in ("HALLMARK_COAGULATION", "HALLMARK_HYPOXIA"):
        (directory / f"{name}.html").write_text(GENE_SET_HTML, encoding="utf8")
    return directory


def test_summary_reports_both_phenotypes(report_dir):
    summary = summarise_index(report_dir / "index.html")
    assert [p.phenotype for p in summary.phenotypes] == ["P", "K"]
    first, second = summary.phenotypes
    assert (first.upregulated, first.gene_sets) == (4, 19)
    assert (second.upregulated, second.gene_sets) == (15, 19)


def test_score_counts_gene_sets_below_the_fdr_threshold(report_dir):
    """The old ``scrape_for_score`` read the first <li> -- the upregulated count --
    and sliced it at fixed offsets, which raised ValueError on real reports."""
    assert summarise_index(report_dir / "index.html").score == 2


def test_both_phrasings_of_the_fdr_line_are_recognised(report_dir):
    """GSEA writes "are significant at" for one phenotype and
    "are significantly enriched at" for the other."""
    summary = summarise_index(report_dir / "index.html")
    assert [p.fdr_below_25 for p in summary.phenotypes] == [0, 2]


def test_nominal_p_value_counts_are_read(report_dir):
    summary = summarise_index(report_dir / "index.html")
    assert [p.nominal_p_below_1 for p in summary.phenotypes] == [0, 1]
    assert [p.nominal_p_below_5 for p in summary.phenotypes] == [1, 2]


def test_summary_of_a_page_without_phenotypes_is_an_error(tmp_path):
    path = tmp_path / "index.html"
    path.write_text("<html><body><ul><li>nothing useful</ul></body></html>", encoding="utf8")
    with pytest.raises(ReportParsingError):
        summarise_index(path)


def test_find_reports_locates_each_directory(report_dir):
    assert find_reports(report_dir.parent) == [report_dir]


def test_gene_set_names_come_from_the_phenotype_report(report_dir):
    assert gene_set_names(report_dir) == ["HALLMARK_COAGULATION", "HALLMARK_HYPOXIA"]


def test_gene_set_table_reads_the_enrichment_rows(report_dir):
    table = gene_set_table(report_dir / "HALLMARK_COAGULATION.html")
    assert table.header == ("SYMBOL", "TITLE", "CORE ENRICHMENT")
    assert table.rows[0][0] == "HRG"


def test_export_keeps_the_whole_gene_set_name(report_dir):
    """``scrape_file`` wrote ``f'{file}'[:-4] + '.csv'``, so the committed output
    holds HALLMARK_COAGULA.csv -- four characters cut off the gene set name."""
    written = export_gene_set_tables(report_dir)
    assert sorted(p.name for p in written) == [
        "HALLMARK_COAGULATION.csv",
        "HALLMARK_HYPOXIA.csv",
    ]


def test_exported_csv_holds_the_table(report_dir):
    written = export_gene_set_tables(report_dir)
    rows = list(csv.reader(written[0].read_text(encoding="utf8").splitlines()))
    assert rows[0] == ["SYMBOL", "TITLE", "CORE ENRICHMENT"]
    assert rows[1] == ["HRG", "histidine rich glycoprotein", "Yes"]


def test_quoted_descriptions_survive_the_round_trip(report_dir):
    """Ensembl wraps descriptions containing commas in double quotes, and GSEA
    passes them through.  ``scrape_file`` deleted every such quote from the data;
    escaping them instead means csv.reader hands back the original text."""
    written = export_gene_set_tables(report_dir)
    rows = list(csv.reader(written[0].read_text(encoding="utf8").splitlines()))
    assert rows[2][1] == '"apolipoprotein A1, variant"'


def test_export_destination_can_be_chosen(report_dir, tmp_path):
    written = export_gene_set_tables(report_dir, tmp_path / "elsewhere")
    assert all(p.parent == tmp_path / "elsewhere" for p in written)


def test_a_gene_set_page_without_a_table_is_skipped(report_dir, caplog):
    (report_dir / "HALLMARK_HYPOXIA.html").write_text("<html></html>", encoding="utf8")
    written = export_gene_set_tables(report_dir)
    assert [p.stem for p in written] == ["HALLMARK_COAGULATION"]
    assert "HALLMARK_HYPOXIA.html" in caplog.text
