"""The raw-table-in, GSEA-inputs-out pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from gsea_pipeline.config import DataLayout
from gsea_pipeline.matrix import read_matrix
from gsea_pipeline.pipeline import (
    FeatureNaming,
    OutputFormat,
    normalise,
    prepare_all,
    prepare_inputs,
)

from .sample_data import PROLINE_CSV

#: The checkout this suite lives in, used by the real-data test below.
REPO_ROOT = Path(__file__).resolve().parent.parent


class StubMapper:
    """Stands in for :class:`~gsea_pipeline.uniprot.UniProtIdMapper`."""

    def __init__(self, mapping):
        self.mapping = mapping
        self.seen = None

    def kegg_genes(self, accessions):
        self.seen = list(accessions)
        return self.mapping


def test_normalise_shortens_headers_and_feature_names(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text(PROLINE_CSV, encoding="utf8")
    matrix = normalise(read_matrix(path))
    assert matrix.samples == ("Z1", "Z2", "C1")
    assert [f.name for f in matrix.features] == ["MYH9", "FLNA", "ALBU"]


def test_raw_naming_leaves_feature_names_alone(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text(PROLINE_CSV, encoding="utf8")
    matrix = normalise(read_matrix(path), naming=FeatureNaming.RAW)
    assert matrix.features[0].name == "MYH9_HUMAN"
    assert matrix.samples == ("Z1", "Z2", "C1"), "sample names are always normalised"


def test_kegg_naming_maps_and_drops_unmapped(tmp_path, caplog):
    path = tmp_path / "x.csv"
    path.write_text(PROLINE_CSV, encoding="utf8")
    mapper = StubMapper({"MYH9_HUMAN": "4627", "FLNA_HUMAN": "2316"})
    with caplog.at_level("WARNING"):
        matrix = normalise(read_matrix(path), naming=FeatureNaming.KEGG, mapper=mapper)
    assert [f.name for f in matrix.features] == ["4627", "2316"]
    assert mapper.seen == ["MYH9_HUMAN", "FLNA_HUMAN", "ALBU_HUMAN"]
    assert "dropped 1 features" in caplog.text


def test_prepare_writes_the_default_formats(proline_file, layout):
    prepared = prepare_inputs(proline_file, layout)
    assert set(prepared.outputs) == {OutputFormat.GCT, OutputFormat.CLS, OutputFormat.TXT}
    assert prepared.gct == layout.gct / "sample.gct"
    assert prepared.cls == layout.phenotypes / "sample.cls"
    assert all(path.is_file() for path in prepared.outputs.values())


def test_prepare_derives_phenotypes_from_the_sample_names(proline_file, layout):
    prepared = prepare_inputs(proline_file, layout)
    assert prepared.phenotypes.classes == ("Z", "C")
    assert prepared.cls.read_text(encoding="utf8") == "3 2 1\n# Z C\nZ Z C\n"


def test_prepare_reads_the_input_once_for_every_format(proline_file, layout, monkeypatch):
    """The old code re-parsed the file once per output format."""
    from gsea_pipeline import pipeline

    calls = []
    original = pipeline.read_matrix
    monkeypatch.setattr(
        pipeline, "read_matrix", lambda *a, **k: (calls.append(a[0]), original(*a, **k))[1]
    )
    prepare_inputs(proline_file, layout, formats=list(OutputFormat))
    assert len(calls) == 1


def test_gct_preamble_matches_the_matrix(proline_file, layout):
    prepared = prepare_inputs(proline_file, layout)
    assert prepared.gct.read_text(encoding="utf8").splitlines()[1] == "3\t3"


def test_kegg_naming_stages_into_its_own_directory(proline_file, layout):
    prepared = prepare_inputs(
        proline_file,
        layout,
        naming=FeatureNaming.KEGG,
        formats=[OutputFormat.STAGED],
        mapper=StubMapper({"MYH9_HUMAN": "4627"}),
    )
    assert prepared.outputs[OutputFormat.STAGED].parent == layout.kegg


def test_symbol_naming_stages_into_the_csv_directory(proline_file, layout):
    prepared = prepare_inputs(proline_file, layout, formats=[OutputFormat.STAGED])
    assert prepared.outputs[OutputFormat.STAGED].parent == layout.staged


def test_duplicate_formats_are_written_once(proline_file, layout):
    prepared = prepare_inputs(
        proline_file, layout, formats=[OutputFormat.GCT, OutputFormat.GCT]
    )
    assert list(prepared.outputs) == [OutputFormat.GCT]


def test_prepare_all_covers_every_raw_file(layout):
    layout.raw.mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (layout.raw / name).write_text(PROLINE_CSV, encoding="utf8")
    prepared = prepare_all(layout)
    assert [item.source.name for item in prepared] == ["a.csv", "b.csv"]


def test_prepare_all_warns_when_there_is_nothing_to_do(layout, caplog):
    with caplog.at_level("WARNING"):
        assert prepare_all(layout) == []
    assert "no input tables" in caplog.text


def test_the_staged_output_can_be_read_back(proline_file, layout):
    """Step two of the old pipeline consumed step one's output, so it must parse."""
    prepared = prepare_inputs(proline_file, layout, formats=[OutputFormat.STAGED])
    staged = read_matrix(prepared.outputs[OutputFormat.STAGED])
    assert staged.samples == prepared.matrix.samples
    assert staged.features == prepared.matrix.features


@pytest.mark.parametrize("name", ["do_gsea.csv", "skuska.csv"])
def test_the_repositorys_own_inputs_still_convert(tmp_path, name):
    """Guards the conversion against the two real tables kept in data/raw."""
    source = REPO_ROOT / "data" / "raw" / name
    if not source.is_file():
        pytest.skip(f"{name} is not checked out")
    layout = DataLayout(tmp_path)
    prepared = prepare_inputs(source, layout, formats=list(OutputFormat))
    assert prepared.matrix.n_features > 100
    assert len(prepared.phenotypes.classes) == 2
    gct = prepared.gct.read_text(encoding="utf8").splitlines()
    assert gct[0] == "#1.2"
    assert gct[1] == f"{prepared.matrix.n_features}\t{prepared.matrix.n_samples}"
    assert len(gct) == prepared.matrix.n_features + 3
