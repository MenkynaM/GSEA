"""Listing and downloading MSigDB annotations, with a fake session."""

from __future__ import annotations

import pytest

from gsea_pipeline.annotations import download_chip_files, list_chip_files
from gsea_pipeline.errors import RemoteServiceError

from .conftest import FakeResponse, FakeSession
from .sample_data import CHIP_INDEX_HTML


def test_listing_keeps_only_matching_chip_files():
    session = FakeSession([FakeResponse(text=CHIP_INDEX_HTML)])
    assert list_chip_files(session=session) == [
        "Human_AFFY_HG_U133.chip",
        "Human_Ensembl_Gene_ID_MSigDB.v7.5.1.chip",
    ]


def test_listing_excludes_non_chip_files_beginning_with_the_prefix():
    """The old filter matched any link whose text started with "H",
    which let Human_notes.txt through."""
    session = FakeSession([FakeResponse(text=CHIP_INDEX_HTML)])
    assert "Human_notes.txt" not in list_chip_files(session=session)


def test_listing_honours_another_prefix():
    session = FakeSession([FakeResponse(text=CHIP_INDEX_HTML)])
    assert list_chip_files(session=session, prefix="Mouse_") == [
        "Mouse_Gene_Symbol_Remapping.chip"
    ]


def test_download_writes_each_file(tmp_path):
    session = FakeSession(
        [
            FakeResponse(content_chunks=(b"a\tb\n", b"X\tY\n")),
            FakeResponse(content_chunks=(b"second",)),
        ]
    )
    written = download_chip_files(["one.chip", "two.chip"], tmp_path, session=session)
    assert [p.name for p in written] == ["one.chip", "two.chip"]
    assert written[0].read_bytes() == b"a\tb\nX\tY\n"


def test_download_builds_the_url_from_the_index(tmp_path):
    session = FakeSession([FakeResponse(content_chunks=(b"x",))])
    download_chip_files(["one.chip"], tmp_path, index_url="https://host/dir/", session=session)
    assert session.requests[0][1] == "https://host/dir/one.chip"


def test_existing_files_are_skipped(tmp_path):
    (tmp_path / "one.chip").write_bytes(b"old")
    session = FakeSession([])
    written = download_chip_files(["one.chip"], tmp_path, session=session)
    assert written[0].read_bytes() == b"old"
    assert session.requests == []


def test_overwrite_redownloads(tmp_path):
    (tmp_path / "one.chip").write_bytes(b"old")
    session = FakeSession([FakeResponse(content_chunks=(b"new",))])
    download_chip_files(["one.chip"], tmp_path, session=session, overwrite=True)
    assert (tmp_path / "one.chip").read_bytes() == b"new"


def test_no_partial_file_is_left_behind(tmp_path):
    session = FakeSession([FakeResponse(content_chunks=(b"x",))])
    download_chip_files(["one.chip"], tmp_path, session=session)
    assert [p.name for p in tmp_path.iterdir()] == ["one.chip"]


@pytest.mark.parametrize("name", ["../escape.chip", "nested/path.chip", "/abs.chip", ""])
def test_a_filename_that_escapes_the_directory_is_refused(tmp_path, name):
    """Filenames come from a remote page; the old code pasted them into a shell."""
    with pytest.raises(RemoteServiceError, match="suspicious filename"):
        download_chip_files([name], tmp_path, session=FakeSession([]))


def test_a_download_failure_is_reported(tmp_path):
    class Failing(FakeResponse):
        def raise_for_status(self):
            import requests

            raise requests.HTTPError("404 Not Found")

    session = FakeSession([Failing()])
    with pytest.raises(RemoteServiceError, match="could not download"):
        download_chip_files(["one.chip"], tmp_path, session=session)
