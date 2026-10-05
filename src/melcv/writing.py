"""Rédaction du CV ou de la lettre à partir de l'analyse, du profil et du canevas."""

import json
from datetime import date

from . import llm as ia

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]  # fmt: skip

FORMAT_MD = (
    "FORMAT DE SORTIE (texte simple, rien d'autre) : '# ' pour le nom ou le titre principal ; "
    "'## ' pour un titre de section ; '- ' pour une puce ; **gras** avec deux astérisques ; "
    "une ligne vide entre les blocs ; chaque paragraphe de lettre sur UNE seule ligne ; "
    "aucun commentaire avant ou après le document ; aucun bloc de code."
)


def aujourdhui(langue, jour=None):
    d = jour or date.today()
    if langue == "English":
        return d.strftime("%B %d, %Y").replace(" 0", " ")
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS_FR[d.month - 1]} {d.year}"


def rediger(type_doc, analyse, corr, profil, langue, consignes, modele, canevas, refs):
    """type_doc : 'cv', 'motivation' ou 'presentation'. Retourne le document en texte balisé."""
    synthese = json.dumps({k: v for k, v in analyse.items() if v}, ensure_ascii=False, indent=1)
    preuves = "\n".join(f"- {c.get('point', '')} => [{c.get('niveau', '')}] {c.get('preuve', '')}" for c in corr)
    base = (
        f"LANGUE DU DOCUMENT : {langue} (toutes les phrases dans cette langue, orthographe impeccable).\n"
        "RÈGLES ABSOLUES : n'utilise QUE des faits présents dans le PROFIL ; n'invente aucune "
        "expérience, aucun chiffre, aucun diplôme ; si une information nécessaire manque, écris "
        "[à compléter]. Le texte doit être assez précis pour ne pas pouvoir servir à une autre "
        "entreprise : cite le poste exact, des éléments concrets de l'offre et de l'entreprise. "
        "Évite le ton trop lisse, les formules creuses et les paragraphes de même longueur.\n"
        f"CONSIGNES PRIORITAIRES DE L'UTILISATEUR : {consignes or 'aucune'}\n\n"
        f"### PROFIL\n{profil}\n\n### ANALYSE DE L'OFFRE\n{synthese}\n\n"
        f"### CORRESPONDANCES OFFRE/PROFIL\n{preuves or '(non disponibles)'}\n\n"
    )
    vocab = f"### BANQUE DE VOCABULAIRE (qualités, compétences)\n{refs}\n\n"
    if type_doc == "cv":
        consigne = (
            "Rédige le CV du candidat, ciblé sur cette offre. Titre en tête aligné sur le poste visé, "
            "résumé de 2-3 lignes, compétences clés (reprends les mots-clés de l'offre seulement s'ils "
            "sont vrais pour le candidat), expériences en ordre antichronologique avec des puces qui "
            "commencent par un verbe d'action et montrent des résultats, formation, langues. Garde ce "
            "qui est pertinent, tiens sur 1 à 2 pages. Si le candidat ne répond pas à une exigence, ne "
            "la prétends pas. Coordonnées du candidat sous le nom.\n" + FORMAT_MD
        )
        return ia.llm(base + vocab + consigne, modele)
    nom = "lettre de motivation" if type_doc == "motivation" else "lettre de présentation"
    consigne = (
        f"Rédige une {nom} en suivant EXACTEMENT le canevas ci-dessous : lieu et date "
        f"({aujourdhui(langue)}), bloc du destinataire (infos de l'offre, sinon [à compléter]), ligne "
        "**Objet : Candidature au poste de … (titre exact et référence)**, salutation, quatre "
        "paragraphes (1 but de la lettre ; 2 ce que tu offres en reprenant UNE À UNE les "
        "responsabilités de l'offre avec les preuves du profil, sans parler de ce que le poste "
        "t'apportera ; 3 ce qui te motive et ta connaissance de l'entreprise, qualités utiles ; "
        "4 conclusion avec demande d'entrevue), formule de politesse reprenant les mots de la "
        "salutation, puis nom, téléphone et courriel du candidat. Une page maximum. Pour l'anglais, "
        "adapte les formules (Dear Hiring Manager, Sincerely).\n" + FORMAT_MD
    )
    return ia.llm(base + f"### CANEVAS ET CONSIGNES DE L'ÉCOLE\n{canevas}\n\n" + vocab + consigne, modele)
