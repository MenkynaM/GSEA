"""Protein tallies, which used to live in a module level dict."""

from __future__ import annotations

import pytest

from gsea_pipeline.errors import MalformedTableError
from gsea_pipeline.proteins import ProteinCounts

#: Columns 4 and 9 of a Proline export, padded out to the right width.
HEADER = ["", "", "", "", "name", "", "", "", "", "count"]


def row(name, count):
    cells = [""] * 10
    cells[4], cells[9] = name, count
    return cells


@pytest.fixture
def counts():
    tally = ProteinCounts()
    tally.add_rows([HEADER, row("VIM", 10), row("ALB", 4), row("VIM", 6)])
    return tally


def test_counts_are_summed_and_positions_recorded(counts):
    assert counts["VIM"].total == 16
    assert counts["VIM"].positions == [2, 4]
    assert counts["ALB"].total == 4


def test_derived_statistics(counts):
    assert counts["VIM"].occurrences == 2
    assert counts["VIM"].average_count == 8
    assert counts["VIM"].average_position == 3
    assert counts["VIM"].within_top(2) == 1
    assert counts["VIM"].within_top(4) == 2


def test_the_header_row_is_skipped(counts):
    assert "name" not in counts


def test_two_tallies_are_independent():
    """The original accumulated into a module level dict shared by every run."""
    first, second = ProteinCounts(), ProteinCounts()
    first.add_rows([HEADER, row("VIM", 1)])
    assert len(first) == 1
    assert len(second) == 0


def test_float_counts_are_truncated_to_integers():
    tally = ProteinCounts()
    tally.add_rows([HEADER, row("VIM", 3.0)])
    assert tally["VIM"].total == 3


def test_blank_names_are_ignored():
    tally = ProteinCounts()
    tally.add_rows([HEADER, row("  ", 5), row("VIM", 1)])
    assert list(tally.tallies) == ["VIM"]


def test_a_short_row_is_reported_with_its_position():
    tally = ProteinCounts()
    with pytest.raises(MalformedTableError, match=":2:"):
        tally.add_rows([HEADER, ["too", "short"]])


def test_a_non_numeric_count_is_reported():
    tally = ProteinCounts()
    with pytest.raises(MalformedTableError, match="not a number"):
        tally.add_rows([HEADER, row("VIM", "lots")])


def test_most_abundant_orders_by_total_then_name(counts):
    assert [name for name, _ in counts.most_abundant()] == ["VIM", "ALB"]


def test_report_has_a_header_and_one_line_per_protein(counts):
    lines = counts.render_report().splitlines()
    assert lines[0].split("\t") == ["NAME", "TOTAL", "OCCURRENCES", "AVERAGE_POSITION"]
    assert lines[1].split("\t") == ["VIM", "16", "2", "3.00"]
    assert len(lines) == 3
