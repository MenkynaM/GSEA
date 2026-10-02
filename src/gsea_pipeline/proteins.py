"""Aggregating protein counts across Proline spreadsheet exports.

``scan.py`` kept its results in a module level dict, so the statistics were only
ever available for whatever the last run had loaded and could not be tested
without an Excel file.  The tally is a value here, and the spreadsheet reader is
a separate, optional adapter: the aggregation is fed plain rows.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigurationError, MalformedTableError

#: Column indices used by the Proline export this was written for.
DEFAULT_NAME_COLUMN = 4
DEFAULT_COUNT_COLUMN = 9


@dataclass
class ProteinTally:
    """One protein's total count and the row positions it was seen at."""

    total: int = 0
    positions: list[int] = field(default_factory=list)

    @property
    def occurrences(self) -> int:
        return len(self.positions)

    @property
    def average_count(self) -> float:
        return self.total / self.occurrences

    @property
    def average_position(self) -> float:
        return sum(self.positions) / self.occurrences

    def within_top(self, n: int) -> int:
        """How many times this protein appeared within the first ``n`` rows."""
        return sum(1 for position in self.positions if position <= n)


@dataclass
class ProteinCounts:
    """Protein tallies accumulated over any number of files."""

    tallies: dict[str, ProteinTally] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.tallies)

    def __contains__(self, name: str) -> bool:
        return name in self.tallies

    def __getitem__(self, name: str) -> ProteinTally:
        return self.tallies[name]

    def add(self, name: str, count: int, position: int) -> None:
        """Record one observation of ``name``."""
        tally = self.tallies.setdefault(name, ProteinTally())
        tally.total += count
        tally.positions.append(position)

    def add_rows(
        self,
        rows: Iterable[Sequence],
        *,
        name_column: int = DEFAULT_NAME_COLUMN,
        count_column: int = DEFAULT_COUNT_COLUMN,
        skip_header: bool = True,
        source: Path | str = "<rows>",
    ) -> None:
        """Record every row of a spreadsheet-like table.

        Rows are numbered from 1 as in the sheet, so a position is the rank the
        protein had in its own file.
        """
        for position, row in enumerate(rows, start=1):
            if skip_header and position == 1:
                continue
            if max(name_column, count_column) >= len(row):
                raise MalformedTableError(
                    source, position, f"row has only {len(row)} columns"
                )
            name = str(row[name_column]).strip()
            if not name:
                continue
            raw_count = row[count_column]
            try:
                count = int(float(raw_count))
            except (TypeError, ValueError) as exc:
                raise MalformedTableError(
                    source, position, f"count {raw_count!r} is not a number"
                ) from exc
            self.add(name, count, position)

    def most_abundant(self) -> list[tuple[str, ProteinTally]]:
        """Tallies ordered by total count, then by name, highest first."""
        return sorted(self.tallies.items(), key=lambda kv: (-kv[1].total, kv[0]))

    def render_report(self) -> str:
        """A tab separated report: name, total, occurrences, average position."""
        lines = ["NAME\tTOTAL\tOCCURRENCES\tAVERAGE_POSITION\n"]
        for name, tally in self.most_abundant():
            lines.append(
                f"{name}\t{tally.total}\t{tally.occurrences}\t{tally.average_position:.2f}\n"
            )
        return "".join(lines)


def read_spreadsheet_rows(path: str | Path) -> Iterator[list]:
    """Yield the rows of the first worksheet of an Excel file.

    Needs the ``excel`` extra (``pip install gsea-pipeline[excel]``): ``openpyxl``
    for ``.xlsx``, or ``xlrd`` for the legacy ``.xls`` that ``openpyxl`` cannot
    read.  Nothing else in the package imports either, so the rest of the
    pipeline runs without them.
    """
    path = Path(path)
    if path.suffix.lower() == ".xls":
        try:
            import xlrd  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise ConfigurationError(
                f"reading the legacy .xls file {path.name} needs xlrd: pip install xlrd"
            ) from exc
        sheet = xlrd.open_workbook(str(path)).sheet_by_index(0)
        for index in range(sheet.nrows):
            yield list(sheet.row_values(index))
        return

    try:
        from openpyxl import load_workbook  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ConfigurationError(
            f"reading {path.name} needs openpyxl: pip install 'gsea-pipeline[excel]'"
        ) from exc
    workbook = load_workbook(str(path), read_only=True, data_only=True)
    try:
        for row in workbook.worksheets[0].iter_rows(values_only=True):
            yield list(row)
    finally:
        workbook.close()


def tally_spreadsheets(
    paths: Iterable[str | Path],
    *,
    name_column: int = DEFAULT_NAME_COLUMN,
    count_column: int = DEFAULT_COUNT_COLUMN,
) -> ProteinCounts:
    """Aggregate every spreadsheet in ``paths`` into one tally."""
    counts = ProteinCounts()
    for path in paths:
        path = Path(path)
        counts.add_rows(
            read_spreadsheet_rows(path),
            name_column=name_column,
            count_column=count_column,
            source=path,
        )
    return counts
