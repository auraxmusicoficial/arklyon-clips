"""Estudo diário (grátis, sem gastar o Claude).
Parte 1 — ESTUDO: o Gemini assiste vídeos sobre crescer/viralizar/monetizar no YouTube e anota as técnicas.
Parte 2 — NICHO: pega os vídeos de GTA 6 que mais cresceram nas últimas ~48 h e o Gemini assiste por dentro
          (gancho, ritmo, formato, texto na tela, narração, CTA...).
Depois o Groq julga tudo (o que é seguro e como aplicar no nosso canal; o que é arriscado vai para "NÃO USAR")
e grava estado/ESTUDO.md, que a produção das 4h47 lê. Manda um resumo curto no ntfy.
Precisa de: GEMINI_KEY, GROQ_KEY, YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN, NTFY_TOPIC (opcional)."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
RAIZ = Path(__file__).resolve().parent.parent
EST = RAIZ / "estado"
BRT = timezone(timedelta(hours=-3))
MODELOS_GEMINI = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3-flash-preview"]
LIMITE_SEG_DIA = 7 * 3600          # o grátis aceita ~8 h de vídeo do YouTube por dia; deixamos folga
N_NICHO, N_ESTUDO = int(os.environ.get("N_NICHO", 15)), int(os.environ.get("N_ESTUDO", 5))
BUSCAS_ESTUDO = [
    "how to go viral on youtube shorts 2026", "youtube algorithm explained 2026", "how to get 4000 watch hours fast",
    "youtube monetization tips small channel", "how to make better youtube thumbnails", "youtube retention tips hook",
    "how to grow a gaming youtube channel", "youtube shorts strategy that works", "faceless youtube channel growth",
    "youtube title tips more views", "live stream growth youtube tips", "youtube analytics what matters",
]
TEMA_ESTUDO = re.compile(r"youtube|views|subscriber|algorithm|shorts|thumbnail|monetiz|watch ?hours|grow|viral|retention|channel|title|live ?stream", re.I)
REGRAS = """Regras fixas do canal (nunca violar): nada de comprar views/inscritos, sub4sub, contas falsas, engajamento falso,
clickbait mentiroso, reaproveitar vídeo dos outros sem transformação, conteúdo repetitivo em loop, burlar Content ID,
automação não oficial no TikTok. Títulos chamativos sim, mas verdadeiros. Canal em inglês, nicho GTA 6, totalmente automático."""


def gemini(partes, max_saida=1800):
    k = os.environ["GEMINI_KEY"]
    corpo = {"contents": [{"parts": partes}],
             "generationConfig": {"maxOutputTokens": max_saida, "mediaResolution": "MEDIA_RESOLUTION_LOW"}}
    ultimo = None
    for m in MODELOS_GEMINI:
        for tent in range(2):
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}",
                                         json.dumps(corpo).encode(), {"Content-Type": "application/json"})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=300))
                txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"].get("parts", [])).strip()
                if txt:
                    return txt
                ultimo = "vazio"
            except urllib.error.HTTPError as e:
                ultimo = f"{m}: HTTP {e.code} {e.read()[:200]!r}"
                if e.code == 429 and tent == 0:
                    time.sleep(40); continue
                if e.code == 429:
                    raise RuntimeError("LIMITE_GEMINI " + ultimo)
            except Exception as e:
                ultimo = f"{m}: {e}"
            break
    raise RuntimeError("Gemini falhou: " + str(ultimo))


def segundos(iso):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def buscar(tok, api, q, depois, n=25, extra="", ordem="viewCount"):
    p = urllib.parse.urlencode({"part": "snippet", "q": q, "type": "video", "order": ordem, "maxResults": n,
                                "publishedAfter": depois, "relevanceLanguage": "en"})
    ids = [i["id"]["videoId"] for i in api(tok, "GET", f"search?{p}{extra}").get("items", [])]
    if not ids:
        return []
    vs = api(tok, "GET", "videos?part=snippet,statistics,contentDetails&id=" + ",".join(ids)).get("items", [])
    agora = datetime.now(timezone.utc); out = []
    for v in vs:
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        horas = max((agora - pub).total_seconds() / 3600, 1)
        views = int(v["statistics"].get("viewCount", 0))
        out.append({"id": v["id"], "titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"],
                    "canal_id": v["snippet"]["channelId"], "views": views, "views_hora": round(views / horas),
                    "seg": segundos(v["contentDetails"]["duration"]), "horas": round(horas)})
    return out


PED_NICHO = """Responda em português do Brasil, direto, em tópicos curtos. Este é um vídeo de GTA 6 que está crescendo muito.
Título: {titulo} | Canal: {canal} ({inscritos} inscritos) | {views} views ({views_hora}/hora) | duração {seg}s.
Assista e anote: 1) gancho dos primeiros 3 segundos (o que aparece/é dito); 2) assunto e ângulo; 3) formato (vertical/horizontal,
gameplay/trailer/notícia/lista/reação, tem rosto?); 4) ritmo de cortes; 5) texto na tela e legendas; 6) narração (voz, tom, velocidade);
7) música/efeitos; 8) como pede like/inscrição; 9) loops de curiosidade (o que promete no começo e só entrega no fim);
10) quanto é análise/opinião própria vs só mostrar imagem; 11) por que você acha que viralizou num canal desse tamanho; 12) uma ideia que um canal automático de cortes
de GTA 6 pode copiar no FORMATO (sem copiar o conteúdo)."""

PED_ESTUDO = """Responda em português do Brasil, direto, em tópicos curtos. Assista este vídeo sobre crescer no YouTube.
Título: {titulo} | Canal: {canal}.
Liste TODAS as técnicas concretas ensinadas (passo a passo, números, exemplos). Para cada uma diga se é segura dentro das
regras do YouTube ou arriscada (e por quê). Não invente o que não está no vídeo."""


def main():
    s = json.loads(os.environ.get("VAULT_SECRETS", "{}"))
    for k, v in s.items():
        os.environ.setdefault(k, v)
    from youtube_ajustes import token, api
    tok = token()
    meu = api(tok, "GET", "channels?part=id&mine=true")["items"][0]["id"]
    vistos_f = EST / "estudados.json"
    vistos = json.loads(vistos_f.read_text()) if vistos_f.exists() else []
    agora = datetime.now(timezone.utc)

    # escolher vídeos do nicho (longos e Shorts, últimas ~48 h, por views/hora)
    depois = (agora - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cand = buscar(tok, api, "GTA 6", depois) + buscar(tok, api, "GTA 6", depois, extra="&videoDuration=short")
    for q in ("GTA 6 tips", "GTA 6 secrets", "GTA 6 news"):   # mais variedade de canais médios
        cand += buscar(tok, api, q, depois)
    unicos = {c["id"]: c for c in cand if c["canal_id"] != meu and 0 < c["seg"] <= 1800
              and re.search(r"gta\s*(6|vi)\b", c["titulo"], re.I)}
    # tamanho dos canais: o que importa é o que funciona para canais MÉDIOS/PEQUENOS (gigantes não servem de modelo)
    ids_canal = list({c["canal_id"] for c in unicos.values()})
    inscritos = {}
    for i in range(0, len(ids_canal), 50):
        for ch in api(tok, "GET", "channels?part=statistics&id=" + ",".join(ids_canal[i:i + 50])).get("items", []):
            inscritos[ch["id"]] = int(ch["statistics"].get("subscriberCount", 0) or 0)
    for c in unicos.values():
        c["inscritos"] = inscritos.get(c["canal_id"], 0)
        c["forca"] = round(c["views"] / max(c["inscritos"], 1000), 2)   # views ÷ inscritos: vídeo que furou a bolha do canal
    medios = [c for c in unicos.values() if 1000 <= c["inscritos"] <= 500_000]
    nicho = sorted(medios, key=lambda c: (-c["forca"], -c["views_hora"]))[:N_NICHO]
    if len(nicho) < N_NICHO:   # completa com o resto se faltar
        resto = [c for c in sorted(unicos.values(), key=lambda c: -c["views_hora"]) if c not in nicho]
        nicho += resto[:N_NICHO - len(nicho)]

    # escolher vídeos de estudo (populares nos últimos 120 dias, ainda não vistos)
    dia = int(agora.strftime("%j"))
    qs = [BUSCAS_ESTUDO[(dia + i) % len(BUSCAS_ESTUDO)] for i in range(3)]
    dep_e = (agora - timedelta(days=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
    est_c = []
    for q in qs:
        est_c += [c for c in buscar(tok, api, q, dep_e, n=15, ordem="relevance") if c["id"] not in vistos
                  and 120 < c["seg"] < 2400 and TEMA_ESTUDO.search(c["titulo"])]
    estudo, ja = [], set()
    for c in sorted(est_c, key=lambda c: -c["views"]):
        if c["id"] not in ja and len(estudo) < N_ESTUDO:
            estudo.append(c); ja.add(c["id"])

    usado = 0; notas_nicho, notas_estudo = [], []
    for lista, pedido, destino in ((nicho, PED_NICHO, notas_nicho), (estudo, PED_ESTUDO, notas_estudo)):
        for c in lista:
            if usado + c["seg"] > LIMITE_SEG_DIA:
                print("limite diário de vídeo atingido"); break
            try:
                txt = gemini([{"file_data": {"file_uri": f"https://www.youtube.com/watch?v={c['id']}"}},
                              {"text": pedido.format(**c)}])
                usado += c["seg"]; destino.append((c, txt)); vistos.append(c["id"])
                print("assistido:", c["titulo"][:70])
            except RuntimeError as e:
                print("pulei:", c["titulo"][:60], "—", str(e)[:150])
                if "LIMITE_GEMINI" in str(e):
                    break
    vistos_f.write_text(json.dumps(vistos[-400:]))
    if not (notas_nicho or notas_estudo):
        raise RuntimeError("nenhum vídeo foi assistido hoje")

    # o Groq julga e transforma em ações para o nosso canal
    from ia import gerar
    aprend = (EST / "APRENDIZADOS.md").read_text()[:3000] if (EST / "APRENDIZADOS.md").exists() else ""
    bloco = lambda ns: "\n\n".join(f"### {c['titulo']} — {c['canal']} ({c.get('inscritos', '?')} inscritos, {c['views']} views, {c['views_hora']}/h, {c['seg']}s)\n{t[:2500]}" for c, t in ns)
    sintese = gerar(
        f"{REGRAS}\n\nO QUE JÁ SABEMOS DO NOSSO CANAL:\n{aprend}\n\nVÍDEOS DO NICHO QUE MAIS CRESCERAM (análise de quem assistiu):\n{bloco(notas_nicho)}"
        f"\n\nVÍDEOS DE ESTUDO SOBRE CRESCER NO YOUTUBE:\n{bloco(notas_estudo)}\n\n"
        "Escreva em português, em Markdown, curto e prático, com estas seções:\n"
        "## O que está bombando no nicho hoje (assuntos, formatos, ganchos, duração — com exemplos reais acima)\n"
        "## Aplicar AMANHÃ na produção (5 a 8 ações concretas: títulos, ganchos, duração, thumb, ritmo, horário)\n"
        "## Técnicas aprovadas do estudo (seguras, e como encaixar no nosso robô)\n"
        "## NÃO USAR (arriscado ou contra as regras — diga por quê)\n"
        "## 3 descobertas principais (uma linha cada)\n\n"
        "IMPORTANTE: use SÓ o que está nas anotações acima. NÃO invente números, porcentagens, horários 'testados', "
        "resultados ou exemplos. Quando for uma ideia sua, escreva '(hipótese para testar)'. Não sugira títulos que prometam "
        "dinheiro real, hacks ou trapaças. Nossos próprios dados (APRENDIZADOS) valem mais que o que funciona para outros canais.",
        sistema="Você é o estrategista de um canal automático de GTA 6 em inglês. Seja honesto e prático. Nunca recomende nada contra as regras.",
        max_tokens=3000)
    hoje = datetime.now(BRT).strftime("%d/%m/%Y")
    cab = (f"# Estudo do dia — {hoje}\n\nGerado pelo robô (Gemini assistiu {len(notas_nicho)} vídeos do nicho e "
           f"{len(notas_estudo)} de estudo, ~{usado // 60} min de vídeo; Groq julgou). A produção deve ler isto junto com APRENDIZADOS.md.\n\n")
    fontes = "\n\n---\n### Vídeos analisados\n" + "\n".join(
        f"- [{c['titulo']}](https://youtu.be/{c['id']}) — {c['canal']} · {c['views_hora']}/h" for c, _ in notas_nicho + notas_estudo)
    (EST / "ESTUDO.md").write_text(cab + sintese + fontes)

    m = re.search(r"##\s*3 descobertas principais(.*)", sintese, re.S | re.I)
    resumo = (m.group(1).strip() if m else sintese[:500])[:900]
    topico = os.environ.get("NTFY_TOPIC")
    if topico:
        try:
            urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + topico, f"📚 Estudo do dia:\n{resumo}".encode(),
                                                         {"Title": "HQ Vault Clips — estudo"}), timeout=20)
        except Exception as e:
            print("ntfy falhou:", e)
    print(cab + sintese)


if __name__ == "__main__":
    main()
