"""Agenda no Buffer o vídeo longo (12h) e os Shorts do dia e registra o plano para os ajustes no YouTube.
Uso: BUFFER_KEY=... python3 motor/publicar.py JOB_DIR DATA(YYYY-MM-DD) COMMIT_SHA [--pular 13:00,16:00] [--urgente]
 - Quantos Shorts fazer no dia: python3 motor/publicar.py --slots DATA   (semana de lançamento = 5; normal = 3)
 - --pular: horários de Short que já estão ocupados (os Shorts do roteiro vão para os horários restantes, em ordem).
 - --urgente: Short de notícia — publica o 1º Short do roteiro.json o quanto antes (público em ~10 min) em todas as redes.
Os arquivos precisam já estar no GitHub em publicar/<DATA>/ (links públicos)."""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ, ler_json

REPO = "auraxmusicoficial/arklyon-clips"
CANAIS = {"tiktok": "6afb1f77ece6dfde5fe5b8ef", "youtube": "6afb1f5dece6dfde5fe5b797", "instagram": "6afb1f0fece6dfde5fe5b3b7"}
SLOTS_SHORTS = ["13:00", "16:00", "21:00"]
SLOTS_LANCAMENTO = ["09:00", "11:00", "13:00", "16:00", "18:00", "20:00", "22:00"]   # semana de lançamento do GTA 6: 7 Shorts por dia
IG_LANCAMENTO = {"13:00", "18:00", "22:00"}   # no Instagram só os 3 melhores horários (mais que isso parece spam e derruba o alcance)
LANCAMENTO = ("2026-11-19", "2026-11-25")


def slots_shorts(data):
    return SLOTS_LANCAMENTO if LANCAMENTO[0] <= data <= LANCAMENTO[1] else SLOTS_SHORTS


# O YouTube só aceita ~5 envios por 24 h neste canal (contando o longo do Metricool): 4 Shorts + 1 longo por dia.
YT_LANCAMENTO = {"09:00", "16:00", "18:00", "22:00"}
YT_MAX_24H = 5


