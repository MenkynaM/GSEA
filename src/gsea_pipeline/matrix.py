"""The expression matrix, and reading one from a delimited file.

``convert_file.py`` and ``convert_proline_files.py`` each re-parsed the input
file once per output format, differing only in the delimiter they split on.  A
table is parsed once into this immutable value and every writer renders it.

Cell values stay strings on purpose: these files hold measurements the pipeline
never does arithmetic on, and round-tripping them through ``float`` would
rewrite the numbers GSEA is given.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .errors import MalformedTableError

#: Delimiters tried when none is given, most specific first.
CANDIDATE_DELIMITERS = (";", "\t", ",")


@dataclass(frozen=True)
class Feature:
    """One row: a protein or gene, and its value in each sample."""

    name: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class ExpressionMatrix:
    """Features by samples, with the transforms the pipeline needs.

    Every method returns a new matrix rather than mutating this one, so a
    pipeline step can be read as the chain of transforms it is.
    """

    samples: tuple[str, ...]
    features: tuple[Feature, ...]

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    @property
    def n_features(self) -> int:
        return len(self.features)

    def rename_samples(self, rename: Callable[[str], str]) -> ExpressionMatrix:
        """Apply ``rename`` to every sample name."""
        return replace(self, samples=tuple(rename(s) for s in self.samples))

    def rename_features(self, rename: Callable[[str], str]) -> ExpressionMatrix:
        """Apply ``rename`` to every feature name."""
        return replace(
            self,
            features=tuple(replace(f, name=rename(f.name)) for f in self.features),
        )

    def map_features(self, mapping: Mapping[str, str]) -> ExpressionMatrix:
        """Keep only the features present in ``mapping``, renamed through it.

        This is the lookup-table counterpart of :meth:`rename_features`: a
        feature absent from ``mapping`` has no new name, so it is dropped.
        """
        return replace(
            self,
            features=tuple(
                replace(f, name=mapping[f.name]) for f in self.features if f.name in mapping
            ),
        )

    def drop_empty_features(self) -> ExpressionMatrix:
        """Drop features whose name is blank."""
        return replace(self, features=tuple(f for f in self.features if f.name.strip()))


def detect_delimiter(header: str) -> str:
    """Guess the delimiter of a table from its header line.

    The candidate that appears most often wins; ties go to the earlier entry of
    :data:`CANDIDATE_DELIMITERS`, which prefers the semicolon the staged tables
    use over the comma that appears inside quoted Proline descriptions.
    """
    counts = {d: header.count(d) for d in CANDIDATE_DELIMITERS}
    best = max(CANDIDATE_DELIMITERS, key=lambda d: counts[d])
    return best if counts[best] else CANDIDATE_DELIMITERS[0]


def read_matrix(
    path: str | Path,
    *,
    delimiter: str | None = None,
    encoding: str = "utf8",
) -> ExpressionMatrix:
    """Read a delimited table whose first column holds the feature names.

    Unlike the string-splitting it replaces, this honours quoting (Proline
    descriptions contain commas) and rejects ragged rows instead of writing a
    misaligned matrix downstream.
    """
    path = Path(path)
    with path.open("r", encoding=encoding, newline="") as handle:
        first_line = handle.readline()
        if not first_line.strip():
            raise MalformedTableError(path, 1, "the file is empty or has a blank header")
        if delimiter is None:
            delimiter = detect_delimiter(first_line)
        handle.seek(0)
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader)
        samples = tuple(cell.strip() for cell in header[1:])
        if not samples:
            raise MalformedTableError(
                path, 1, f"no sample columns found using delimiter {delimiter!r}"
            )

        features: list[Feature] = []
        for line_number, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue  # tolerate blank lines, including a trailing one
            if len(row) - 1 != len(samples):
                raise MalformedTableError(
                    path,
                    line_number,
                    f"expected {len(samples)} values for "
                    f"{len(samples)} samples, found {len(row) - 1}",
                )
            features.append(
                Feature(row[0].strip(), tuple(cell.strip() for cell in row[1:]))
            )

    return ExpressionMatrix(samples=samples, features=tuple(features))


def matrix_from_rows(
    samples: Sequence[str], rows: Iterable[tuple[str, Sequence[str]]]
) -> ExpressionMatrix:
    """Build a matrix from in-memory rows; handy in tests and notebooks."""
    return ExpressionMatrix(
        samples=tuple(samples),
        features=tuple(Feature(name, tuple(values)) for name, values in rows),
    )
