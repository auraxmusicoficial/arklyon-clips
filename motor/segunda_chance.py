"""Segunda chance: Short que BOMBOU numa rede ganha vaga nas redes onde ainda não saiu (ex.: na semana de lançamento só 3 por dia
vão pro Instagram e 4 pro YouTube — os outros nunca foram vistos lá). Roda 1x por dia no robô do GitHub (sem Claude):
- critério: ≥ 1,5x a mediana da rede onde saiu (YouTube, TikTok ou Instagram) e ainda não postado em outra rede;
- Instagram: agenda pelo Buffer no melhor horário livre de amanhã (máx. 1 por dia, 2 h longe de outros posts lá);
- YouTube: sobe direto pela API (máx. 1 por dia, só se o canal ainda tiver folga no limite de envios).
Legenda adaptada à rede pelo Groq. Registra em estado/segunda_chance.json."""
import json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

EST = Path(__file__).resolve().parent.parent / "estado"
BRT = timezone(timedelta(hours=-3))
FATOR = 1.5


def candidatos():
    d = json.loads((EST / "redes_dados.json").read_text())
    med, linhas = d["medianas"], d["linhas"]
    out = []
    for l in linhas:
        forca = max((l[r] / med[r]) for r in ("youtube", "tiktok", "instagram") if r in l and med.get(r))
        if forca >= FATOR:
            faltam = [r for r in ("instagram", "youtube") if r not in l and r not in l.get("redes_postadas", [])]
            if faltam:
                out.append((forca, l, faltam))
    return sorted(out, key=lambda x: -x[0])


def legenda_ig(p):
    from ia import gerar
    try:
        return gerar(f"Write an Instagram Reels caption in English for this GTA 6 video. Hook line first, 1–2 short lines, a question to "
                     f"drive comments, then 5 hashtags (#gta6 first). Max 2 emojis. No links.\nTitle: {p['yt_title']}\n"
                     f"Description: {p.get('descricao', '')[:800]}", max_tokens=300).strip()
    except Exception:
        return f"{p['yt_title']}\n\nWould you try this? 👇\n\n#gta6 #gta #gtavi #gaming #rockstargames"


def main():
    import publicar
    from robo_github import subir_direto
    reg_f = EST / "segunda_chance.json"
    reg = json.loads(reg_f.read_text()) if reg_f.exists() else []
    feitos = {r["quando"] + r["rede"] for r in reg}
    plano = json.loads((EST / "publicacoes.json").read_text())
    por_quando = {p["quando"]: p for p in plano if isinstance(p, dict) and p.get("tipo") == "short"}
    hoje = datetime.now(BRT).date().isoformat()
    agora = datetime.now(BRT)
    msgs = []
    usado = {"instagram": False, "youtube": False}
    # horários já ocupados no Instagram hoje (roda de manhã, depois que a produção do dia agendou tudo)
    ocupados = []
    for p in plano:
        if isinstance(p, dict) and "instagram" in (p.get("buffer") or {}):
            q = datetime.fromisoformat(p["quando"]).astimezone(BRT)
            h = (p.get("quando_redes") or {}).get("instagram")
            if q.date().isoformat() == hoje:
                ocupados.append(int(h[:2]) if h else q.hour)
    for forca, l, faltam in candidatos():
        p = por_quando.get(l["quando"])
        if not p:
            continue
        for rede in faltam:
            if usado[rede] or (l["quando"] + rede) in feitos:
                continue
            try:
                if rede == "instagram":
                    horas = sorted(publicar.melhores_horas("instagram", publicar.CANDIDATOS, 3) or {"13:00", "18:00", "22:00"},
                                   key=lambda h: h)
                    livres = [h for h in publicar.CANDIDATOS if all(abs(int(h[:2]) - o) >= 2 for o in ocupados)
                              and publicar.quando(hoje, h)[1] > agora + timedelta(minutes=40)]
                    h = next((x for x in horas if x in livres), livres[0] if livres else None)
                    if not h:
                        continue
                    due, _ = publicar.quando(hoje, h)
                    m = p["thumb"].rsplit("/", 1)
                    sid = m[1].replace("thumb_", "").replace(".jpg", "")
                    url = f"{m[0]}/short_{sid}.mp4"
                    pid = publicar.criar("instagram", legenda_ig(p), url, due,
                                         {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": False}})
                    p.setdefault("buffer", {})["instagram"] = pid
                    ocupados.append(int(h[:2])); detalhe = f"Instagram hoje às {h}"
                else:
                    if publicar.envios_youtube_24h() >= publicar.YT_MAX_24H - 1:
                        continue
                    vid = subir_direto(p)
                    p["video_id"] = vid; p["ajustado"] = False; detalhe = f"YouTube agora (https://youtu.be/{vid})"
                usado[rede] = True
                reg.append({"quando": l["quando"], "rede": rede, "titulo": l["titulo"], "forca": round(forca, 1),
                            "feito_em": datetime.now(BRT).isoformat(), "detalhe": detalhe})
                print(f"segunda chance: {l['titulo']!r} ({forca:.1f}x a mediana) → {detalhe}")
                msgs.append(f"🔁 Segunda chance: '{l['titulo'][:50]}' bombou ({forca:.1f}x a média) e vai pro {detalhe}")
            except Exception as e:
                print(f"segunda chance falhou ({rede}):", str(e)[:200])
    (EST / "publicacoes.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
    reg_f.write_text(json.dumps(reg[-100:], ensure_ascii=False, indent=1))
    return msgs


if __name__ == "__main__":
    s = json.loads(os.environ.get("VAULT_SECRETS", "{}"))
    for k, v in s.items():
        os.environ.setdefault(k, v)
    main()
