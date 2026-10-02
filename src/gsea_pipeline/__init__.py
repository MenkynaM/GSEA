"""Prepare GSEA inputs from Proline exports, run GSEA, and read its reports.

The pieces, smallest first:

* :mod:`~gsea_pipeline.config` -- where files live.
* :mod:`~gsea_pipeline.naming` -- Proline and UniProt name normalisation.
* :mod:`~gsea_pipeline.matrix` -- the expression matrix and reading one.
* :mod:`~gsea_pipeline.phenotypes` -- sample groups and ``.cls`` files.
* :mod:`~gsea_pipeline.writers` -- rendering a matrix as GCT, TXT or CSV.
* :mod:`~gsea_pipeline.uniprot` -- accession to KEGG gene mapping.
* :mod:`~gsea_pipeline.annotations` -- MSigDB ``*.chip`` downloads.
* :mod:`~gsea_pipeline.gsea` -- locating and running GSEA desktop.
* :mod:`~gsea_pipeline.reports` -- reading the HTML GSEA writes.
* :mod:`~gsea_pipeline.proteins` -- protein tallies over spreadsheet exports.
* :mod:`~gsea_pipeline.pipeline` -- raw table in, GSEA inputs out.
"""

from __future__ import annotations

from .config import DataLayout
from .errors import (
    ConfigurationError,
    GseaNotFoundError,
    GseaPipelineError,
    MalformedTableError,
    RemoteServiceError,
    ReportParsingError,
)
from .gsea import GseaInstallation, run_gsea
from .matrix import ExpressionMatrix, Feature, read_matrix
from .phenotypes import Phenotypes, read_cls
from .pipeline import FeatureNaming, OutputFormat, prepare_all, prepare_inputs

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "DataLayout",
    "ExpressionMatrix",
    "Feature",
    "FeatureNaming",
    "GseaInstallation",
    "GseaNotFoundError",
    "GseaPipelineError",
    "MalformedTableError",
    "OutputFormat",
    "Phenotypes",
    "RemoteServiceError",
    "ReportParsingError",
    "__version__",
    "prepare_all",
    "prepare_inputs",
    "read_cls",
    "read_matrix",
    "run_gsea",
]
