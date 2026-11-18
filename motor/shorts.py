"""Gera os Shorts/Reels/TikToks verticais (>60 s) com capa no primeiro frame.
Uso: python3 motor/shorts.py JOB_DIR   -> JOB_DIR/saida/short_<id>.mp4 e thumb_<id>.jpg"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import (CIANO, FONTES, LEAD, ROSA, TAIL, cab, dur, legendas, ler_json, render_segmento, run, t, takes)
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
        render_segmento(src, partes[0], takes(s["broll"], d0), d0, None, job / "voz" / f"{sid}.wav", LEAD)
        L = legendas(info["palavras"], LEAD, n=3, estilo="Cap", dest=ROSA, pos=(540, 1430))
        total = d0
        if s.get("quote"):
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
        L.append(rf"Dialogue: 2,{t(0)},{t(conteudo)},Tit,,0,0,0,,{{\pos(540,400)}}{s['titulo_tela']}")
        L.append(rf"Dialogue: 2,{t(conteudo-2.6)},{t(conteudo)},End,,0,0,0,,{{\pos(540,1690)\fad(250,0)}}FULL BREAKDOWN ON THE CHANNEL")
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
        fc += ("[vc]split[x][y];[x]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:3,"
               "eq=brightness=-0.12[bg];[y]scale=1300:-2,crop=1080:731[fg];[bg][fg]overlay=0:(H-h)/2-40,setsar=1,fps=30[vb];"
               "[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[cap];[vb]format=yuv420p[vb2];"
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
        print("ok short", sid, round(total, 1), "s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or None)
