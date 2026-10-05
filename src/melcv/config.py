"""Chemins et réglages. Le dossier de travail est MELCV_HOME, sinon le dossier courant."""

import json
import os
from pathlib import Path

HOME = Path(os.environ.get("MELCV_HOME", Path.cwd()))
DATA = HOME / "data"
MODELES = HOME / "modeles"
REFS = HOME / "references"
SORTIES = HOME / "sorties"
CFG_FILE = DATA / "reglages.json"
PROFIL_FILE = DATA / "profil.txt"

CFG = {
    "modele": "qwen2.5:7b",
    "ollama": os.environ.get("MELCV_OLLAMA", "http://localhost:11434"),
    "ctx": 16384,
    "port": 8765,
}


def initialiser():
    """Crée les dossiers et charge les réglages sauvegardés."""
    for dossier in (DATA, MODELES, REFS, SORTIES):
        dossier.mkdir(parents=True, exist_ok=True)
    if CFG_FILE.exists():
        CFG.update(json.loads(CFG_FILE.read_text(encoding="utf-8")))


def sauver_reglages(modele, ctx):
    CFG["modele"], CFG["ctx"] = modele, int(ctx)
    CFG_FILE.write_text(json.dumps({"modele": CFG["modele"], "ctx": CFG["ctx"]}), encoding="utf-8")
