"""The data layout, which used to be computed at import time."""

from __future__ import annotations

from gsea_pipeline.config import DATA_DIR_ENV, DataLayout, ensure_dir


def test_every_path_hangs_off_the_root(tmp_path):
    layout = DataLayout(tmp_path)
    for path in (layout.raw, layout.gct, layout.txt, layout.phenotypes, layout.gsea_output):
        assert path.parent == tmp_path


def test_from_env_reads_the_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))
    assert DataLayout.from_env().root == tmp_path.resolve()


def test_an_explicit_root_beats_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "ignored"))
    assert DataLayout.from_env(tmp_path / "chosen").root == (tmp_path / "chosen").resolve()


def test_from_env_defaults_to_data_under_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    assert DataLayout.from_env().root == (tmp_path / "data").resolve()


def test_importing_the_package_creates_nothing(tmp_path, monkeypatch):
    """``paths.py`` ran ``os.scandir`` and could block on ``input()`` at import."""
    monkeypatch.chdir(tmp_path)
    import gsea_pipeline  # noqa: F401  (re-imported for the side effects it must not have)

    assert list(tmp_path.iterdir()) == []


def test_iter_raw_files_is_sorted_and_skips_directories(tmp_path):
    layout = DataLayout(tmp_path)
    layout.raw.mkdir(parents=True)
    for name in ("b.csv", "a.csv"):
        (layout.raw / name).touch()
    (layout.raw / "subdir").mkdir()
    assert [p.name for p in layout.iter_raw_files()] == ["a.csv", "b.csv"]


def test_iter_raw_files_accepts_a_pattern(tmp_path):
    layout = DataLayout(tmp_path)
    layout.raw.mkdir(parents=True)
    (layout.raw / "keep.csv").touch()
    (layout.raw / "skip.txt").touch()
    assert [p.name for p in layout.iter_raw_files("*.csv")] == ["keep.csv"]


def test_iter_raw_files_on_a_missing_directory_is_empty(tmp_path):
    assert DataLayout(tmp_path / "nope").iter_raw_files() == []


def test_ensure_dir_is_idempotent(tmp_path):
    target = tmp_path / "a" / "b"
    assert ensure_dir(target) == target
    assert ensure_dir(target).is_dir()
