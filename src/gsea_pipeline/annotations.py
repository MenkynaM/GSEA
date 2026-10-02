"""Listing and downloading MSigDB ``*.chip`` platform annotations.

The previous implementation shelled out to ``curl`` on Windows and ``wget`` on
Linux, interpolating a remote filename straight into a shell command line.  This
downloads with :mod:`requests` -- one code path, no shell, and a filename check
so a crafted link cannot write outside the target directory.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests

from .config import ensure_dir
from .errors import RemoteServiceError
from .htmlparse import iter_links, parse_html

LOGGER = logging.getLogger(__name__)

CHIP_INDEX_URL = (
    "https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/"
)
REQUEST_TIMEOUT = 120.0
CHUNK_SIZE = 1 << 16


def list_chip_files(
    *,
    index_url: str = CHIP_INDEX_URL,
    prefix: str = "Human_",
    session: requests.Session | None = None,
) -> list[str]:
    """Return the ``*.chip`` filenames offered at ``index_url``.

    ``prefix`` filters by filename.  The old code filtered on the link text
    starting with ``"H"``, which also matched anything else beginning with that
    letter; matching the filename against a full prefix is both narrower and
    easier to change when another organism is wanted.
    """
    http = session or requests
    response = http.get(index_url, timeout=REQUEST_TIMEOUT)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RemoteServiceError(f"could not list {index_url}: {exc}") from exc

    names = []
    for link in iter_links(parse_html(response.text)):
        name = Path(unquote(link.href)).name
        if name.endswith(".chip") and name.startswith(prefix):
            names.append(name)
    return sorted(dict.fromkeys(names))


def download_chip_files(
    names: Iterable[str],
    destination: Path,
    *,
    index_url: str = CHIP_INDEX_URL,
    session: requests.Session | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """Download each name in ``names`` from ``index_url`` into ``destination``.

    Existing files are skipped unless ``overwrite`` is set, so an interrupted
    run can be repeated cheaply.
    """
    http = session or requests
    ensure_dir(destination)
    downloaded: list[Path] = []

    for name in names:
        safe_name = Path(name).name
        if not safe_name or safe_name != name:
            raise RemoteServiceError(f"refusing to download suspicious filename {name!r}")

        target = destination / safe_name
        if target.exists() and not overwrite:
            LOGGER.info("%s already present, skipping", safe_name)
            downloaded.append(target)
            continue

        url = urljoin(index_url, safe_name)
        LOGGER.info("downloading %s", url)
        partial = target.with_name(target.name + ".part")
        with http.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                raise RemoteServiceError(f"could not download {url}: {exc}") from exc
            with partial.open("wb") as handle:
                for chunk in response.iter_content(CHUNK_SIZE):
                    handle.write(chunk)
        partial.replace(target)
        downloaded.append(target)

    return downloaded
