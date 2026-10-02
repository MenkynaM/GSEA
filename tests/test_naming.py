"""Name normalisation, including the cases the old fixed-width slices broke on."""

from __future__ import annotations

import pytest

from gsea_pipeline.naming import (
    sample_group,
    sample_name,
    split_sample_code,
    strip_kegg_organism,
    strip_organism_suffix,
)


@pytest.mark.parametrize(
    ("column", "expected"),
    [
        ("norm(Weighted SC Z1)", "Z1"),
        ("norm(Weighted SC C12)", "C12"),
        (" P5 ", "P5"),
        ("abundance(sample A3)", "A3"),
        # Already normalised headers survive a second pass.
        ("Z1", "Z1"),
        # No trailing parenthesis: fall back to the last whitespace token.
        ("Weighted SC Z1", "Z1"),
    ],
)
def test_sample_name(column, expected):
    assert sample_name(column) == expected


def test_sample_name_of_header_without_parentheses_keeps_full_token():
    """The old ``split(' ')[-1][:-1]`` dropped a character from such headers."""
    assert sample_name("Z1") == "Z1"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("MYH9_HUMAN", "MYH9"),
        ("ALBU_HUMAN", "ALBU"),
        ("P12345_MOUSE", "P12345"),
        # No organism suffix: left alone, where ``name[:-6]`` would have cut into it.
        ("MYH9", "MYH9"),
        ("TF", "TF"),
        ("4627", "4627"),
        ("HLA_A", "HLA_A"),
    ],
)
def test_strip_organism_suffix(name, expected):
    assert strip_organism_suffix(name) == expected


@pytest.mark.parametrize(
    ("kegg_id", "expected"),
    [("hsa:4627", "4627"), ("mmu:17886", "17886"), ("4627", "4627")],
)
def test_strip_kegg_organism(kegg_id, expected):
    """``kegg_id[4:]`` only worked for three-letter organism codes."""
    assert strip_kegg_organism(kegg_id) == expected


@pytest.mark.parametrize(
    ("sample", "expected"),
    [
        ("Z12", ("Z", "12")),
        (" P5 ", ("P", "5")),
        ("C10", ("C", "10")),
        ("control", ("control", "")),
        ("", ("", "")),
    ],
)
def test_split_sample_code(sample, expected):
    assert split_sample_code(sample) == expected


def test_split_sample_code_ignores_leading_whitespace():
    """The original indexed the unstripped string, so ``" P5"`` split as ``("", " P5")``."""
    assert split_sample_code(" P5") == ("P", "5")
    assert sample_group(" P5") == "P"
