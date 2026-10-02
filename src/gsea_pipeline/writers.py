"""Rendering an :class:`~gsea_pipeline.matrix.ExpressionMatrix` to GSEA inputs.

GCT, TXT and the two CSV flavours differ only in a preamble and a delimiter, so
they share one serialiser here instead of one hand-rolled loop each.  The loops
they replace built their output with ``text = text + line``, which is quadratic
in the number of features; these stream row by row.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

from .config import ensure_dir
from .matrix import ExpressionMatrix
from .phenotypes import Phenotypes

#: GSEA fills the mandatory GCT description column with this when there is none.
NO_DESCRIPTION = "na"

#: Version line every GCT file starts with.
GCT_VERSION = "#1.2"


def _tab_rows(matrix: ExpressionMatrix) -> Iterator[str]:
    """Yield the shared tab separated body of the GCT and TXT formats."""
    yield "NAME\tDESCRIPTION\t" + "\t".join(matrix.samples) + "\n"
    for feature in matrix.features:
        yield "\t".join((feature.name, NO_DESCRIPTION, *feature.values)) + "\n"


def write_gct(matrix: ExpressionMatrix, path: str | Path, *, encoding: str = "utf8") -> Path:
    """Write ``matrix`` as a GCT file: the TXT body behind a two line preamble."""
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(f"{GCT_VERSION}\n{matrix.n_features}\t{matrix.n_samples}\n")
        handle.writelines(_tab_rows(matrix))
    return path


def write_txt(matrix: ExpressionMatrix, path: str | Path, *, encoding: str = "utf8") -> Path:
    """Write ``matrix`` as a plain tab separated table."""
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.writelines(_tab_rows(matrix))
    return path


def write_delimited(
    matrix: ExpressionMatrix,
    path: str | Path,
    *,
    delimiter: str = ";",
    index_header: str = "#",
    quoting: int = csv.QUOTE_MINIMAL,
    encoding: str = "utf8",
) -> Path:
    """Write ``matrix`` as a delimited table with the feature names first.

    ``index_header`` names the feature column; pass ``""`` to leave it unnamed,
    as a pandas index CSV does.
    """
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter, quoting=quoting, lineterminator="\n")
        writer.writerow([index_header, *matrix.samples])
        for feature in matrix.features:
            writer.writerow([feature.name, *feature.values])
    return path


def write_wide_csv(matrix: ExpressionMatrix, path: str | Path, **kwargs) -> Path:
    """Write the comma separated export, ready to reopen in pandas.

    The layout is what ``DataFrame.to_csv()`` produces -- an unnamed first column
    holding the feature names -- so ``read_csv(path, index_col=0)`` round-trips
    it.  Cells are quoted only where a comma or quote makes it necessary.
    """
    return write_delimited(matrix, path, delimiter=",", index_header="", **kwargs)


def write_staged_csv(matrix: ExpressionMatrix, path: str | Path, **kwargs) -> Path:
    """Write the semicolon separated staging table used between pipeline steps."""
    return write_delimited(matrix, path, delimiter=";", index_header="#", **kwargs)


def write_cls(
    phenotypes: Phenotypes, path: str | Path, *, encoding: str = "utf8"
) -> Path:
    """Write a ``.cls`` phenotype file."""
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(phenotypes.render(), encoding=encoding)
    return path
