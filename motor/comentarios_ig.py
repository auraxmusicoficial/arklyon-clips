"""Responde os comentários do Instagram (@hqvaultclips) com a IA grátis, igual ao YouTube.
  python3 motor/comentarios_ig.py listar  -> mostra (JSON) comentários novos sem resposta
  python3 motor/comentarios_ig.py auto    -> escreve as respostas com motor/ia.py e responde
Usa IG_TOKEN (token da Meta, guardado nos Secrets do GitHub)."""
import json, os, sys, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ
from comentarios import SISTEMA

IG_ID = "17841479560326823"   # @hqvaultclips (id público da conta)
G = "https://graph.facebook.com/v23.0/"
EST = RAIZ / "estado" / "comentarios_ig.json"
MAX_POR_RODADA = 20


def api(caminho, dados=None):
    tok = os.environ["IG_TOKEN"]
    if dados is None:
        sep = "&" if "?" in caminho else "?"
        req = urllib.request.Request(G + caminho + sep + "access_token=" + tok)
    else:
        req = urllib.request.Request(G + caminho, data=urllib.parse.urlencode({**dados, "access_token": tok}).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": {"message": f"HTTP {e.code}"}}


def listar(imprimir=True):
    feitos = set(json.loads(EST.read_text())) if EST.exists() else set()
    eu = api(f"{IG_ID}?fields=username").get("username", "hqvaultclips")
    midias = api(f"{IG_ID}/media?fields=id,caption,comments_count&limit=25")
    if "error" in midias:
        raise RuntimeError(midias["error"].get("message"))
    novos = []
    for m in midias.get("data", []):
        if not m.get("comments_count"):
            continue
        cs = api(f"{m['id']}/comments?fields=id,text,username,timestamp,replies{{username}}&limit=50")
        for c in cs.get("data", []):
            if c["id"] in feitos or c.get("username") == eu:
                continue
            if any(r.get("username") == eu for r in c.get("replies", {}).get("data", [])):
                continue
            novos.append({"id": c["id"], "post": (m.get("caption") or "").split("#")[0].strip()[:600],
                          "autor": c.get("username", ""), "texto": c.get("text", ""), "data": c.get("timestamp")})
    if imprimir:
        print(json.dumps(novos, ensure_ascii=False, indent=1))
    return novos


def auto():
    novos = listar(imprimir=False)[:MAX_POR_RODADA]
    if not novos:
        print("sem comentários novos no Instagram"); return 0
    from ia import gerar
    sistema = SISTEMA.replace("English YouTube channel", "English GTA 6 page on Instagram").replace("the video", "the post")
    lista = [{"id": n["id"], "post_caption": n["post"], "author": n["autor"], "comment": n["texto"][:600]} for n in novos]
    out = gerar("Write replies for these Instagram comments. Keep them short (max ~150 characters). "
                "Use ONLY facts written in post_caption. If they ask how/where/when and the caption doesn't say it exactly, "
                "do NOT make anything up: say we'll cover it in a future post or ask what they think. "
                "Return JSON: {\"replies\": [{\"id\": \"...\", \"texto\": \"reply or empty\"}]}\n\n"
                + json.dumps(lista, ensure_ascii=False), sistema=sistema, json_saida=True)
    resp = {r.get("id"): r.get("texto", "") for r in json.loads(out).get("replies", [])}
    feitos = set(json.loads(EST.read_text())) if EST.exists() else set()
    n_ok = 0
    for n in novos:
        txt = (resp.get(n["id"]) or "").strip()
        if txt:
            r = api(f"{n['id']}/replies", {"message": txt[:2000]})
            if "error" in r:
                print("ERRO", n["id"], r["error"].get("message")); continue
            n_ok += 1; print("ok", n["id"])
        feitos.add(n["id"])
    EST.write_text(json.dumps(sorted(feitos), indent=0))
    return n_ok


if __name__ == "__main__":
    {"listar": lambda: listar(), "auto": lambda: print("respondidos:", auto())}[sys.argv[1]]()
