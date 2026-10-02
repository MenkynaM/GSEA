"""The UniProt client, driven entirely by a fake session."""

from __future__ import annotations

import pytest

from gsea_pipeline.errors import RemoteServiceError
from gsea_pipeline.uniprot import UniProtIdMapper

from .conftest import FakeResponse, FakeSession


def mapper(responses, **kwargs):
    session = FakeSession(responses)
    return UniProtIdMapper(session=session, polling_interval=0, **kwargs), session


def test_map_ids_submits_polls_and_collects(monkeypatch):
    client, session = mapper(
        [
            FakeResponse(payload={"jobId": "job-1"}),
            FakeResponse(payload={"jobStatus": "RUNNING"}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://rest.uniprot.org/results/job-1"}),
            FakeResponse(
                payload={"results": [{"from": "MYH9_HUMAN", "to": "hsa:4627"}], "failedIds": []}
            ),
        ]
    )
    monkeypatch.setattr("gsea_pipeline.uniprot.time.sleep", lambda _: None)

    assert client.map_ids(["MYH9_HUMAN"], from_db="UniProtKB_AC-ID", to_db="KEGG") == {
        "MYH9_HUMAN": "hsa:4627"
    }
    assert session.requests[0][0] == "POST"
    assert session.requests[0][2]["data"]["ids"] == "MYH9_HUMAN"


def test_kegg_genes_strips_the_organism_prefix():
    client, _ = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(
                payload={
                    "results": [
                        {"from": "MYH9_HUMAN", "to": "hsa:4627"},
                        {"from": "ALBU_HUMAN", "to": "hsa:213"},
                    ]
                }
            ),
        ]
    )
    assert client.kegg_genes(["MYH9_HUMAN", "ALBU_HUMAN"]) == {
        "MYH9_HUMAN": "4627",
        "ALBU_HUMAN": "213",
    }


def test_paginated_results_are_combined():
    client, _ = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(
                payload={"results": [{"from": "A", "to": "hsa:1"}]},
                headers={"Link": '<https://example.invalid/page2>; rel="next"'},
            ),
            FakeResponse(payload={"results": [{"from": "B", "to": "hsa:2"}]}),
        ]
    )
    assert client.kegg_genes(["A", "B"]) == {"A": "1", "B": "2"}


def test_empty_input_makes_no_requests():
    client, session = mapper([])
    assert client.kegg_genes([]) == {}
    assert session.requests == []


def test_duplicate_ids_are_submitted_once():
    client, session = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(payload={"results": []}),
        ]
    )
    client.kegg_genes(["A", "A", "B", ""])
    assert session.requests[0][2]["data"]["ids"] == "A,B"


@pytest.mark.parametrize("status", ["NEW", "QUEUED", "RUNNING"])
def test_queued_statuses_are_polled_not_raised(monkeypatch, status):
    """The original raised on anything that was not exactly RUNNING."""
    client, _ = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"jobStatus": status}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(payload={"results": []}),
        ]
    )
    monkeypatch.setattr("gsea_pipeline.uniprot.time.sleep", lambda _: None)
    assert client.kegg_genes(["A"]) == {}


def test_a_failed_job_is_reported():
    client, _ = mapper(
        [FakeResponse(payload={"jobId": "j"}), FakeResponse(payload={"jobStatus": "ERROR"})]
    )
    with pytest.raises(RemoteServiceError, match="status ERROR"):
        client.kegg_genes(["A"])


def test_polling_gives_up_at_the_deadline(monkeypatch):
    client, _ = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"jobStatus": "RUNNING"}),
        ],
        polling_timeout=0,
    )
    monkeypatch.setattr("gsea_pipeline.uniprot.time.sleep", lambda _: None)
    with pytest.raises(RemoteServiceError, match="still RUNNING"):
        client.kegg_genes(["A"])


def test_a_response_without_a_job_id_is_reported():
    client, _ = mapper([FakeResponse(payload={"unexpected": True}, text="{}")])
    with pytest.raises(RemoteServiceError, match="no job id"):
        client.kegg_genes(["A"])


def test_every_request_carries_a_timeout():
    """Without one a stalled server hangs the pipeline for good."""
    client, session = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"results": [], "failedIds": []}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(payload={"results": []}),
        ]
    )
    client.kegg_genes(["A"])
    assert all("timeout" in kwargs for _, _, kwargs in session.requests)


def test_unmapped_identifiers_are_logged_not_raised(caplog):
    client, _ = mapper(
        [
            FakeResponse(payload={"jobId": "j"}),
            FakeResponse(payload={"results": [], "failedIds": ["NOPE"]}),
            FakeResponse(payload={"redirectURL": "https://example.invalid/results/j"}),
            FakeResponse(payload={"results": [{"from": "A", "to": "hsa:1"}], "failedIds": ["NOPE"]}),
        ]
    )
    with caplog.at_level("INFO"):
        assert client.kegg_genes(["A", "NOPE"]) == {"A": "1"}
    assert "mapped 1/2" in caplog.text
