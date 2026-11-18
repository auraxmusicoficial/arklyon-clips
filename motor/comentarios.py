"""Acompanha e responde os comentários do canal no YouTube.
  python3 motor/comentarios.py listar            -> mostra (JSON) comentários novos ainda sem resposta do canal
  python3 motor/comentarios.py responder R.json  -> R.json = [{"id": "<id do comentário>", "texto": "resposta"}]
Usa YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ
from youtube_ajustes import api, token

EST = RAIZ / "estado" / "comentarios.json"


def canal(tok):
    return api(tok, "GET", "channels?part=id&mine=true")["items"][0]["id"]


def listar():
    tok = token(); cid = canal(tok)
    feitos = set(json.loads(EST.read_text())) if EST.exists() else set()
    r = api(tok, "GET", f"commentThreads?part=snippet,replies&allThreadsRelatedToChannelId={cid}&maxResults=100&order=time")
    novos = []
    for th in r.get("items", []):
        top = th["snippet"]["topLevelComment"]; sn = top["snippet"]
        if top["id"] in feitos or sn.get("authorChannelId", {}).get("value") == cid:
            continue
        respondeu = any(rp["snippet"].get("authorChannelId", {}).get("value") == cid
                        for rp in th.get("replies", {}).get("comments", []))
        if respondeu:
            continue
        novos.append({"id": top["id"], "video": th["snippet"]["videoId"], "autor": sn["authorDisplayName"],
                      "texto": sn["textOriginal"], "data": sn["publishedAt"]})
    print(json.dumps(novos, ensure_ascii=False, indent=1))


def responder(arq):
    tok = token(); itens = json.loads(Path(arq).read_text(encoding="utf-8"))
    feitos = set(json.loads(EST.read_text())) if EST.exists() else set()
    for it in itens:
        if not it.get("texto", "").strip():  # decidiu não responder (spam, ofensa, etc.)
            feitos.add(it["id"]); continue
        res = api(tok, "POST", "comments?part=snippet", {"snippet": {"parentId": it["id"], "textOriginal": it["texto"][:9000]}})
        ok = "error" not in res
        print(("ok " if ok else "ERRO ") + it["id"], "" if ok else res.get("error", {}).get("message"))
        feitos.add(it["id"])  # marca também os que decidiu ignorar (texto vazio não é enviado)
    EST.write_text(json.dumps(sorted(feitos), indent=0))


if __name__ == "__main__":
    {"listar": lambda: listar(), "responder": lambda: responder(sys.argv[2])}[sys.argv[1]]()
