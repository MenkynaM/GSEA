"""Rendering a matrix into each GSEA input format."""

from __future__ import annotations

import csv

from gsea_pipeline.matrix import matrix_from_rows, read_matrix
from gsea_pipeline.writers import (
    write_delimited,
    write_gct,
    write_staged_csv,
    write_txt,
    write_wide_csv,
)


def test_gct_preamble_counts_features_and_samples(matrix, tmp_path):
    path = write_gct(matrix, tmp_path / "x.gct")
    lines = path.read_text(encoding="utf8").splitlines()
    assert lines[0] == "#1.2"
    assert lines[1] == "2\t3"
    assert lines[2] == "NAME\tDESCRIPTION\tZ1\tZ2\tC1"
    assert lines[3] == "MYH9\tna\t1\t2\t3"
    assert len(lines) == 5


def test_txt_is_the_gct_body_without_the_preamble(matrix, tmp_path):
    gct = write_gct(matrix, tmp_path / "x.gct").read_text(encoding="utf8")
    txt = write_txt(matrix, tmp_path / "x.txt").read_text(encoding="utf8")
    assert gct.split("\n", 2)[2] == txt


def test_staged_csv_round_trips_through_read_matrix(matrix, tmp_path):
    path = write_staged_csv(matrix, tmp_path / "x.csv")
    assert path.read_text(encoding="utf8").splitlines()[0] == "#;Z1;Z2;C1"
    assert read_matrix(path) == matrix


def test_wide_csv_has_an_unnamed_index_column(matrix, tmp_path):
    path = write_wide_csv(matrix, tmp_path / "x.csv")
    rows = list(csv.reader(path.read_text(encoding="utf8").splitlines()))
    assert rows[0] == ["", "Z1", "Z2", "C1"]
    assert rows[1] == ["MYH9", "1", "2", "3"]


def test_delimiters_that_appear_in_the_data_are_quoted(tmp_path):
    """Hand-built strings produced broken CSV here; the csv module escapes it."""
    matrix = matrix_from_rows(["Z1"], [("KRT9, isoform 2", ("0.55",))])
    path = write_wide_csv(matrix, tmp_path / "x.csv")
    assert '"KRT9, isoform 2"' in path.read_text(encoding="utf8")
    assert read_matrix(path, delimiter=",").features[0].name == "KRT9, isoform 2"


def test_writers_create_missing_directories(matrix, tmp_path):
    path = write_gct(matrix, tmp_path / "deep" / "nested" / "x.gct")
    assert path.is_file()


def test_every_line_ends_with_a_newline(matrix, tmp_path):
    """A GCT whose last row has no line terminator trips some readers."""
    for writer, name in (
        (write_gct, "x.gct"),
        (write_txt, "x.txt"),
        (write_staged_csv, "x.csv"),
    ):
        assert writer(matrix, tmp_path / name).read_text(encoding="utf8").endswith("\n")


def test_delimited_writer_honours_its_arguments(matrix, tmp_path):
    path = write_delimited(matrix, tmp_path / "x.tsv", delimiter="\t", index_header="NAME")
    assert path.read_text(encoding="utf8").splitlines()[0] == "NAME\tZ1\tZ2\tC1"
