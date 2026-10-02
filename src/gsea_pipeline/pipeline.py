"""Turning a raw Proline export into the files GSEA needs.

This replaces the ``if __name__ == "__main__"`` blocks of ``convert_file.py`` and
``convert_proline_files.py``.  Those were two pipelines that differed only in how
they named features -- gene symbols in one, KEGG identifiers in the other -- and
each re-read its input once per output format.  Here one function reads the table
once and the feature naming is an argument.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .config import DataLayout
from .matrix import ExpressionMatrix, read_matrix
from .naming import sample_name, strip_organism_suffix
from .phenotypes import Phenotypes
from .uniprot import UniProtIdMapper
from .writers import write_cls, write_gct, write_staged_csv, write_txt, write_wide_csv

LOGGER = logging.getLogger(__name__)


class FeatureNaming(str, Enum):
    """How feature names are derived from the raw table's first column."""

    #: Strip the UniProt organism suffix: ``MYH9_HUMAN`` -> ``MYH9``.
    SYMBOL = "symbol"
    #: Map accessions to KEGG gene numbers over the network, dropping the rest.
    KEGG = "kegg"
    #: Leave the names exactly as they are.
    RAW = "raw"


class OutputFormat(str, Enum):
    """A file the pipeline can produce for one input table."""

    GCT = "gct"
    CLS = "cls"
    TXT = "txt"
    #: Semicolon separated staging table, the intermediate the old code wrote.
    STAGED = "staged"
    #: Quoted comma separated export, convenient to reopen in pandas.
    WIDE = "wide"


#: What a plain ``prepare`` run produces: everything GSEA itself needs.
DEFAULT_FORMATS: tuple[OutputFormat, ...] = (
    OutputFormat.GCT,
    OutputFormat.CLS,
    OutputFormat.TXT,
)


@dataclass(frozen=True)
class PreparedInputs:
    """What :func:`prepare_inputs` produced for one raw table."""

    source: Path
    matrix: ExpressionMatrix
    phenotypes: Phenotypes
    outputs: dict[OutputFormat, Path]

    @property
    def gct(self) -> Path | None:
        return self.outputs.get(OutputFormat.GCT)

    @property
    def cls(self) -> Path | None:
        return self.outputs.get(OutputFormat.CLS)


def normalise(
    matrix: ExpressionMatrix,
    *,
    naming: FeatureNaming = FeatureNaming.SYMBOL,
    mapper: UniProtIdMapper | None = None,
) -> ExpressionMatrix:
    """Reduce Proline column headers to sample names and rename the features."""
    matrix = matrix.rename_samples(sample_name).drop_empty_features()

    if naming is FeatureNaming.SYMBOL:
        return matrix.rename_features(strip_organism_suffix)
    if naming is FeatureNaming.KEGG:
        mapper = mapper or UniProtIdMapper()
        accessions = [feature.name for feature in matrix.features]
        mapping = mapper.kegg_genes(accessions)
        mapped = matrix.map_features(mapping)
        dropped = matrix.n_features - mapped.n_features
        if dropped:
            LOGGER.warning("dropped %d features with no KEGG counterpart", dropped)
        return mapped
    return matrix


def prepare_inputs(
    source: str | Path,
    layout: DataLayout,
    *,
    naming: FeatureNaming = FeatureNaming.SYMBOL,
    formats: Sequence[OutputFormat] = DEFAULT_FORMATS,
    delimiter: str | None = None,
    mapper: UniProtIdMapper | None = None,
) -> PreparedInputs:
    """Read one raw table and write the requested GSEA inputs for it."""
    source = Path(source)
    stem = source.stem
    LOGGER.info("preparing %s", source)

    matrix = normalise(
        read_matrix(source, delimiter=delimiter), naming=naming, mapper=mapper
    )
    if not matrix.features:
        LOGGER.warning("%s produced no features; nothing written", source.name)
    phenotypes = Phenotypes.from_samples(matrix.samples)

    base = layout.kegg if naming is FeatureNaming.KEGG else layout.staged
    targets = {
        OutputFormat.GCT: (layout.gct / f"{stem}.gct", write_gct),
        OutputFormat.TXT: (layout.txt / f"{stem}.txt", write_txt),
        OutputFormat.STAGED: (base / f"{stem}.csv", write_staged_csv),
        OutputFormat.WIDE: (layout.wide / f"{stem}.csv", write_wide_csv),
    }

    outputs: dict[OutputFormat, Path] = {}
    for fmt in dict.fromkeys(formats):
        if fmt is OutputFormat.CLS:
            outputs[fmt] = write_cls(phenotypes, layout.phenotypes / f"{stem}.cls")
        else:
            path, writer = targets[fmt]
            outputs[fmt] = writer(matrix, path)
        LOGGER.info("wrote %s", outputs[fmt])

    return PreparedInputs(source, matrix, phenotypes, outputs)


def prepare_all(
    layout: DataLayout,
    *,
    sources: Iterable[str | Path] | None = None,
    naming: FeatureNaming = FeatureNaming.SYMBOL,
    formats: Sequence[OutputFormat] = DEFAULT_FORMATS,
    delimiter: str | None = None,
    mapper: UniProtIdMapper | None = None,
) -> list[PreparedInputs]:
    """Prepare every raw table, or just ``sources`` when given."""
    paths = list(sources) if sources is not None else layout.iter_raw_files()
    if not paths:
        LOGGER.warning("no input tables found in %s", layout.raw)
    return [
        prepare_inputs(
            path,
            layout,
            naming=naming,
            formats=formats,
            delimiter=delimiter,
            mapper=mapper,
        )
        for path in paths
    ]
