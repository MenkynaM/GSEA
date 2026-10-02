"""UniProt ID mapping.

Adapted from UniProt's published example client, trimmed to the one thing this
project asks of it -- accession to KEGG gene -- and hardened:

* every request has a timeout, so a stalled server cannot hang the pipeline;
* the polling loop accepts every queued status instead of raising on anything
  that is not ``RUNNING``, and gives up after a deadline;
* only the JSON response format is handled, which removes the TSV, XLSX and XML
  branches together with the XML merging code none of this project reached.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from requests.adapters import HTTPAdapter, Retry

from .errors import RemoteServiceError
from .naming import strip_kegg_organism

LOGGER = logging.getLogger(__name__)

API_URL = "https://rest.uniprot.org"
POLLING_INTERVAL = 3.0
POLLING_TIMEOUT = 600.0
REQUEST_TIMEOUT = 60.0
PAGE_SIZE = 500

#: Statuses that mean "not finished yet" rather than "failed".
PENDING_STATUSES = frozenset({"NEW", "QUEUED", "RUNNING"})

_NEXT_LINK = re.compile(r'<(?P<url>.+)>;\s*rel="next"')


def build_session(*, total_retries: int = 5, backoff_factor: float = 0.25) -> requests.Session:
    """A session that retries the transient 5xx responses UniProt returns."""
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=frozenset({"GET", "POST"}),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


@dataclass
class UniProtIdMapper:
    """Submits ID mapping jobs and collects their results.

    ``session`` is injectable so tests (and callers with their own retry or proxy
    configuration) do not have to reach the network.
    """

    session: requests.Session | None = None
    api_url: str = API_URL
    polling_interval: float = POLLING_INTERVAL
    polling_timeout: float = POLLING_TIMEOUT
    request_timeout: float = REQUEST_TIMEOUT

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = build_session()

    # -- low level -------------------------------------------------------
    def _get(self, url: str, **kwargs) -> requests.Response:
        response = self.session.get(url, timeout=self.request_timeout, **kwargs)
        self._check(response)
        return response

    @staticmethod
    def _check(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RemoteServiceError(
                f"{response.request.method} {response.url} failed with "
                f"{response.status_code}: {response.text[:500]}"
            ) from exc

    def submit(self, ids: Sequence[str], *, from_db: str, to_db: str) -> str:
        """Start a mapping job and return its id."""
        response = self.session.post(
            f"{self.api_url}/idmapping/run",
            data={"from": from_db, "to": to_db, "ids": ",".join(ids)},
            timeout=self.request_timeout,
        )
        self._check(response)
        try:
            return response.json()["jobId"]
        except (ValueError, KeyError) as exc:
            raise RemoteServiceError(f"no job id in response: {response.text[:500]}") from exc

    def wait_until_ready(self, job_id: str) -> None:
        """Poll the job until it finishes, or raise once the deadline passes."""
        deadline = time.monotonic() + self.polling_timeout
        while True:
            payload = self._get(f"{self.api_url}/idmapping/status/{job_id}").json()
            status = payload.get("jobStatus")
            if status is None:
                return  # a finished job answers with its results instead
            if status.upper() not in PENDING_STATUSES:
                raise RemoteServiceError(f"job {job_id} failed with status {status}")
            if time.monotonic() >= deadline:
                raise RemoteServiceError(
                    f"job {job_id} still {status} after {self.polling_timeout:.0f}s"
                )
            LOGGER.info("job %s is %s, retrying in %.0fs", job_id, status, self.polling_interval)
            time.sleep(self.polling_interval)

    def results_url(self, job_id: str) -> str:
        """The URL the finished job's results live at."""
        payload = self._get(f"{self.api_url}/idmapping/details/{job_id}").json()
        try:
            return payload["redirectURL"]
        except KeyError as exc:
            raise RemoteServiceError(f"job {job_id} has no results URL") from exc

    def _paged_results(self, url: str) -> Iterator[dict]:
        """Yield each page of a result set, following ``Link: rel="next"``."""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query.setdefault("format", ["json"])
        query.setdefault("size", [str(PAGE_SIZE)])
        url = parsed._replace(query=urlencode(query, doseq=True)).geturl()
        while url:
            response = self._get(url)
            yield response.json()
            match = _NEXT_LINK.match(response.headers.get("Link", ""))
            url = match.group("url") if match else ""

    # -- high level ------------------------------------------------------
    def map_ids(self, ids: Iterable[str], *, from_db: str, to_db: str) -> dict[str, str]:
        """Map ``ids`` from one database to another.

        Returns only the identifiers that mapped; UniProt reports the rest under
        ``failedIds``, which are logged rather than raised, because a proteomics
        table legitimately contains entries with no counterpart.
        """
        unique = list(dict.fromkeys(i for i in ids if i))
        if not unique:
            return {}

        job_id = self.submit(unique, from_db=from_db, to_db=to_db)
        self.wait_until_ready(job_id)

        mapped: dict[str, str] = {}
        failed: list[str] = []
        for page in self._paged_results(self.results_url(job_id)):
            for row in page.get("results", ()):
                mapped[row["from"]] = row["to"]
            failed.extend(page.get("failedIds", ()) or ())

        LOGGER.info(
            "mapped %d/%d identifiers from %s to %s", len(mapped), len(unique), from_db, to_db
        )
        if failed:
            LOGGER.debug("unmapped identifiers: %s", ", ".join(failed))
        return mapped

    def kegg_genes(self, accessions: Iterable[str]) -> dict[str, str]:
        """Map UniProt accessions to bare KEGG gene numbers.

        ``{"MYH9_HUMAN": "hsa:4627"}`` is returned as ``{"MYH9_HUMAN": "4627"}``,
        which is the form the GCT files use.
        """
        mapped = self.map_ids(accessions, from_db="UniProtKB_AC-ID", to_db="KEGG")
        return {key: strip_kegg_organism(value) for key, value in mapped.items()}
