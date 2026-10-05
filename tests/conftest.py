import pytest

from melcv import config, jobs


@pytest.fixture
def maison(tmp_path, monkeypatch):
    """Dossier de travail isolé pour chaque test."""
    for nom in ("DATA", "MODELES", "REFS", "SORTIES"):
        dossier = tmp_path / nom.lower()
        dossier.mkdir()
        monkeypatch.setattr(config, nom, dossier)
    monkeypatch.setattr(config, "PROFIL_FILE", tmp_path / "data" / "profil.txt")
    monkeypatch.setattr(config, "CFG_FILE", tmp_path / "data" / "reglages.json")
    jobs.JOBS.clear()
    return tmp_path
