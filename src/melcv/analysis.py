"""Analyse d'une offre (même très longue) et comparaison avec le profil."""

import json
import re

from . import llm as ia

CHAMPS_LISTES = ("missions", "exigences", "atouts", "mots_cles", "valeurs_culture")
SCHEMA = (
    '{"poste":"","entreprise":"","lieu":"","reference":"","date_limite":"","type_emploi":"",'
    '"langue_offre":"fr ou en ou autre","missions":[],"exigences":[],"atouts":[],'
    '"mots_cles":[],"valeurs_culture":[],"ton":"","contact":""}'
)


def decouper(texte, taille=5500):
    """Coupe un long texte en blocs d'environ `taille` caractères, sur les fins de paragraphe."""
    blocs, courant = [], ""
    for para in re.split(r"\n+", texte):
        if courant and len(courant) + len(para) > taille:
            blocs.append(courant)
            courant = ""
        courant += para + "\n"
    if courant.strip():
        blocs.append(courant)
    return blocs


def fusionner(resultats):
    """Fusionne les analyses partielles : listes dédoublonnées, premier champ texte non vide."""
    base = json.loads(SCHEMA.replace("fr ou en ou autre", "fr"))
    out = {k: ([] if k in CHAMPS_LISTES else "") for k in base}
    for res in resultats:
        if not isinstance(res, dict):
            continue
        for cle, val in res.items():
            if cle not in out:
                continue
            if isinstance(out[cle], list):
                connus = {x.lower() for x in out[cle]}
                for x in val if isinstance(val, list) else [val]:
                    x = str(x).strip()
                    if x and x.lower() not in connus:
                        out[cle].append(x)
                        connus.add(x.lower())
            elif not out[cle] and isinstance(val, str) and val.strip():
                out[cle] = val.strip()
    return out


def analyser_offre(offre, modele, log=print):
    parts = decouper(offre)
    resultats = []
    for i, bloc in enumerate(parts, 1):
        log(f"Analyse de l'offre, partie {i}/{len(parts)}…")
        resultats.append(
            ia.llm(
                "Tu analyses un extrait d'offre d'emploi (toute langue). Extrais UNIQUEMENT ce qui est "
                "écrit, dans la langue de l'offre, sans inventer ; laisse vide ou [] ce qui est absent "
                "de cet extrait. Pour 'exigences' : diplôme, années d'expérience, compétences "
                "obligatoires. Pour 'atouts' : ce qui est présenté comme un plus. "
                f"Réponds en JSON strict de la forme : {SCHEMA}\n\nEXTRAIT :\n{bloc}",
                modele,
                True,
            )
        )
    return fusionner(resultats)


def correspondances(analyse, profil, modele):
    """Pour chaque point de l'offre, la preuve trouvée dans le profil (ou niveau 'aucun')."""
    points = (analyse["exigences"] + analyse["missions"] + analyse["atouts"])[:18]
    if not points:
        return []
    rep = ia.llm(
        "Compare chaque point de l'offre avec le PROFIL du candidat. Pour chaque point, cite la preuve "
        "EXACTE du profil (expérience, formation, outil) ou mets niveau 'aucun' si le profil n'en "
        "contient pas. N'invente rien. JSON strict : "
        '{"correspondances":[{"point":"","preuve":"","niveau":"fort|partiel|aucun"}]}\n\n'
        "POINTS DE L'OFFRE :\n- " + "\n- ".join(points) + f"\n\nPROFIL :\n{profil}",
        modele,
        True,
    )
    liste = rep.get("correspondances", []) if isinstance(rep, dict) else []
    return [x for x in liste if isinstance(x, dict)]
