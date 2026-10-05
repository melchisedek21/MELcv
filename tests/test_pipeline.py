import pytest

from melcv import config, jobs, writing
from melcv import llm as ia

PROFIL = "NOM : Marie Tremblay\nEXPÉRIENCES : architecte principale chez X de 2018 à 2026, gouvernance."
OFFRE = "Poste : Architecte d'entreprise chez EDC. Missions : gouvernance, feuilles de route. " * 3


def faux_llm(prompt, modele, json_mode=False):
    if json_mode and "Compare chaque" in prompt:
        return {"correspondances": [
            {"point": "gouvernance", "preuve": "8 ans chez X", "niveau": "fort"},
            {"point": "Salesforce", "preuve": "", "niveau": "aucun"},
        ]}  # fmt: skip
    if json_mode:
        return {"poste": "Architecte", "entreprise": "EDC", "langue_offre": "en",
                "exigences": ["gouvernance", "Salesforce"]}  # fmt: skip
    return "```\nDear Hiring Manager,\n\nTexte.\n```"


def nouveau_job():
    return {"etat": "en cours", "log": [], "resultat": None}


def test_pipeline_complet(maison, monkeypatch):
    monkeypatch.setattr(ia, "llm", faux_llm)
    config.PROFIL_FILE.write_text(PROFIL * 2, encoding="utf-8")
    job = nouveau_job()
    jobs.executer({"type": "motivation", "offre": OFFRE, "langue": "auto"}, job)
    res = job["resultat"]
    assert res["langue"] == "English"  # détectée dans l'offre
    assert res["ecarts"] == ["Salesforce"]
    assert (res["forts"], res["total"]) == (1, 2)
    assert "```" not in res["texte"]


def test_profil_vide_refuse(maison):
    with pytest.raises(RuntimeError, match="profil"):
        jobs.executer({"type": "cv", "offre": OFFRE}, nouveau_job())


def test_offre_trop_courte_refusee(maison):
    config.PROFIL_FILE.write_text(PROFIL * 2, encoding="utf-8")
    with pytest.raises(RuntimeError, match="offre"):
        jobs.executer({"type": "cv", "offre": "ok"}, nouveau_job())


def test_langue_imposee_prioritaire(maison, monkeypatch):
    prompts = []

    def espion(prompt, modele, json_mode=False):
        prompts.append(prompt)
        return faux_llm(prompt, modele, json_mode)

    monkeypatch.setattr(ia, "llm", espion)
    config.PROFIL_FILE.write_text(PROFIL * 2, encoding="utf-8")
    jobs.executer({"type": "cv", "offre": OFFRE, "langue": "Français"}, nouveau_job())
    assert "LANGUE DU DOCUMENT : Français" in prompts[-1]


def test_dates():
    from datetime import date

    assert writing.aujourdhui("Français", date(2026, 10, 1)) == "1er octobre 2026"
    assert writing.aujourdhui("English", date(2026, 10, 5)) == "October 5, 2026"
