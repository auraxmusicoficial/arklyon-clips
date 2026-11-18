"""Monta o vídeo longo 16:9 (capítulos, legendas, cards, citações do original).
Uso: python3 motor/longo.py JOB_DIR   -> JOB_DIR/saida/longo.mp4 + capitulos.txt"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import (CIANO, LEAD, ROSA, TAIL, cab, dur, legendas, ler_json, render_segmento, run, t, takes)


def main(job):
    job = Path(job); r = ler_json(job / "roteiro.json"); L0 = r["longo"]
    T = ler_json(job / "voz" / "tempos.json")
    fonte = ler_json(job / "transc.json")["palavras"]
    src = job / "video.mp4"
    seg = job / "seg"; seg.mkdir(exist_ok=True)
    out = job / "saida"; out.mkdir(exist_ok=True)
    ordem, caps, ncap, tempo = [], [], 0, 0.0
    for i, s in enumerate(L0["secoes"]):
        sid = s["id"]; info = T[sid]
        d = LEAD + info["dur"] + TAIL
        L = legendas(info["palavras"], LEAD)
        if i == 0:
            a, b = L0["abertura"]
            L.append(rf"Dialogue: 1,{t(0)},{t(3.2)},Hook,,0,0,0,,{{\pos(960,430)\fad(150,300)\t(0,3200,\fscx108\fscy108)}}{a}")
            L.append(rf"Dialogue: 1,{t(0)},{t(3.2)},Sub,,0,0,0,,{{\pos(960,570)\fad(150,300)\t(0,3200,\fscx110\fscy110)}}{b}")
            caps.append((tempo, "Intro"))
        elif s.get("cap"):
            ncap += 1
            L.append(rf"Dialogue: 1,{t(0.15)},{t(3.4)},CapNum,,0,0,0,,{{\pos(90,34)\fad(200,250)}}CHAPTER {ncap}")
            L.append(rf"Dialogue: 1,{t(0.25)},{t(3.4)},CapTit,,0,0,0,,{{\move(-600,96,90,96,0,350)\fad(0,250)}} {s['cap'].upper()} ")
            caps.append((tempo, s["cap"].title()))
        if i == len(L0["secoes"]) - 1:
            caps.append((tempo, "Your Turn"))
            L.append(rf"Dialogue: 1,{t(info['dur']*0.45)},{t(d)},Hook,,0,0,0,,{{\pos(960,420)\fad(250,0)}}SUBSCRIBE")
            L.append(rf"Dialogue: 1,{t(info['dur']*0.45+0.3)},{t(d)},Sub,,0,0,0,,{{\pos(960,560)\fad(250,0)}}FOR EVERY GTA 6 DETAIL")
        ass = seg / f"{sid}.ass"; ass.write_text(cab() + "\n".join(L) + "\n", encoding="utf-8")
        render_segmento(src, seg / f"{sid}.mp4", takes(s["broll"], d), d, ass, job / "voz" / f"{sid}.wav", LEAD)
        ordem.append(sid); tempo += d
        print("ok", sid, round(d, 1), flush=True)
        if s.get("quote"):
            a, b = s["quote"]; a -= 0.3; b += 0.5
            ws = [dict(w, s=w["s"] - a, e=w["e"] - a) for w in fonte if a <= w["s"] < b]
            assq = seg / f"{sid}_q.ass"
            assq.write_text(cab() + "\n".join(legendas(ws, 0, n=5, estilo="Quote", dest=CIANO)) + "\n", encoding="utf-8")
            render_segmento(src, seg / f"{sid}_q.mp4", [a], b - a, assq, vol_orig=1.0, take=b - a)
            ordem.append(sid + "_q"); tempo += dur(seg / f"{sid}_q.mp4")
    (seg / "lista.txt").write_text("".join(f"file '{seg}/{o}.mp4'\n" for o in ordem))
    bruto = seg / "concat.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", seg / "lista.txt", "-c", "copy", bruto])
    # versão final abaixo de ~95 MB (limite de arquivo do GitHub é 100 MB)
    total = dur(bruto); vb = max(1200, min(4000, int((93 * 8 * 1024) / total) - 180))
    run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{vb}k",
         "-maxrate", f"{int(vb*1.2)}k", "-bufsize", f"{vb*2}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", out / "longo.mp4"])
    (out / "capitulos.txt").write_text("".join(f"{int(a//60)}:{int(a%60):02d} {n}\n" for a, n in caps), encoding="utf-8")
    print(f"longo pronto: {total/60:.1f} min, {(out/'longo.mp4').stat().st_size/1e6:.0f} MB")


if __name__ == "__main__":
    main(sys.argv[1])
