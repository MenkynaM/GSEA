"""Shared fixtures.

The suite never touches the network: the UniProt and MSigDB clients take a
session, and these fixtures supply a fake one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from gsea_pipeline.config import DataLayout
from gsea_pipeline.matrix import matrix_from_rows

from .sample_data import PROLINE_CSV


@pytest.fixture
def layout(tmp_path: Path) -> DataLayout:
    """A data layout rooted in a temporary directory."""
    return DataLayout(tmp_path / "data")


@pytest.fixture
def proline_file(layout: DataLayout) -> Path:
    """A small Proline-style export in ``<layout>/raw``."""
    layout.raw.mkdir(parents=True)
    path = layout.raw / "sample.csv"
    path.write_text(PROLINE_CSV, encoding="utf8")
    return path


@pytest.fixture
def matrix():
    """A three-sample, two-feature matrix with names already normalised."""
    return matrix_from_rows(
        ["Z1", "Z2", "C1"], [("MYH9", ("1", "2", "3")), ("FLNA", ("4", "5", "6"))]
    )


@dataclass
class FakeResponse:
    """The slice of ``requests.Response`` the clients actually use."""

    payload: object = None
    text: str = ""
    headers: dict = field(default_factory=dict)
    status_code: int = 200
    content_chunks: tuple[bytes, ...] = ()

    def json(self):
        if self.payload is None:
            raise ValueError("no JSON payload")
        return self.payload

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 1):
        yield from self.content_chunks

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> bool:
        return False


@dataclass
class FakeSession:
    """Serves queued responses and records the requests it was given."""

    responses: list = field(default_factory=list)
    requests: list = field(default_factory=list)

    def _next(self, method: str, url: str, **kwargs) -> FakeResponse:
        self.requests.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError(f"unexpected {method} {url}")
        return self.responses.pop(0)

    def get(self, url, **kwargs):
        return self._next("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._next("POST", url, **kwargs)
