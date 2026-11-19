"""Relatório de desempenho do canal (YouTube): o que funcionou para fazer mais do que dá certo.
Gera estado/RELATORIO.md (lido pelo robô antes de escolher o tema do dia) e estado/desempenho.json (histórico).
Uso: YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... python3 motor/relatorio.py"""
import json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ
from youtube_ajustes import api, token

BRT = timezone(timedelta(hours=-3))
DES = RAIZ / "estado" / "desempenho.json"
REL = RAIZ / "estado" / "RELATORIO.md"


def segs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def main():
    tok = token()
    ch = api(tok, "GET", "channels?part=statistics,contentDetails&mine=true")["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]; st = ch["statistics"]
    ids, pg = [], ""
    for _ in range(4):
        r = api(tok, "GET", f"playlistItems?part=contentDetails&maxResults=50&playlistId={up}{pg}")
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        if not r.get("nextPageToken"):
            break
        pg = f"&pageToken={r['nextPageToken']}"
    vids = []
    for i in range(0, len(ids), 50):
        vids += api(tok, "GET", "videos?part=snippet,statistics,contentDetails,status&id=" + ",".join(ids[i:i + 50])).get("items", [])
    agora = datetime.now(timezone.utc); lin = []
    for v in vids:
        if v["status"]["privacyStatus"] != "public":
            continue
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        horas = max(1, (agora - pub).total_seconds() / 3600)
        s = v["statistics"]; vw = int(s.get("viewCount", 0)); lk = int(s.get("likeCount", 0)); cm = int(s.get("commentCount", 0))
        d = segs(v["contentDetails"]["duration"])
        lin.append({"id": v["id"], "titulo": v["snippet"]["title"], "tipo": "short" if d <= 180 else "longo", "dur": d,
                    "views": vw, "likes": lk, "coments": cm, "views_dia": round(vw / horas * 24, 1),
                    "engaj": round((lk + cm) / vw * 100, 1) if vw else 0.0,
                    "hora_brt": pub.astimezone(BRT).strftime("%H"), "dias": round(horas / 24, 1)})
    hist = json.loads(DES.read_text()).get("historico", []) if DES.exists() else []
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    hist = [h for h in hist if h["data"] != hoje] + [{"data": hoje, "inscritos": int(st.get("subscriberCount", 0)),
                                                     "views": int(st.get("viewCount", 0)), "videos": int(st.get("videoCount", 0))}]
    DES.write_text(json.dumps({"atualizado": agora.isoformat(), "historico": hist[-60:], "videos": lin}, ensure_ascii=False, indent=1))

    def media(xs, k):
        return round(sum(x[k] for x in xs) / len(xs), 1) if xs else 0
    sh = [x for x in lin if x["tipo"] == "short"]; lg = [x for x in lin if x["tipo"] == "longo"]
    ant = hist[-8] if len(hist) >= 8 else hist[0]
    por_hora = {}
    for x in lin:
        por_hora.setdefault(x["hora_brt"], []).append(x["views_dia"])
    horas = sorted(((h, round(sum(v) / len(v), 1), len(v)) for h, v in por_hora.items()), key=lambda t: -t[1])
    top = sorted(lin, key=lambda x: -x["views_dia"])
    L = [f"# Relatório do canal — {hoje}", "",
         f"- Inscritos: **{hist[-1]['inscritos']}** (desde {ant['data']}: {hist[-1]['inscritos'] - ant['inscritos']:+d})",
         f"- Visualizações totais: **{hist[-1]['views']}** (desde {ant['data']}: {hist[-1]['views'] - ant['views']:+d})",
         f"- Vídeos públicos: {len(lin)} ({len(sh)} Shorts, {len(lg)} longos)",
         f"- Média de views/dia: Shorts **{media(sh, 'views_dia')}** · longos **{media(lg, 'views_dia')}**",
         f"- Engajamento médio (curtidas+comentários / views): Shorts {media(sh, 'engaj')}% · longos {media(lg, 'engaj')}%", "",
         f"- Teste de formato nos Shorts: rápidos (<45 s) **{media([x for x in sh if x['dur'] < 45], 'views_dia')}** views/dia · completos (≥45 s) **{media([x for x in sh if x['dur'] >= 45], 'views_dia')}** views/dia", "",
         "## Melhores vídeos (views por dia)", "| # | Tipo | Título | Views | Views/dia | Engaj. |", "|---|---|---|---|---|---|"]
    L += [f"| {i} | {x['tipo']} | {x['titulo'][:70]} | {x['views']} | {x['views_dia']} | {x['engaj']}% |" for i, x in enumerate(top[:10], 1)]
    L += ["", "## Piores (evite repetir o ângulo/estilo)"] + [f"- {x['titulo'][:80]} — {x['views_dia']} views/dia" for x in top[-5:][::-1] if len(top) > 5]
    L += ["", "## Horário de publicação (BRT) × views/dia"] + [f"- {h}h: {m} views/dia ({n} vídeos)" for h, m, n in horas[:8]]
    L += ["", "## Como usar (robô)",
          "- Antes de escolher o tema: repita o ASSUNTO/formato dos 3 melhores (com ângulo novo) e evite o que está entre os piores.",
          "- Compare títulos e capas dos melhores com os piores e aplique o padrão vencedor.",
          "- Poucos dados (canal novo): trate como pista, não como regra; reavalie toda semana."]
    REL.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main()
