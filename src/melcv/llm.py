"""Client minimal pour Ollama (modèles d'IA exécutés localement)."""

import json
import re
import urllib.request

from . import config


class ErreurLLM(RuntimeError):
    pass


def llm(prompt, modele, json_mode=False):
    """Interroge le modèle. En mode JSON, retourne un dict (vide si la réponse est inexploitable)."""
    corps = {
        "model": modele,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": config.CFG["ctx"], "temperature": 0.3},
    }
    if json_mode:
        corps["format"] = "json"
    req = urllib.request.Request(
        config.CFG["ollama"].rstrip("/") + "/api/generate",
        json.dumps(corps).encode(),
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            reponse = json.loads(r.read())["response"].strip()
    except Exception as e:
        raise ErreurLLM(f"Ollama ne répond pas ou le modèle est absent. Lance : ollama pull {modele} ({e})") from e
    if not json_mode:
        return reponse
    try:
        return json.loads(reponse)
    except ValueError:
        m = re.search(r"\{.*\}", reponse, re.S)
        try:
            return json.loads(m.group(0)) if m else {}
        except ValueError:
            return {}


def modeles_installes():
    """Liste des modèles Ollama installés, ou None si Ollama est injoignable."""
    try:
        with urllib.request.urlopen(config.CFG["ollama"].rstrip("/") + "/api/tags", timeout=4) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return None
