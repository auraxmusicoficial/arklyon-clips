"""Controle diário (ideia do Felipe): uma foto por dia do que foi postado ONTEM e de como está indo, nas 3 redes,
para saber exatamente o que dá certo e o que não dá. Grava estado/CONTROLE.md (o dia de ontem + tendência) e guarda o
histórico em estado/controle_historico.json. Roda 1x por dia no robô do GitHub, depois do relatório e da análise por rede."""
import json, statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

EST = Path(__file__).resolve().parent.parent / "estado"
BRT = timezone(timedelta(hours=-3))


def main():
    hoje = datetime.now(BRT).date()
    ontem = (hoje - timedelta(days=1)).isoformat()
    plano = [p for p in json.loads((EST / "publicacoes.json").read_text()) if isinstance(p, dict)]
    des = {v["id"]: v for v in json.loads((EST / "desempenho.json").read_text()).get("videos", [])}
    des_t = {v["titulo"].lower(): v for v in des.values()}
    rd = json.loads((EST / "redes_dados.json").read_text()) if (EST / "redes_dados.json").exists() else {"linhas": [], "medianas": {}}
    med = rd.get("medianas", {})
    try:   # métricas do TikTok/Instagram direto do Buffer (inclusive posts com menos de 1 dia)
        import os, sys
        sys.path.insert(0, str(Path(__file__).parent))
        import redes
        bp = redes.buffer_posts() if os.environ.get("BUFFER_KEY") else {}
    except Exception as e:
        print("Buffer indisponível:", e); bp = {}
    linhas = []
    for p in plano:
        if not p.get("quando", "").startswith(ontem):
            continue
        y = des.get(p.get("video_id") or p.get("yt_direto") or "") or des_t.get(p.get("yt_title", "").lower())
        b = p.get("buffer") or {}
        r = {rede: int(bp[b[rede]].get("views", 0)) for rede in ("tiktok", "instagram") if rede in b and b[rede] in bp}
        linhas.append({"hora": p["quando"][11:16], "tipo": p.get("tipo"), "titulo": p.get("yt_title", "")[:60],
                       "yt": y["views"] if y else None, "tt": r.get("tiktok"), "ig": r.get("instagram"),
                       "redes": sorted((p.get("buffer") or {}).keys()) + (["youtube(api)"] if p.get("via") == "api" or p.get("yt_direto") else [])})
    def nota(l):
        s = [l[k] / med[n] for k, n in (("yt", "youtube"), ("tt", "tiktok"), ("ig", "instagram")) if l.get(k) is not None and med.get(n)]
        return max(s) if s else 0
    linhas.sort(key=lambda l: -nota(l))
    tot = {k: sum(l[k] or 0 for l in linhas) for k in ("yt", "tt", "ig")}
    hist_f = EST / "controle_historico.json"
    hist = json.loads(hist_f.read_text()) if hist_f.exists() else []
    hist = [h for h in hist if h["dia"] != ontem] + [{"dia": ontem, "posts": len(linhas), **tot}]
    hist = sorted(hist, key=lambda h: h["dia"])[-60:]
    hist_f.write_text(json.dumps(hist, indent=1))
    fmt = lambda x: "—" if x is None else str(x)
    tab = "| Hora | Tipo | Título | YouTube | TikTok | Instagram | vs. média |\n|---|---|---|---|---|---|---|\n" + "\n".join(
        f"| {l['hora']} | {l['tipo']} | {l['titulo']} | {fmt(l['yt'])} | {fmt(l['tt'])} | {fmt(l['ig'])} | {nota(l):.1f}x |" for l in linhas)
    tend = "\n".join(f"| {h['dia'][8:]}/{h['dia'][5:7]} | {h['posts']} | {h['yt']} | {h['tt']} | {h['ig']} |" for h in hist[-10:])
    melhor = linhas[0]["titulo"] if linhas else "—"
    pior = linhas[-1]["titulo"] if len(linhas) > 1 else "—"
    (EST / "CONTROLE.md").write_text(
        f"# Controle diário — posts de {ontem[8:]}/{ontem[5:7]}\n\n(atualizado {datetime.now(BRT):%d/%m %H:%M}; números de ~1 dia — o robô atualiza 2x por dia)\n\n"
        f"- Posts de ontem: **{len(linhas)}** · views somadas: YouTube **{tot['yt']}** · TikTok **{tot['tt']}** · Instagram **{tot['ig']}**\n"
        f"- Melhor de ontem: **{melhor}** · Pior: {pior}\n- \"vs. média\" = quantas vezes a mediana da rede onde foi melhor (1.0x = normal)\n\n"
        f"## Posts de ontem\n{tab}\n\n## Tendência (views somadas dos posts de cada dia)\n| Dia | Posts | YouTube | TikTok | Instagram |\n|---|---|---|---|---|\n{tend}\n",
        encoding="utf-8")
    print(f"CONTROLE.md: {len(linhas)} posts de {ontem}")


if __name__ == "__main__":
    main()