def envios_youtube_24h():
    """Quantos vídeos o canal publicou nas últimas 24 h (para não estourar o limite de envios)."""
    try:
        from youtube_ajustes import token, api
        tok = token()
        up = api(tok, "GET", "channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        it = api(tok, "GET", f"playlistItems?part=contentDetails&maxResults=15&playlistId={up}").get("items", [])
        lim = datetime.now(timezone.utc) - timedelta(hours=24)
        return sum(1 for i in it if datetime.fromisoformat(i["contentDetails"].get("videoPublishedAt", "1970-01-01T00:00:00Z").replace("Z", "+00:00")) > lim)
    except Exception as e:
        print("não consegui contar os envios do YouTube:", e); return 0


def vai_youtube(data, hh):
    return hh in YT_LANCAMENTO if LANCAMENTO[0] <= data <= LANCAMENTO[1] else True


def vai_instagram(data, hh):
    return hh in IG_LANCAMENTO if LANCAMENTO[0] <= data <= LANCAMENTO[1] else True
SLOT_LONGO = "12:00"
BRT = timezone(timedelta(hours=-3))
ANTECEDENCIA_YT = timedelta(hours=3)   # sobe no YouTube como não listado 3 h antes; o ajuste (8h52, 11h52, 15h52, 19h52) programa a estreia pública
MUT = """mutation($input: CreatePostInput!) { createPost(input: $input) { __typename
 ... on PostActionSuccess { post { id dueAt status } } ... on InvalidInputError { message } ... on LimitReachedError { message }
 ... on UnexpectedError { message } ... on RestProxyError { message } ... on UnauthorizedError { message } } }"""


def gql(q, v):
    k = os.environ["BUFFER_KEY"]
    r = subprocess.run(["curl", "-sS", "-m", "180", "https://api.buffer.com", "-H", f"Authorization: Bearer {k}",
                        "-H", "Content-Type: application/json", "-d", json.dumps({"query": q, "variables": v})],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def quando(data, hhmm):
    d = datetime.strptime(f"{data} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=BRT)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), d


def antes(dt):
    alvo = max(dt - ANTECEDENCIA_YT, datetime.now(timezone.utc) + timedelta(minutes=5))
    return alvo.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def criar(rede, texto, url, due, meta, capa_ms=None):
    video = {"url": url}
    if capa_ms is not None and rede in ("tiktok", "instagram"):
        video["metadata"] = {"thumbnailOffset": capa_ms}
    inp = {"channelId": CANAIS[rede], "text": texto, "assets": [{"video": video}], "metadata": meta,
           "mode": "customScheduled", "dueAt": due, "schedulingType": "automatic", "needsApproval": False}
    res = gql(MUT, {"input": inp})["data"]["createPost"]
    if res["__typename"] != "PostActionSuccess":
        raise RuntimeError(f"Buffer recusou ({rede}): {res}")
    return res["post"]["id"]


def main(job, data, sha, pular=(), urgente=False):
    job = Path(job); r = ler_json(job / "roteiro.json"); L0 = r.get("longo") or {}
    base = f"https://raw.githubusercontent.com/{REPO}/{sha}/publicar/{data}"
    agora = datetime.now(BRT); plano = []
    if urgente:
        return publicar_urgente(job, r, data, base)
    # vídeo longo (YouTube)
    if L0:
        agendar_longo(job, r, L0, data, base, agora, plano)
    # shorts (YouTube, TikTok, Instagram)
    livres = [h for h in slots_shorts(data) if h not in pular and quando(data, h)[1] > agora]
    for s, hh in zip(r["shorts"], livres):
        due, dt = quando(data, hh)
        plano.append(agendar_short(job, s, base, due, dt, antes(dt), instagram=vai_instagram(data, hh),
                                   youtube=vai_youtube(data, hh)))
        print("agendado short", s["id"], dt)
    for s in r["shorts"][len(livres):]:
        print("SOBROU (sem horário livre hoje):", s["id"])
    salvar(plano)


def agendar_longo(job, r, L0, data, base, agora, plano):
    caps = (job / "saida" / "capitulos.txt").read_text(encoding="utf-8").strip()
    desc = (f"{L0['descricao'].strip()}\n\n⏱️ CHAPTERS\n{caps}\n\n🔔 Subscribe for every GTA 6 detail, theory and breakdown all the way to launch.\n\n"
            f"Footage: {r.get('credito_fonte', 'Rockstar Games')}. Commentary and analysis are original. Narration voice is AI-generated.\n\n"
            f"{' '.join(L0.get('hashtags', ['#GTA6', '#GTAVI', '#GrandTheftAuto6']))}")
    due, dt = quando(data, SLOT_LONGO)
    if dt > agora:
        pid = criar("youtube", desc, f"{base}/longo.mp4", antes(dt),
                    {"youtube": {"title": L0["titulo"][:100], "privacy": "unlisted", "categoryId": "20", "madeForKids": False,
                                 "isAiGenerated": False}})
        plano.append({"tipo": "longo", "quando": dt.isoformat(), "upload": (dt - ANTECEDENCIA_YT).isoformat(), "yt_title": L0["titulo"][:100], "descricao": desc,
                      "tags": L0["tags"], "thumb": f"{base}/thumb_longo.jpg", "buffer": {"youtube": pid}, "ajustado": False,
                      "comentario": L0.get("comentario_youtube", ""), "fb_textos": L0.get("fb_textos", []),
                      "playlist": L0.get("playlist", "news")})
        print("agendado longo", dt)


def agendar_short(job, s, base, due, dt, due_yt, privacidade="unlisted", instagram=True, youtube=True):
    if True:  # noqa
        url = f"{base}/short_{s['id']}.mp4"; ids = {}
        rapido = (job / "saida" / f"short_{s['id']}_yt.mp4").exists()
        url_yt = f"{base}/short_{s['id']}_yt.mp4" if rapido else url
        from comum import dur as _dur
        capa = max(100, int(_dur(job / "saida" / f"short_{s['id']}.mp4") * 1000) - 250)   # capa fica no fim do vídeo
        tx = {r_: s.get(f"texto_{r_}", s.get("texto_post", "")) for r_ in ("youtube", "tiktok", "instagram")}
        if youtube:
            ids["youtube"] = criar("youtube", tx["youtube"], url_yt, due_yt,
                                   {"youtube": {"title": s["yt_title"][:100], "privacy": privacidade, "categoryId": "20", "madeForKids": False,
                                                "isAiGenerated": False}})
        ids["tiktok"] = criar("tiktok", tx["tiktok"], url, due, {"tiktok": {"title": s["tt_title"][:90], "isAiGenerated": False}}, capa_ms=capa)
        ig = {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": False}
        if s.get("primeiro_comentario_instagram"):
            ig["firstComment"] = s["primeiro_comentario_instagram"]
        if instagram:
            try:
                ids["instagram"] = criar("instagram", tx["instagram"], url, due, {"instagram": ig}, capa_ms=capa)
            except RuntimeError as e:
                if "firstComment" not in ig or "First comment" not in str(e):
                    raise
                # plano grátis do Buffer não aceita 1º comentário: põe 5 hashtags no fim da legenda
                ig.pop("firstComment")
                tags5 = " ".join(s["primeiro_comentario_instagram"].split()[:5])
                ids["instagram"] = criar("instagram", tx["instagram"] + "\n\n" + tags5, url, due, {"instagram": ig}, capa_ms=capa)
        return {"tipo": "short", "quando": dt.isoformat(), "upload": (dt - ANTECEDENCIA_YT).isoformat(), "yt_title": s["yt_title"][:100], "descricao": tx["youtube"],
                      "tags": s["tags"], "thumb": f"{base}/thumb_{s['id']}.jpg", "buffer": ids, "ajustado": False if "youtube" in ids else True, "formato_yt": "rapido" if rapido else "completo",
                      "comentario": s.get("comentario_youtube", ""), "fb_textos": s.get("fb_textos", []),
                "playlist": "shorts", "urgente": privacidade == "public"}


def instagram_perto(dt, horas=2):
    """True se já existe post do Instagram agendado/feito a menos de `horas` de dt."""
    est = RAIZ / "estado" / "publicacoes.json"
    if not est.exists():
        return False
    for p in json.loads(est.read_text()):
        if isinstance(p, dict) and "instagram" in (p.get("buffer") or {}):
            try:
                q = datetime.fromisoformat(p["quando"])
            except (KeyError, ValueError):
                continue
            if abs((q - dt).total_seconds()) < horas * 3600:
                return True
    return False


def publicar_urgente(job, r, data, base):
    s = r["shorts"][0]
    dt = datetime.now(timezone.utc) + timedelta(minutes=10)
    due = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    n = envios_youtube_24h()
    yt = n < YT_MAX_24H - 1
    if not yt:
        print(f"YouTube já tem {n} envios nas últimas 24 h — Short urgente vai só pro TikTok/Instagram")
    ig = not instagram_perto(dt)
    if not ig:
        print("Já tem post no Instagram a menos de 2 h desse horário — Short urgente vai só pro YouTube/TikTok (evita 2 posts colados)")
    p = agendar_short(job, s, base, due, dt.astimezone(BRT), due, privacidade="public", youtube=yt, instagram=ig)
    p["upload"] = dt.astimezone(BRT).isoformat()
    salvar([p])
    print("Short urgente publicado agora:", s["id"], "— rode motor/youtube_ajustes.py daqui a ~15 min para capa/tags")


def salvar(plano):
    est = RAIZ / "estado" / "publicacoes.json"
    todos = json.loads(est.read_text()) if est.exists() else []
    est.write_text(json.dumps(todos + plano, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--slots":
        print(len(slots_shorts(a[1])), " ".join(slots_shorts(a[1]))); sys.exit()
    pular = a[a.index("--pular") + 1].split(",") if "--pular" in a else ()
    main(a[0], a[1], a[2], pular=pular, urgente="--urgente" in a)
