"""Análise POR REDE (ideia do Felipe): o mesmo Short pode flopar no YouTube e bombar no TikTok, ou o contrário.
Junta as métricas de cada post — YouTube (estado/desempenho.json) + TikTok e Instagram (métricas que o Buffer coleta) —,
compara rede por rede e grava estado/REDES.md: ranking em cada rede, vídeos que só funcionaram numa rede, melhor horário por
rede e o que o Groq conclui sobre o que cada público prefere. A produção lê isso para escolher o que mandar para cada rede.
Grátis (Buffer + Groq), roda no robô do GitHub junto com o relatório."""
import json, os, statistics, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

EST = Path(__file__).resolve().parent.parent / "estado"
BRT = timezone(timedelta(hours=-3))


def buffer_posts():
    k = os.environ["BUFFER_KEY"]
    def g(q, v=None):
        r = urllib.request.Request("https://api.buffer.com", json.dumps({"query": q, "variables": v or {}}).encode(),
                                   {"Authorization": "Bearer " + k, "Content-Type": "application/json", "User-Agent": "vault"})
        return json.load(urllib.request.urlopen(r, timeout=60))
    org = g("{ account { organizations { id } } }")["data"]["account"]["organizations"][0]["id"]
    q = ("query($o:OrganizationId!,$a:String){ posts(input:{organizationId:$o, filter:{status:[sent]}}, first:100, after:$a)"
         "{ pageInfo{ hasNextPage endCursor } edges{ node{ id channelService sentAt text metrics{ type value } } } } }")
    out, cur = {}, None
    for _ in range(5):
        r = g(q, {"o": org, "a": cur})
        if "errors" in r:
            raise RuntimeError(str(r["errors"])[:300])
        p = r["data"]["posts"]
        for e in p["edges"]:
            n = e["node"]; m = {x["type"]: x["value"] for x in (n.get("metrics") or [])}
            out[n["id"]] = {"rede": n["channelService"], "quando": n["sentAt"], "texto": n["text"], **m}
        if not p["pageInfo"]["hasNextPage"]:
            break
        cur = p["pageInfo"]["endCursor"]
    return out


def main():
    bp = buffer_posts()
    plano = json.loads((EST / "publicacoes.json").read_text())
    des = json.loads((EST / "desempenho.json").read_text()).get("videos", [])
    yt_id = {v["id"]: v for v in des}
    yt_tit = {v["titulo"].lower(): v for v in des}
    resg = json.loads((EST / "resgates.json").read_text()) if (EST / "resgates.json").exists() else {}
    for vid, r in resg.items():   # título trocado no resgate: casa pelo título antigo também
        if vid in yt_id:
            yt_tit[r["titulo_antigo"].lower()] = yt_id[vid]
    agora = datetime.now(timezone.utc)
    linhas = []
    for p in plano:
        if not isinstance(p, dict) or p.get("tipo") != "short":
            continue
        q = datetime.fromisoformat(p["quando"])
        dias = (agora - q).total_seconds() / 86400
        if dias < 1:
            continue   # muito cedo para julgar
        reg = {"titulo": p.get("yt_title", "")[:70], "dias": round(dias, 1), "hora": q.astimezone(BRT).hour}
        y = yt_id.get(p.get("video_id") or p.get("yt_direto") or "") or yt_tit.get(p.get("yt_title", "").lower())
        if y:
            reg["youtube"] = y["views"]
        for rede, pid in (p.get("buffer") or {}).items():
            m = bp.get(pid)
            if m and rede in ("tiktok", "instagram"):
                reg[rede] = int(m.get("views", 0)); reg[f"{rede}_tempo"] = round(m.get("averageTimeWatched", 0), 1)
        if any(k in reg for k in ("youtube", "tiktok", "instagram")):
            linhas.append(reg)
    if not linhas:
        print("sem dados por rede ainda"); return
    redes = ["youtube", "tiktok", "instagram"]
    med = {r: statistics.median([l[r] for l in linhas if r in l] or [0]) for r in redes}
    so_uma = []
    for l in linhas:   # bombou numa rede (≥2x a mediana dela) e flopou nas outras (<0,5x)
        for r in redes:
            outras = [o for o in redes if o != r and o in l]
            if r in l and med[r] and l[r] >= 2 * med[r] and outras and all(med[o] and l[o] < 0.5 * med[o] for o in outras):
                so_uma.append((r, l))
    hora = {}
    for r in redes:
        por_h = {}
        for l in linhas:
            if r in l:
                por_h.setdefault(l["hora"], []).append(l[r])
        if por_h:
            hora[r] = sorted(((h, round(statistics.mean(v))) for h, v in por_h.items()), key=lambda x: -x[1])[:3]
    tabela = "| Short | YouTube | TikTok | Instagram |\n|---|---|---|---|\n" + "\n".join(
        f"| {l['titulo']} | {l.get('youtube', '—')} | {l.get('tiktok', '—')} | {l.get('instagram', '—')} |"
        for l in sorted(linhas, key=lambda l: -max(l.get(r, 0) for r in redes))[:25])
    ranking = ""
    for r in redes:
        com = sorted([l for l in linhas if r in l], key=lambda l: -l[r])
        if com:
            ranking += (f"\n### {r.title()} (mediana {med[r]:.0f} views)\n- Melhores: " + "; ".join(f"{l['titulo']} ({l[r]})" for l in com[:3])
                        + "\n- Piores: " + "; ".join(f"{l['titulo']} ({l[r]})" for l in com[-3:]))
    destaque = "\n".join(f"- **Só no {r.title()}:** {l['titulo']} — YT {l.get('youtube', '—')} · TT {l.get('tiktok', '—')} · IG {l.get('instagram', '—')}"
                         for r, l in so_uma) or "- (nenhum ainda)"
    horas = "\n".join(f"- {r.title()}: " + ", ".join(f"{h}h ({v} views em média)" for h, v in hs) for r, hs in hora.items())
    conclusao = ""
    try:
        from ia import gerar
        conclusao = gerar(
            "Dados de Shorts de um canal de GTA 6 em inglês, publicados iguais no YouTube, TikTok e Instagram (views por rede):\n"
            + json.dumps(linhas, ensure_ascii=False)[:9000]
            + "\n\nEm português, curto e prático (Markdown), responda: ## O que cada rede prefere (assunto, tipo de título/gancho, duração — "
              "só com base nos dados; diga quando há poucos dados) ## O que fazer diferente por rede a partir de amanhã (3–5 ações). "
              "Não invente números.", max_tokens=1500)
    except Exception as e:
        print("conclusão do Groq falhou:", e)
    hoje = datetime.now(BRT).strftime("%d/%m/%Y %H:%M")
    (EST / "REDES.md").write_text(
        f"# Desempenho por rede — {hoje}\n\nShorts com 1+ dia ({len(linhas)}). Views: YouTube (API) e TikTok/Instagram (Buffer).\n\n"
        f"## Bombou numa rede só (conteúdo que combina com aquele público)\n{destaque}\n\n## Melhor horário por rede\n{horas}\n"
        f"{ranking}\n\n{conclusao}\n\n## Tabela\n{tabela}\n", encoding="utf-8")
    print(f"REDES.md: {len(linhas)} Shorts, {len(so_uma)} que bombaram numa rede só")


if __name__ == "__main__":
    s = json.loads(os.environ.get("VAULT_SECRETS", "{}"))
    for k, v in s.items():
        os.environ.setdefault(k, v)
    main()
