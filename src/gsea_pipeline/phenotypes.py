"""Phenotype labels and the ``.cls`` files that carry them.

A ``.cls`` file is three lines::

    <samples> <classes> 1
    # <class name> <class name> ...
    <label per sample, in column order>

The classes are the group prefixes of the sample names, in first-seen order --
that order is what GSEA reports as "phenotype" and what the ``#A_versus_B``
suffix on a ``-cls`` argument refers to, so it is preserved rather than sorted.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .errors import MalformedTableError
from .naming import sample_group


@dataclass(frozen=True)
class Phenotypes:
    """The class label of each sample, in column order."""

    labels: tuple[str, ...]

    @property
    def classes(self) -> tuple[str, ...]:
        """The distinct labels, in first-seen order."""
        seen: dict[str, None] = {}
        for label in self.labels:
            seen.setdefault(label, None)
        return tuple(seen)

    @property
    def n_samples(self) -> int:
        return len(self.labels)

    @classmethod
    def from_samples(cls, samples: Sequence[str]) -> Phenotypes:
        """Derive the labels from sample names such as ``P5`` or ``Z12``."""
        return cls(tuple(sample_group(s) for s in samples))

    def render(self) -> str:
        """Render the ``.cls`` file contents."""
        return (
            f"{self.n_samples} {len(self.classes)} 1\n"
            f"# {' '.join(self.classes)}\n"
            f"{' '.join(self.labels)}\n"
        )

    def comparisons(self, *, include_rest: bool = True) -> list[str]:
        """The comparison selectors GSEA accepts after a ``.cls#`` argument.

        Every ordered pair of distinct classes, then optionally each class
        against the rest::

            >>> Phenotypes(("P", "K", "P")).comparisons()
            ['P_versus_K', 'K_versus_P', 'P_versus_REST', 'K_versus_REST']
        """
        classes = self.classes
        pairs = [
            f"{first}_versus_{second}"
            for first in classes
            for second in classes
            if first != second
        ]
        if include_rest:
            pairs += [f"{name}_versus_REST" for name in classes]
        return pairs


def read_cls(path: str | Path, *, encoding: str = "utf8") -> Phenotypes:
    """Read a ``.cls`` file, checking it against its own declared header."""
    path = Path(path)
    lines = [
        line.strip()
        for line in path.read_text(encoding=encoding).splitlines()
        if line.strip()
    ]
    if len(lines) < 3:
        raise MalformedTableError(path, len(lines), "a .cls file needs three lines")

    header = lines[0].split()
    if len(header) < 2 or not header[0].isdigit():
        raise MalformedTableError(path, 1, f"unreadable .cls header: {lines[0]!r}")
    declared_samples = int(header[0])

    if not lines[1].startswith("#"):
        raise MalformedTableError(path, 2, "the class name line must start with '#'")

    labels = tuple(lines[2].split())
    if len(labels) != declared_samples:
        raise MalformedTableError(
            path,
            3,
            f"header declares {declared_samples} samples but {len(labels)} labels follow",
        )
    return Phenotypes(labels)
