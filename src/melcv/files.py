"""Lecture du profil, du canevas, des références et des pages web."""

import re
import urllib.request
from html import unescape
from pathlib import Path

from . import config


def lire_fichier(chemin, limite=6000):
    """Retourne le texte d'un .txt, .md, .docx ou .pdf (vide si illisible)."""
    p = Path(chemin)
    suffixe = p.suffix.lower()
    try:
        if suffixe in (".txt", ".md"):
            texte = p.read_text(encoding="utf-8", errors="ignore")
        elif suffixe == ".docx":
            from docx import Document

            texte = "\n".join(x.text for x in Document(str(p)).paragraphs if x.text.strip())
        elif suffixe == ".pdf":
            from pypdf import PdfReader

            texte = "\n".join(pg.extract_text() or "" for pg in PdfReader(str(p)).pages)
        else:
            return ""
    except Exception:
        return ""
    texte = re.sub(r"\n\s*\n+", "\n", texte)
    return re.sub(r"[ \t]+", " ", texte).strip()[:limite]


def _fichiers(dossier):
    return sorted(f for f in Path(dossier).glob("*") if f.is_file() and not f.name.startswith("."))


def charger_canevas():
    return "\n\n".join(lire_fichier(f, 6000) for f in _fichiers(config.MODELES))


def charger_references():
    return "\n\n".join(f"[{f.stem}]\n{lire_fichier(f, 2200)}" for f in _fichiers(config.REFS))


def lister(dossier):
    return [f.name for f in _fichiers(dossier)]


def lire_profil():
    return config.PROFIL_FILE.read_text(encoding="utf-8") if config.PROFIL_FILE.exists() else ""


def url_vers_texte(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "ignore")
    html = re.sub(r"(?is)<(script|style|nav|footer|header|svg).*?</\1>", " ", html)
    texte = unescape(re.sub(r"<[^>]+>", " ", html))
    return re.sub(r"\s+", " ", texte).strip()[:30000]


def assembler_offre(brut, log=print):
    """Remplace chaque ligne qui est un lien par le contenu de la page ; garde le texte collé."""
    morceaux = []
    for ligne in brut.splitlines():
        m = re.fullmatch(r"\s*(https?://\S+)\s*", ligne)
        if not m:
            morceaux.append(ligne)
            continue
        try:
            log(f"Lecture de la page {m.group(1)[:70]}…")
            morceaux.append(url_vers_texte(m.group(1)))
        except Exception as e:
            log(f"Page illisible ({e}). Colle plutôt le texte.")
    return "\n".join(morceaux).strip()
