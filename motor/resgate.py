"""Resgate de vídeos que flopam (dica do Alan Schencke: o YouTube continua testando o vídeo; embalagem nova = sinais novos).
Roda 1x por dia depois do relatório:
1) vídeos com 2–7 dias e views/dia bem abaixo da mediana do mesmo tipo → o Groq escreve um título novo (1 troca por vídeo);
2) se o tema do flop está nos "Temas quentes" do ESTUDO.md → pede um REMAKE para a produção (estado/remakes.json).
Registra tudo em estado/resgates.json; o relatório compara antes/depois."""
import json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

EST = Path(__file__).resolve().parent.parent / "estado"
BRT = timezone(timedelta(hours=-3))
LIMIAR = 0.35          # abaixo de 35% da mediana do tipo = flop
MAX_POR_DIA = 3

REGRAS = """Rules for the new title: English, max 70 characters, keyword "GTA 6" early, curiosity/benefit hook, TRUE (never promise
what the video doesn't show), no clickbait lies, max 1 emoji at the end, can start with 2–3 hook words in CAPS. It must feel
clearly different from the old title (new angle), not a synonym swap."""


def mediana(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def main():
    from youtube_ajustes import token, api
    from ia import gerar
    d = json.loads((EST / "desempenho.json").read_text())
    vids = d.get("videos", [])
    reg_f = EST / "resgates.json"
    reg = json.loads(reg_f.read_text()) if reg_f.exists() else {}
    # atualiza o "depois" dos resgates antigos
    por_id = {v["id"]: v for v in vids}
    for vid, r in reg.items():
        if vid in por_id:
            r["views_dia_agora"] = por_id[vid]["views_dia"]
    feitos = 0
    for tipo in ("longo", "short"):
        grupo = [v for v in vids if v.get("tipo") == tipo]
        med = mediana([v["views_dia"] for v in grupo])
        if med <= 0:
            continue
        flops = sorted([v for v in grupo if 2 <= v.get("dias", 0) <= 7 and v["views_dia"] < LIMIAR * med and v["id"] not in reg],
                       key=lambda v: v["views_dia"])
        for v in flops:
            if feitos >= MAX_POR_DIA:
                break
            bons = [x["titulo"] for x in sorted(grupo, key=lambda x: -x["views_dia"])[:5]]
            try:
                novo = json.loads(gerar(
                    f"{REGRAS}\n\nOur best-performing titles (copy the STYLE, not the topic): {json.dumps(bons)}\n"
                    f"Old title of a {tipo} that flopped ({v['views']} views in {v['dias']} days): {v['titulo']!r}\n"
                    'Reply ONLY JSON: {"title": "..."}', json_saida=True, max_tokens=300))["title"].strip()[:100]
            except Exception as e:
                print("título novo falhou:", e); continue
            sn = api(token(), "GET", f"videos?part=snippet&id={v['id']}").get("items", [{}])[0].get("snippet")
            if not sn or not novo or novo.lower() == sn["title"].lower():
                continue
            corpo = {"id": v["id"], "snippet": {"title": novo, "description": sn["description"], "tags": sn.get("tags", []),
                                                "categoryId": sn["categoryId"], "defaultLanguage": "en", "defaultAudioLanguage": "en"}}
            res = api(token(), "PUT", "videos?part=snippet", corpo)
            if "error" in res:
                print("troca recusada:", str(res)[:200]); continue
            reg[v["id"]] = {"tipo": tipo, "quando": datetime.now(BRT).isoformat(), "titulo_antigo": v["titulo"], "titulo_novo": novo,
                            "views_dia_antes": v["views_dia"], "mediana_tipo": med}
            feitos += 1
            print(f"resgate ({tipo}): {v['titulo']!r} → {novo!r}")
    # remakes: flop cujo tema está nos Temas quentes
    try:
        estudo = (EST / "ESTUDO.md").read_text()
        m = re.search(r"## Temas quentes.*?(?=\n## |\n---|\Z)", estudo, re.S)
        quentes = m.group(0).lower() if m else ""
        palav = lambda t: {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in {"that", "this", "with", "your", "what", "gta6"}}
        rem_f = EST / "remakes.json"
        rem = json.loads(rem_f.read_text()) if rem_f.exists() else []
        ja = {r["id"] for r in rem}
        for vid, r in reg.items():
            comuns = palav(r["titulo_antigo"]) & palav(quentes)
            if vid not in ja and len(comuns) >= 2:
                rem.append({"id": vid, "titulo": r["titulo_antigo"], "tema": sorted(comuns), "pedido": datetime.now(BRT).date().isoformat(),
                            "feito": False})
                print("remake pedido:", r["titulo_antigo"])
        rem_f.write_text(json.dumps(rem[-30:], ensure_ascii=False, indent=1))
    except Exception as e:
        print("remakes falharam:", e)
    reg_f.write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    return feitos


if __name__ == "__main__":
    main()
