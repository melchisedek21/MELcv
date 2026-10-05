"""Serveur web local (127.0.0.1 uniquement) : interface + API JSON."""

import json
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import config, export, files, jobs
from . import llm as ia

PAGE = Path(__file__).parent / "web" / "index.html"
TYPES_MIME = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "txt": "text/plain; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def repondre(self, code, corps, ctype="application/json", extra=None):
        if not isinstance(corps, bytes):
            corps = json.dumps(corps, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corps)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/":
            return self.repondre(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/api/etat":
            return self.repondre(200, {
                "profil": files.lire_profil(),
                "cfg": {"modele": config.CFG["modele"], "ctx": config.CFG["ctx"]},
                "modeles": ia.modeles_installes(),
                "canevas": files.lister(config.MODELES),
                "references": files.lister(config.REFS),
                "pdf_fidele": bool(export._libreoffice()),
            })  # fmt: skip
        if url.path == "/api/tache":
            job = jobs.JOBS.get(urllib.parse.parse_qs(url.query).get("id", [""])[0])
            return self.repondre(200 if job else 404, job or {"erreur": "inconnue"})
        self.repondre(404, {"erreur": "introuvable"})

    def do_POST(self):
        taille = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(taille) or b"{}")
        if self.path == "/api/profil":
            config.PROFIL_FILE.write_text(d.get("profil", ""), encoding="utf-8")
            return self.repondre(200, {"ok": True})
        if self.path == "/api/reglages":
            config.sauver_reglages(d.get("modele", config.CFG["modele"]), d.get("ctx", config.CFG["ctx"]))
            return self.repondre(200, {"ok": True})
        if self.path == "/api/generer":
            return self.repondre(200, {"id": jobs.lancer(d)})
        if self.path == "/api/exporter":
            try:
                p = export.exporter(d["texte"], d["type"], d["format"], d.get("nom", ""))
            except ImportError:
                return self.repondre(500, {"erreur": "Installe les modules : pip install -e ."})
            except (KeyError, ValueError) as e:
                return self.repondre(400, {"erreur": f"Requête invalide : {e}"})
            en_tete = {"Content-Disposition": f'attachment; filename="{urllib.parse.quote(p.name)}"'}
            return self.repondre(200, p.read_bytes(), TYPES_MIME[d["format"]], en_tete)
        self.repondre(404, {"erreur": "introuvable"})


def main():
    config.initialiser()
    serveur = ThreadingHTTPServer(("127.0.0.1", config.CFG["port"]), Handler)
    url = f"http://127.0.0.1:{config.CFG['port']}"
    print(f"MELcv est prêt : {url}   (Ctrl+C pour arrêter)")
    if "--sans-navigateur" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
