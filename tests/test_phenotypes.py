"""Phenotype grouping and ``.cls`` files."""

from __future__ import annotations

import pytest

from gsea_pipeline.errors import MalformedTableError
from gsea_pipeline.phenotypes import Phenotypes, read_cls
from gsea_pipeline.writers import write_cls


def test_classes_keep_first_seen_order():
    """GSEA names its phenotypes by this order, so it must not be sorted."""
    assert Phenotypes.from_samples(["P5", "K1", "P2", "K3"]).classes == ("P", "K")
    assert Phenotypes.from_samples(["K1", "P5"]).classes == ("K", "P")


def test_from_samples_handles_padded_names():
    phenotypes = Phenotypes.from_samples([" P5", "P10 ", " K9 "])
    assert phenotypes.labels == ("P", "P", "K")


def test_render_matches_the_cls_format():
    rendered = Phenotypes.from_samples(["P1", "P2", "K1"]).render()
    assert rendered == "3 2 1\n# P K\nP P K\n"


def test_render_reproduces_a_known_file():
    """The 20-sample example committed in this repository."""
    samples = "P5 P10 P2 K9 K1 P1 P3 K7 K2 P4 P9 P8 K10 K3 K4 K8 K6 K5 P7 P6".split()
    rendered = Phenotypes.from_samples(samples).render()
    assert rendered.splitlines() == [
        "20 2 1",
        "# P K",
        "P P P K K P P K K P P P K K K K K K P P",
    ]


def test_comparisons_covers_each_ordered_pair_then_the_rest():
    phenotypes = Phenotypes(("P", "K", "P"))
    assert phenotypes.comparisons() == [
        "P_versus_K",
        "K_versus_P",
        "P_versus_REST",
        "K_versus_REST",
    ]
    assert phenotypes.comparisons(include_rest=False) == ["P_versus_K", "K_versus_P"]


def test_round_trip_through_a_file(tmp_path):
    original = Phenotypes.from_samples(["Z1", "Z2", "C1"])
    path = write_cls(original, tmp_path / "x.cls")
    assert read_cls(path) == original


def test_read_cls_rejects_a_label_count_mismatch(tmp_path):
    path = tmp_path / "bad.cls"
    path.write_text("5 2 1\n# P K\nP P K\n", encoding="utf8")
    with pytest.raises(MalformedTableError, match="declares 5 samples but 3"):
        read_cls(path)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "20 2 1\n",
        "20 2 1\n# P K\n",
        "not a header\n# P K\nP P\n",
        "2 2 1\nP K\nP K\n",  # the class line must start with '#'
    ],
)
def test_read_cls_rejects_malformed_files(tmp_path, text):
    path = tmp_path / "bad.cls"
    path.write_text(text, encoding="utf8")
    with pytest.raises(MalformedTableError):
        read_cls(path)
