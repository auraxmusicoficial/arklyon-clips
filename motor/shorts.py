"""Gera os Shorts/Reels/TikToks verticais (>60 s) com capa no fim; com "rapido_youtube": true gera também short_<id>_yt.mp4 (20–40 s) só pro YouTube.
Uso: python3 motor/shorts.py JOB_DIR   -> JOB_DIR/saida/short_<id>.mp4 e thumb_<id>.jpg"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import (CIANO, FONTES, LEAD, ROSA, SHOT, TAIL, cab, dur, legendas, ler_json, render_segmento, run, t, takes)
from thumb import thumb

CAPA_S = 0.5   # segundos de capa no FIM do vídeo (vira a capa no TikTok/Instagram sem atrasar o gancho)


def main(job, so=None):
    job = Path(job); r = ler_json(job / "roteiro.json")
    T = ler_json(job / "voz" / "tempos.json"); fonte = ler_json(job / "transc.json")["palavras"]
    src = job / "video.mp4"; seg = job / "seg"; seg.mkdir(exist_ok=True); out = job / "saida"; out.mkdir(exist_ok=True)
    for s in r["shorts"]:
        sid = s["id"]
        if so and sid not in so:
            continue
        info = T[sid]; d0 = LEAD + info["dur"] + TAIL
        partes = [seg / f"{sid}_n.mp4"]
        tk = takes(s["broll"], d0)
        try:   # abre o Short com a cena de maior impacto (pico de áudio + movimento) dentro do b-roll
            from impacto import momento_forte
            forte = momento_forte(src, s["broll"], SHOT)
            if forte is not None:
                from impacto import violento
                if violento(src, forte, SHOT):   # violência gráfica nos primeiros 7 s = Short sem anúncio
                    print(f"  {sid}: cena de impacto em {forte:.1f}s tem violência gráfica — não vou abrir com ela")
                    forte = None
            if forte is not None:
                tk = [forte] + [x for x in tk if abs(x - forte) >= SHOT][: len(tk) - 1]
                print(f"  {sid}: abre com a cena de impacto em {forte:.1f}s")
        except Exception as e:
            print("AVISO impacto falhou, seguindo com a ordem normal:", e)
        render_segmento(src, partes[0], tk, d0, None, job / "voz" / f"{sid}.wav", LEAD)
        comp = s.get("comparar")   # Short de COMPARAÇÃO lado a lado: GTA 6 em cima, outro jogo embaixo
        parte2 = None
        if comp:
            try:
                src2 = job / comp.get("fonte", "video2.mp4")
                parte2 = seg / f"{sid}_n2.mp4"
                render_segmento(src2, parte2, takes(comp["broll"], d0), d0, None, None, vol_orig=0.0)
            except Exception as e:
                print("AVISO comparação falhou, Short sai no formato normal:", e); comp = None; parte2 = None
        Y_CAP, Y_TIT, Y_END, Y_POP = (1690, 210, 1835, 945) if comp else (1430, 400, 1690, 1160)
        L = legendas(info["palavras"], LEAD, n=3, estilo="Cap", dest=ROSA, pos=(540, Y_CAP))
        total = d0
        if s.get("quote") and not comp:
            a, b = s["quote"]; a -= 0.3; b += 0.5
            render_segmento(src, seg / f"{sid}_q.mp4", [a], b - a, None, vol_orig=1.0, take=b - a)
            partes.append(seg / f"{sid}_q.mp4")
            ws = [dict(w, s=w["s"] - a, e=w["e"] - a) for w in fonte if a <= w["s"] < b]
            L += legendas(ws, total, n=3, estilo="Quote", dest=CIANO, pos=(540, 1430))
            total += dur(partes[-1])
        conteudo = total
        total += CAPA_S
        if total < 61:
            raise SystemExit(f"Short {sid} tem {total:.1f}s — precisa passar de 60 s. Aumente a narração e rode de novo.")
        L.append(rf"Dialogue: 2,{t(0)},{t(conteudo)},Tit,,0,0,0,,{{\pos(540,{Y_TIT})}}{s['titulo_tela']}")
        L.append(rf"Dialogue: 2,{t(conteudo-2.6)},{t(conteudo)},End,,0,0,0,,{{\pos(540,{Y_END})\fad(250,0)}}FULL BREAKDOWN ON THE CHANNEL")
        if comp:
            r1, r2 = (comp.get("rotulos") or ["GTA 6", "GTA 5"])[:2]
            L.append(rf"Dialogue: 3,{t(0)},{t(conteudo)},Tit,,0,0,0,,{{\an7\pos(36,352)\fs76\c&H00D7FF&}}{r1}")
            L.append(rf"Dialogue: 3,{t(0)},{t(conteudo)},Tit,,0,0,0,,{{\an7\pos(36,980)\fs76\c&HFFFFFF&}}{r2}")
        # números e palavras-chave "pulam" na tela no momento exato da fala (dado chocante prende quem está rolando o feed)
        try:
            import re as _re2
            NUM = {"two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "fifteen", "twenty",
                   "fifty", "hundred", "thousand", "million", "billion", "first", "1st", "#1"}
            UNID = {"billion", "million", "thousand", "hundred", "stars", "star", "hours", "years", "dollars", "percent",
                    "players", "copies", "miles", "minutes", "days", "times", "%"}
            ws = info["palavras"]; limpa = lambda w: _re2.sub(r"[^\w$%.#]", "", w).strip(".")
            alvo = [x.lower() for x in s.get("destaques", [])]
            pops, ult = [], -9.0
            i = 0
            while i < len(ws):
                w0 = limpa(ws[i]["w"]); low = w0.lower(); txt = None
                for frase in alvo:   # destaques escolhidos no roteiro têm prioridade
                    p = frase.split()
                    if [limpa(x["w"]).lower() for x in ws[i:i + len(p)]] == [limpa(x).lower() for x in p]:
                        txt = frase.upper(); break
                depois_gta = i > 0 and limpa(ws[i - 1]["w"]).lower() in {"gta", "gtas"}   # "GTA 6"/"GTA Six" não é dado
                if not txt and not depois_gta and (any(c.isdigit() for c in w0) or low in NUM) and low != "first":
                    txt = w0.upper()
                    if i + 1 < len(ws) and limpa(ws[i + 1]["w"]).lower() in UNID:
                        txt += " " + limpa(ws[i + 1]["w"]).upper()
                if txt and ws[i]["s"] - ult >= 1.3 and len(pops) < 6:
                    a = LEAD + ws[i]["s"]; pops.append((a, txt)); ult = ws[i]["s"]
                i += 1
            for a, txt in pops:
                L.append(rf"Dialogue: 3,{t(a)},{t(a + 1.1)},Tit,,0,0,0,,{{\pos(540,{Y_POP})\fs150\c&H00D7FF&\fscx60\fscy60"
                         rf"\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)\fad(0,180)}}{txt}")
        except Exception as e:
            print("AVISO destaques na tela falharam:", e)
        if s.get("ranking"):   # Short de ranking: selo grande "#5", "#4"... aparece quando a narração chega em cada item
            import re as _re
            nz = lambda w: _re.sub(r"[^a-z0-9]", "", w.lower())
            pw = [nz(w["w"]) for w in info["palavras"]]
            marcas = []
            for it in s["ranking"]:
                alvo = [nz(x) for x in str(it.get("inicio", "")).split()[:3] if nz(x)]
                for i in range(len(pw) - len(alvo) + 1):
                    if alvo and pw[i:i + len(alvo)] == alvo:
                        marcas.append((LEAD + info["palavras"][i]["s"], str(it["n"]))); break
                else:
                    print(f"AVISO ranking {sid}: não achei o item #{it.get('n')} na narração")
            marcas.sort()
            for k, (ini, num) in enumerate(marcas):
                fim = marcas[k + 1][0] if k + 1 < len(marcas) else conteudo - 2.6
                L.append(rf"Dialogue: 3,{t(ini)},{t(max(fim, ini + 0.5))},Tit,,0,0,0,,{{\pos(540,640)\fs190\c&H00A5FF&\fad(120,0)}}#{num}")
        ass = seg / f"{sid}_v.ass"; ass.write_text(cab(1080, 1920, vertical=True) + "\n".join(L) + "\n", encoding="utf-8")
        capa = out / f"thumb_{sid}.jpg"
        th = s["thumb"]
        thumb(src, th["t"], th["linhas"], th.get("selo", ""), capa, vertical=True, x=th.get("x", 0.5),
              foco=th.get("foco"), zoom=th.get("zoom", 1.2), circulo=th.get("circulo", True), seta=th.get("seta", True),
              estilo=th.get("estilo", "gta"), estrelas=th.get("estrelas", 0))
        n = len(partes)
        ent = ["-loop", "1", "-t", f"{CAPA_S}", "-i", str(capa), "-f", "lavfi", "-t", f"{CAPA_S}", "-i",
               "anullsrc=channel_layout=stereo:sample_rate=48000"]
        for p in partes:
            ent += ["-i", str(p)]
        fc = "".join(f"[{i+2}:v][{i+2}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];"
        if parte2:   # tela dividida: GTA 6 em cima (330–938), comparação embaixo (958–1566)
            ent += ["-i", str(parte2)]
            fc += (f"[vc]split[x][y];[x]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:3,"
                   f"eq=brightness=-0.18[bg];[y]scale=1080:608[t1];[{n+2}:v]scale=1080:608,setsar=1[t2];"
                   "[bg][t1]overlay=0:330[b1];[b1][t2]overlay=0:958,setsar=1,fps=30[vb];")
        else:
            fc += ("[vc]split[x][y];[x]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:3,"
                   "eq=brightness=-0.12[bg];[y]scale=1300:-2,crop=1080:731[fg];[bg][fg]overlay=0:(H-h)/2-40,setsar=1,fps=30[vb];")
        fc += ("[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[cap];[vb]format=yuv420p[vb2];"
               f"[vb2]ass='{ass}':fontsdir={FONTES}[vt];"
               "[vt][ac][cap][1:a]concat=n=2:v=1:a=1[v][a]")
        run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out / f"short_{sid}.mp4"])
        try:   # trilha original por baixo + impacto no gancho e "ding" no fim
            from trilha import sonorizar
            import zlib
            final = out / f"short_{sid}.mp4"; tmp = seg / f"{sid}_som.mp4"
            sonorizar(final, tmp, marcas=[0.5], ding=[conteudo - 2.6], estilo=s.get("trilha", "acao"),
                      semente=zlib.crc32(sid.encode()) % 1000, volume_db=-15)
            tmp.replace(final)
        except Exception as e:
            print("AVISO trilha falhou, seguindo sem música:", e)
        if s.get("rapido_youtube"):
            try:
                corte_rapido(out / f"short_{sid}.mp4", out / f"short_{sid}_yt.mp4", info["palavras"], total)
            except Exception as e:
                print("AVISO versão rápida falhou (o YouTube recebe a completa):", e)
        print("ok short", sid, round(total, 1), "s", flush=True)


def corte_rapido(final, saida, palavras, total, minimo=22.0, maximo=40.0):
    """Versão curta pro YouTube (20–40 s): gancho + revelação principal, cortando no fim de uma frase da narração,
    com a capa no fim. Mesmo vídeo, mesma narração — só mais curto."""
    fins = [LEAD + w["e"] for w in palavras if w["w"].rstrip("\"'”’)").endswith((".", "!", "?"))]
    ok = [f for f in fins if minimo <= f <= maximo]
    corte = (ok[-1] if ok else min(maximo, total - CAPA_S)) + 0.35
    fc = (f"[0:v]trim=0:{corte:.2f},setpts=PTS-STARTPTS[v1];[0:a]atrim=0:{corte:.2f},asetpts=PTS-STARTPTS,"
          f"afade=t=out:st={corte - 0.4:.2f}:d=0.4[a1];"
          f"[0:v]trim=start={total - CAPA_S:.2f},setpts=PTS-STARTPTS[v2];[0:a]atrim=start={total - CAPA_S:.2f},"
          "asetpts=PTS-STARTPTS,volume=0[a2];[v1][a1][v2][a2]concat=n=2:v=1:a=1[v][a]")
    run(["ffmpeg", "-y", "-v", "error", "-i", final, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", saida])
    print(f"  versão rápida YouTube: {corte + CAPA_S:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or None)
