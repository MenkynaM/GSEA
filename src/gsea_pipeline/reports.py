"""Reading what GSEA wrote.

A GSEA run produces a directory with an ``index.html`` summary, one HTML page per
gene set, and the matching TSV files.  This module reads the HTML, which is what
``scrape.py`` did, and fixes two bugs it had:

* ``scrape_for_score`` read the *first* ``<li>`` of ``index.html`` and sliced it
  at fixed offsets.  The first item is the "upregulated in phenotype" count, not
  the FDR one its docstring described, and the slice raised ``ValueError`` on the
  reports in this repository.  The counts are now matched by pattern, per
  phenotype, so both phenotypes of a run are reported.
* ``scrape_file`` wrote each table to ``f'{file}'[:-4] + '.csv'``, stripping four
  characters off the *gene set name* rather than an extension -- which is why the
  committed output holds ``HALLMARK_COAGULA.csv``.  The full name is kept.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .config import ensure_dir
from .errors import ReportParsingError
from .htmlparse import Node, Table, iter_links, list_items, parse_html, read_table

LOGGER = logging.getLogger(__name__)

#: Name of the summary page GSEA writes at the top of every report directory.
INDEX_NAME = "index.html"

#: Subdirectory the scraped tables are written into.
CONVERTED_DIRNAME = "converted"

_UPREGULATED = re.compile(
    r"(?P<count>\d+)\s*/\s*(?P<total>\d+)\s+gene sets are upregulated in phenotype\s+(?P<phenotype>\S+)"
)
_FDR = re.compile(r"(?P<count>\d+)\s+gene sets are signif\w*(?:\s+enriched)?\s+at FDR\s*<\s*25%")
_NOMINAL = re.compile(
    r"(?P<count>\d+)\s+gene sets are signif\w*(?:\s+enriched)?\s+at nominal pvalue\s*<\s*(?P<level>\d+)%"
)


@dataclass(frozen=True)
class PhenotypeSummary:
    """The headline counts GSEA reports for one phenotype of a run."""

    phenotype: str
    upregulated: int
    gene_sets: int
    fdr_below_25: int = 0
    nominal_p_below_1: int = 0
    nominal_p_below_5: int = 0


@dataclass(frozen=True)
class ReportSummary:
    """A whole report directory, summarised."""

    path: Path
    phenotypes: tuple[PhenotypeSummary, ...]

    @property
    def score(self) -> int:
        """Gene sets enriched at FDR < 25% across both phenotypes.

        This is the number ``scrape_for_score`` set out to return, and the one
        worth ranking a parameter sweep by.
        """
        return sum(p.fdr_below_25 for p in self.phenotypes)


def summarise_index(path: str | Path) -> ReportSummary:
    """Read the headline counts out of a report's ``index.html``."""
    path = Path(path)
    items = list_items(parse_html(path.read_text(encoding="utf8", errors="replace")))

    phenotypes: list[PhenotypeSummary] = []
    current: dict | None = None
    for item in items:
        start = _UPREGULATED.search(item)
        if start:
            if current:
                phenotypes.append(PhenotypeSummary(**current))
            current = {
                "phenotype": start.group("phenotype"),
                "upregulated": int(start.group("count")),
                "gene_sets": int(start.group("total")),
            }
            continue
        if current is None:
            continue
        fdr = _FDR.search(item)
        if fdr:
            current["fdr_below_25"] = int(fdr.group("count"))
            continue
        nominal = _NOMINAL.search(item)
        if nominal:
            key = f"nominal_p_below_{nominal.group('level')}"
            if key in PhenotypeSummary.__dataclass_fields__:
                current[key] = int(nominal.group("count"))
    if current:
        phenotypes.append(PhenotypeSummary(**current))

    if not phenotypes:
        raise ReportParsingError(f"{path}: no phenotype summary found")
    return ReportSummary(path.parent, tuple(phenotypes))


def find_reports(root: str | Path) -> list[Path]:
    """Every report directory under ``root``, found by its ``index.html``."""
    return sorted(p.parent for p in Path(root).rglob(INDEX_NAME))


def gene_set_names(report_dir: str | Path) -> list[str]:
    """The gene sets a report has a detail page for.

    Taken from the per-phenotype report pages, whose "GS DETAILS" column links to
    each ``<gene set>.html``.
    """
    report_dir = Path(report_dir)
    names: list[str] = []
    for page in sorted(report_dir.glob("gsea_report_for_*.html")):
        root = parse_html(page.read_text(encoding="utf8", errors="replace"))
        for link in iter_links(root):
            href = Path(link.href)
            if href.suffix == ".html" and (report_dir / href.name).exists():
                names.append(href.stem)
    return sorted(dict.fromkeys(names))


def _rich_table(markup: str, source: Path) -> Table:
    root: Node = parse_html(markup)
    container = root.find("div", css_class="richTable")
    if container is None:
        raise ReportParsingError(f"{source}: no enrichment table found")
    return read_table(container)


def gene_set_table(path: str | Path) -> Table:
    """Read the per-gene enrichment table from one gene set's HTML page."""
    path = Path(path)
    return _rich_table(path.read_text(encoding="utf8", errors="replace"), path)


def export_gene_set_tables(
    report_dir: str | Path, destination: str | Path | None = None
) -> list[Path]:
    """Write every gene set's enrichment table beside the report as CSV.

    Defaults to a ``converted/`` subdirectory of the report, which is where the
    original put them.
    """
    report_dir = Path(report_dir)
    destination = ensure_dir(Path(destination) if destination else report_dir / CONVERTED_DIRNAME)

    written: list[Path] = []
    for name in gene_set_names(report_dir):
        source = report_dir / f"{name}.html"
        try:
            table = gene_set_table(source)
        except ReportParsingError as exc:
            LOGGER.warning("skipping %s: %s", source.name, exc)
            continue
        target = destination / f"{name}.csv"
        with target.open("w", encoding="utf8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(table.header)
            writer.writerows(table.rows)
        written.append(target)
    return written
