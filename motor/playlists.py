"""Playlists automáticas do canal: cria as que faltam e coloca cada vídeo na playlist do tema.
Quem termina um vídeo emenda no próximo da playlist, e o tempo assistido no canal sobe.
Uso como módulo: adicionar(tok, video_id, chave)   (chamado pelo youtube_ajustes.py)
Uso direto:      YT_CLIENT_ID=... python3 motor/playlists.py   (só cria/lista as playlists)"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

EST = RAIZ / "estado" / "playlists.json"
PLAYLISTS = {
    "news": ("GTA 6 News & Updates (Daily)",
             "Every GTA 6 update the day it happens: release, trailers, price, editions, reviews and patches. New video every day."),
    "secrets": ("GTA 6 Secrets, Hidden Details & Easter Eggs",
                "The details nobody noticed in GTA 6 — hidden easter eggs, map secrets and trailer breakdowns."),
    "tips": ("GTA 6 Tips, Guides & Rankings",
             "GTA 6 tips and tricks, beginner guides, best cars, weapons, missions and settings — ranked and explained."),
    "theories": ("GTA 6 Story, Characters & Theories",
                 "Jason and Lucia, the story of Leonida and the biggest GTA 6 fan theories, explained."),
    "cheats": ("GTA 6 Cheats, Safe Codes & Money Guides",
               "Every working GTA 6 cheat code, safe combination and money method — checked against trusted sources."),
    "shorts": ("GTA 6 Shorts — Quick Facts & Moments",
               "Fast GTA 6 facts, secrets and moments in under 2 minutes."),
}


def _ids():
    return json.loads(EST.read_text()) if EST.exists() else {}


def garantir(tok, chave):
    from youtube_ajustes import api
    ids = _ids()
    if chave not in PLAYLISTS:
        chave = "news"
    if chave in ids:
        return ids[chave]
    titulo, desc = PLAYLISTS[chave]
    res = api(tok, "POST", "playlists?part=snippet,status",
              {"snippet": {"title": titulo, "description": desc, "defaultLanguage": "en"}, "status": {"privacyStatus": "public"}})
    if "error" in res:
        print("playlist não criada:", res["error"].get("message")); return None
    ids[chave] = res["id"]; EST.write_text(json.dumps(ids, indent=1))
    print("playlist criada:", titulo)
    return res["id"]


def adicionar(tok, vid, chave):
    from youtube_ajustes import api
    pl = garantir(tok, chave or "news")
    if not pl:
        return False
    res = api(tok, "POST", "playlistItems?part=snippet",
              {"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
    ok = "error" not in res
    print("playlist:", chave, "ok" if ok else res["error"].get("message"))
    return ok


if __name__ == "__main__":
    from youtube_ajustes import token
    t = token()
    for k in PLAYLISTS:
        print(k, garantir(t, k))
