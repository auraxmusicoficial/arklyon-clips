"""Análises do YouTube (YouTube Analytics API) -> estado/YT_ANALYTICS.md e estado/yt_analytics.json.
Mostra de onde vêm as views, retenção (% assistido) de cada vídeo e países. Os dados do YouTube chegam com ~2 dias de atraso.
Usa YT_REFRESH_TOKEN2 (token com a permissão yt-analytics.readonly) ou, se não houver, YT_REFRESH_TOKEN."""
import json, os, sys, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

EST = RAIZ / "estado"


def token():
    rt = os.environ.get("YT_REFRESH_TOKEN2") or os.environ["YT_REFRESH_TOKEN"]
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": rt, "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d))["access_token"]


def relatorio(tok, ini, fim, **q):
    u = "https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(
        {"ids": "channel==MINE", "startDate": ini, "endDate": fim, **q})
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer " + tok})))
    cols = [h["name"] for h in r["columnHeaders"]]
    return [dict(zip(cols, row)) for row in r.get("rows", [])]


def titulos(tok, ids):
    out = {}
    for i in range(0, len(ids), 50):
        u = "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=" + ",".join(ids[i:i + 50])
        for v in json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer " + tok})))["items"]:
            out[v["id"]] = (v["snippet"]["title"], v["snippet"]["publishedAt"][:10])
    return out


def main():
    tok = token()
    fim = date.today().isoformat(); ini = (date.today() - timedelta(days=28)).isoformat()
    try:
        fontes = relatorio(tok, ini, fim, metrics="views,estimatedMinutesWatched", dimensions="insightTrafficSourceType", sort="-views")
    except urllib.error.HTTPError as e:
        print("AVISO YouTube Analytics indisponível (token sem permissão?):", e.code); return []
    dias = relatorio(tok, ini, fim, metrics="views,averageViewPercentage,subscribersGained", dimensions="day")
    paises = relatorio(tok, ini, fim, metrics="views", dimensions="country", sort="-views", maxResults="8")
    tipos = relatorio(tok, ini, fim, metrics="views,averageViewPercentage,averageViewDuration", dimensions="creatorContentType")
    vids = relatorio(tok, ini, fim, metrics="views,averageViewDuration,averageViewPercentage,subscribersGained",
                     dimensions="video", sort="-views", maxResults="60")
    nomes = titulos(tok, [v["video"] for v in vids])
    L = [f"# YouTube Analytics (últimos 28 dias, dados até ~2 dias atrás) — gerado {fim}", "",
         "Retenção = % médio do vídeo que as pessoas assistem. Short bom: 60%+ (abaixo de 45% o YouTube para de mostrar). "
         "Longo bom: 35%+.", "", "## De onde vêm as views"]
    L += [f"- {f['insightTrafficSourceType']}: {f['views']} views" for f in fontes]
    L += ["", "## Por tipo"] + [f"- {t['creatorContentType']}: {t['views']} views, retenção {t['averageViewPercentage']:.0f}%, "
                                f"{t['averageViewDuration']:.0f}s em média" for t in tipos]
    L += ["", "## Países"] + [f"- {p['country']}: {p['views']}" for p in paises]
    L += ["", "## Por dia"] + [f"- {d['day']}: {d['views']} views, retenção {d['averageViewPercentage']:.0f}%, +{d['subscribersGained']} inscritos"
                               for d in dias[-10:]]
    L += ["", "## Vídeos (mais vistos primeiro)", "| publicado | views | retenção | assistido | +insc | título |", "|---|---|---|---|---|---|"]
    for v in vids:
        t, pub = nomes.get(v["video"], ("?", "?"))
        L.append(f"| {pub} | {v['views']} | {v['averageViewPercentage']:.0f}% | {v['averageViewDuration']:.0f}s | {v['subscribersGained']} | {t[:60]} |")
    (EST / "YT_ANALYTICS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (EST / "yt_analytics.json").write_text(json.dumps({"gerado": fim, "fontes": fontes, "tipos": tipos, "dias": dias,
                                                       "videos": vids}, ensure_ascii=False, indent=1))
    print("ok YT_ANALYTICS.md", len(vids), "vídeos")
    return []


if __name__ == "__main__":
    main()
