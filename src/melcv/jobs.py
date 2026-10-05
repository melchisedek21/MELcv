"""Exécution des générations en arrière-plan (la page web consulte l'avancement)."""

import re
import threading
import uuid

from . import analysis, config, files, writing

JOBS = {}


def executer(params, job):
    """Pipeline complet : lecture, analyse, comparaison, rédaction. Remplit job['resultat']."""
    log = job["log"].append
    modele = params.get("modele") or config.CFG["modele"]
    profil = files.lire_profil().strip()
    if len(profil) < 80:
        raise RuntimeError("Ton profil est presque vide : remplis l'onglet « Mon profil » d'abord.")
    offre = files.assembler_offre(params["offre"], log)
    if len(offre) < 40:
        raise RuntimeError("L'offre est vide ou trop courte.")
    an = analysis.analyser_offre(offre, modele, log)
    langue = params.get("langue", "auto")
    if langue == "auto":
        langue = "English" if an.get("langue_offre", "fr").lower().startswith("en") else "Français"
    log("Comparaison de l'offre avec ton profil…")
    corr = analysis.correspondances(an, profil, modele)
    log("Rédaction du document…")
    texte = writing.rediger(
        params["type"], an, corr, profil, langue, params.get("consignes", ""),
        modele, files.charger_canevas(), files.charger_references(),
    )  # fmt: skip
    texte = re.sub(r"^```\w*\n|\n```$", "", texte.strip())
    job["resultat"] = {
        "texte": texte,
        "langue": langue,
        "poste": an.get("poste", ""),
        "entreprise": an.get("entreprise", ""),
        "ecarts": [c.get("point", "") for c in corr if c.get("niveau") == "aucun"],
        "forts": sum(1 for c in corr if c.get("niveau") == "fort"),
        "total": len(corr),
    }


def lancer(params):
    jid = uuid.uuid4().hex[:8]
    job = JOBS[jid] = {"etat": "en cours", "log": [], "resultat": None}

    def travail():
        try:
            executer(params, job)
            job["etat"] = "terminé"
        except Exception as e:
            job["etat"] = "erreur"
            job["log"].append(str(e))

    threading.Thread(target=travail, daemon=True).start()
    return jid
