"""Where files live.

The previous ``paths.py`` computed every path from ``os.getcwd()`` at import
time and, on Windows, could block on an ``input()`` prompt just because
something imported it.  Here the layout is an ordinary value: build one, pass it
around, override it in tests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

#: Environment variable that overrides the data directory.
DATA_DIR_ENV = "GSEA_DATA_DIR"


@dataclass(frozen=True)
class DataLayout:
    """The directory tree the pipeline reads from and writes to.

    Every attribute is derived from :attr:`root`, so relocating the whole tree
    is a single argument.
    """

    root: Path

    @classmethod
    def from_env(cls, root: str | os.PathLike[str] | None = None) -> DataLayout:
        """Build a layout from an explicit root, ``$GSEA_DATA_DIR``, or ``./data``."""
        if root is None:
            root = os.environ.get(DATA_DIR_ENV) or Path.cwd() / "data"
        return cls(Path(root).expanduser().resolve())

    # -- inputs ----------------------------------------------------------
    @property
    def raw(self) -> Path:
        """Source tables exactly as exported from Proline."""
        return self.root / "raw"

    @property
    def chips(self) -> Path:
        """``*.chip`` platform annotations downloaded from MSigDB."""
        return self.root / "chips"

    @property
    def gmt(self) -> Path:
        """``*.gmt`` gene set databases."""
        return self.root / "gmt"

    # -- generated inputs for GSEA ---------------------------------------
    @property
    def staged(self) -> Path:
        """Normalised copies of the raw tables, one row per feature."""
        return self.root / "csv"

    @property
    def wide(self) -> Path:
        """Quoted CSV exports, convenient to reopen in pandas or Excel."""
        return self.root / "converted"

    @property
    def kegg(self) -> Path:
        """Tables whose feature names were mapped to KEGG gene identifiers."""
        return self.root / "kegg"

    @property
    def gct(self) -> Path:
        """``*.gct`` expression matrices."""
        return self.root / "gct"

    @property
    def txt(self) -> Path:
        """Tab separated expression matrices without the GCT preamble."""
        return self.root / "txt"

    @property
    def phenotypes(self) -> Path:
        """``*.cls`` phenotype label files."""
        return self.root / "phenotypes"

    # -- outputs ---------------------------------------------------------
    @property
    def gsea_output(self) -> Path:
        """Parent directory GSEA writes its report folders into."""
        return self.root / "gsea"

    def iter_raw_files(self, pattern: str = "*") -> list[Path]:
        """Return the raw input files, sorted, so runs are reproducible."""
        if not self.raw.is_dir():
            return []
        return sorted(p for p in self.raw.glob(pattern) if p.is_file())


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
