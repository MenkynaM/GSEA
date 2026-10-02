"""Reading tables, and the structural checks the old string splitting skipped."""

from __future__ import annotations

import pytest

from gsea_pipeline.errors import MalformedTableError
from gsea_pipeline.matrix import detect_delimiter, matrix_from_rows, read_matrix

from .sample_data import PROLINE_CSV, STAGED_CSV


def write(tmp_path, text, name="table.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf8")
    return path


def test_reads_comma_separated_table(tmp_path):
    matrix = read_matrix(write(tmp_path, PROLINE_CSV))
    assert matrix.samples == (
        "norm(Weighted SC Z1)",
        "norm(Weighted SC Z2)",
        "norm(Weighted SC C1)",
    )
    assert matrix.n_features == 3
    assert matrix.features[0].name == "MYH9_HUMAN"
    assert matrix.features[0].values == ("87.5", "79.9", "145.2")


def test_reads_semicolon_separated_table(tmp_path):
    matrix = read_matrix(write(tmp_path, STAGED_CSV))
    assert matrix.samples == ("Z1", "Z2", "C1")
    assert matrix.n_features == 2


def test_header_whitespace_is_stripped(tmp_path):
    matrix = read_matrix(write(tmp_path, "#; P5; P10\nALB;281;51\n"))
    assert matrix.samples == ("P5", "P10")


def test_quoted_commas_do_not_split_cells(tmp_path):
    """Proline descriptions contain commas; naive ``split(',')`` broke on them."""
    text = 'Protein Set,Z1\n"KRT9, isoform 2",0.55\n'
    matrix = read_matrix(write(tmp_path, text), delimiter=",")
    assert matrix.features[0].name == "KRT9, isoform 2"
    assert matrix.features[0].values == ("0.55",)


def test_blank_lines_are_skipped(tmp_path):
    matrix = read_matrix(write(tmp_path, "#;Z1\nA;1\n\nB;2\n\n"))
    assert [f.name for f in matrix.features] == ["A", "B"]


def test_ragged_row_is_rejected_with_its_line_number(tmp_path):
    path = write(tmp_path, "#;Z1;Z2\nA;1;2\nB;3\n")
    with pytest.raises(MalformedTableError) as excinfo:
        read_matrix(path)
    assert ":3:" in str(excinfo.value)


def test_empty_file_is_rejected(tmp_path):
    with pytest.raises(MalformedTableError):
        read_matrix(write(tmp_path, ""))


def test_table_without_sample_columns_is_rejected(tmp_path):
    with pytest.raises(MalformedTableError):
        read_matrix(write(tmp_path, "only-one-column\nA\n"), delimiter=";")


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("#;a;b;c", ";"),
        ("Protein Set,a,b,c", ","),
        ("NAME\ta\tb", "\t"),
        # Nothing to go on: the staged format's delimiter is the default.
        ("single", ";"),
    ],
)
def test_detect_delimiter(header, expected):
    assert detect_delimiter(header) == expected


def test_transforms_return_new_matrices(matrix):
    renamed = matrix.rename_samples(str.lower)
    assert renamed.samples == ("z1", "z2", "c1")
    assert matrix.samples == ("Z1", "Z2", "C1"), "the original must be untouched"


def test_map_features_drops_unmapped(matrix):
    mapped = matrix.map_features({"MYH9": "4627"})
    assert [f.name for f in mapped.features] == ["4627"]
    assert mapped.features[0].values == ("1", "2", "3")


def test_drop_empty_features():
    matrix = matrix_from_rows(["Z1"], [("A", ("1",)), ("  ", ("2",))])
    assert matrix.drop_empty_features().n_features == 1
