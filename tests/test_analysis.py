from melcv import analysis
from melcv import llm as ia


def test_decouper_respecte_la_taille_et_garde_tout():
    texte = "\n".join(f"Ligne numéro {i} " + "x" * 80 for i in range(200))
    blocs = analysis.decouper(texte, taille=2000)
    assert len(blocs) > 5
    assert all(len(b) < 2200 for b in blocs)
    assert "".join(blocs).count("Ligne numéro") == 200


def test_fusionner_dedoublonne_et_garde_le_premier_texte():
    res = analysis.fusionner(
        [
            {"poste": "Architecte", "exigences": ["SaaS", "API"], "lieu": ""},
            {"poste": "Autre", "exigences": ["saas", "TOGAF"], "lieu": "Ottawa"},
            "pas un dict",
        ]
    )
    assert res["poste"] == "Architecte"
    assert res["lieu"] == "Ottawa"
    assert res["exigences"] == ["SaaS", "API", "TOGAF"]


def test_analyser_offre_longue_appelle_le_modele_par_morceaux(monkeypatch):
    appels = []

    def faux(prompt, modele, json_mode=False):
        appels.append(prompt)
        return {"mots_cles": [f"mot{len(appels)}"]}

    monkeypatch.setattr(ia, "llm", faux)
    offre = "\n".join("Paragraphe " + "y" * 200 for _ in range(100))
    res = analysis.analyser_offre(offre, "test", log=lambda m: None)
    assert len(appels) > 1
    assert len(res["mots_cles"]) == len(appels)


def test_correspondances_sans_points_ne_sollicite_pas_le_modele(monkeypatch):
    monkeypatch.setattr(ia, "llm", lambda *a, **k: 1 / 0)
    vide = analysis.fusionner([])
    assert analysis.correspondances(vide, "profil", "test") == []
