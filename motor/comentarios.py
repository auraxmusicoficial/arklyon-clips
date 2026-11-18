"""Acompanha e responde os comentários do canal no YouTube.
  python3 motor/comentarios.py listar            -> mostra (JSON) comentários novos ainda sem resposta do canal
  python3 motor/comentarios.py responder R.json  -> R.json = [{"id": "<id do comentário>", "texto": "resposta"}]
  python3 motor/comentarios.py auto              -> lista, escreve as respostas com a IA grátis (motor/ia.py) e responde
Usa YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ
from youtube_ajustes import api, token

EST = RAIZ / "estado" / "comentarios.json"


def canal(tok):
    return api(tok, "GET", "channels?part=id&mine=true")["items"][0]["id"]


def listar(imprimir=True):
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
    if imprimir:
        print(json.dumps(novos, ensure_ascii=False, indent=1))
    return novos


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


SISTEMA = """You run "HQ Vault Clips", an English YouTube channel about GTA 6. You reply to viewer comments as the channel owner:
a real person who loves GTA. Rules: reply in the commenter's language (default English); 1-2 short sentences, natural and warm;
react to what they actually said and add one small detail or opinion; when it fits, ask a question back to keep the conversation going;
vary wording, no links, no hashtags, don't beg for subscriptions, never invent facts about the game (if unsure, keep it general).
If they ask something the video answers, don't guess: tell them it's covered in the video (e.g. "I break it down near the end!") and ask what they think.
Criticism: thank them, stay calm and friendly, never argue. Use at most one emoji, only if it fits.
For spam, scams, hate, sexual content or bot-like comments, return an empty reply."""


def auto():
    novos = listar(imprimir=False)[:30]
    if not novos:
        print("sem comentários novos"); return 0
    tok = token()
    ids = ",".join(sorted({n["video"] for n in novos}))
    titulos = {v["id"]: v["snippet"]["title"] for v in api(tok, "GET", f"videos?part=snippet&id={ids}").get("items", [])}
    from ia import gerar
    lista = [{"id": n["id"], "video_title": titulos.get(n["video"], ""), "author": n["autor"], "comment": n["texto"][:600]} for n in novos]
    out = gerar("Write replies for these comments. Return JSON: {\"replies\": [{\"id\": \"...\", \"texto\": \"reply or empty\"}]}\n\n"
                + json.dumps(lista, ensure_ascii=False), sistema=SISTEMA, json_saida=True)
    resp = json.loads(out).get("replies", [])
    validos = {n["id"] for n in novos}
    resp = [r for r in resp if r.get("id") in validos]
    arq = Path("/tmp/respostas_auto.json"); arq.write_text(json.dumps(resp, ensure_ascii=False), encoding="utf-8")
    responder(arq)
    return sum(1 for r in resp if r.get("texto", "").strip())


if __name__ == "__main__":
    {"listar": lambda: listar(), "responder": lambda: responder(sys.argv[2]), "auto": lambda: print("respondidos:", auto())}[sys.argv[1]]()
