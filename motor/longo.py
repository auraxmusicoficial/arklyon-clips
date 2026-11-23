"""Monta o vídeo longo 16:9 (capítulos, legendas, cards, citações do original).
Uso: python3 motor/longo.py JOB_DIR   -> JOB_DIR/saida/longo.mp4 + capitulos.txt"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import (CIANO, LEAD, ROSA, TAIL, cab, dur, legendas, ler_json, render_segmento, run, t, takes)


def estudio_l(bruto, ass, saida, fpng):
    """Layout original 16:9: fundo próprio + gameplay numa janela + painel de informação; legendas/cartões por cima."""
    from comum import FONTES
    from estudio import JANELA_L
    x, y, w, h = JANELA_L
    d = dur(bruto)
    fc = (f"[1:v]scale=1920:1080,setsar=1,fps=30[bg];[0:v]scale={w}:{h},setsar=1[fg];"
          f"[bg][fg]overlay={x}:{y}:shortest=1,ass='{ass}':fontsdir={FONTES}[v]")
    run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-loop", "1", "-framerate", "30", "-t", f"{d:.2f}", "-i", fpng,
         "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "copy", saida])


def painel_l(s, palavras, d, titulo_cap):
    """Linhas ASS do painel da direita: cartões s["cartoes"] = [{"quando": "...", "texto": "..."}] ou o nome do capítulo."""
    import re
    nz = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    pw = [nz(w["w"]) for w in palavras]; marcas = []
    for c in s.get("cartoes", []):
        alvo = [nz(x) for x in str(c.get("quando", "")).split()[:4] if nz(x)]
        for i in range(len(pw) - len(alvo) + 1):
            if alvo and pw[i:i + len(alvo)] == alvo:
                marcas.append((LEAD + palavras[i]["s"], c["texto"].upper())); break
    marcas.sort()
    if not marcas:
        marcas = [(0.0, titulo_cap.upper())]
    L = []
    for k, (a, txt) in enumerate(marcas):
        b = marcas[k + 1][0] if k + 1 < len(marcas) else d
        import textwrap
        txt2 = "\\N".join(textwrap.wrap(txt, 13 if len(txt) <= 40 else 16)[:6])
        L.append(rf"Dialogue: 2,{t(a)},{t(b)},Hook,,0,0,0,,{{\pos(1626,560)\fs{70 if len(txt) > 30 else 88}\fad(150,0)}}{txt2}")
    return L


def main(job):
    job = Path(job); r = ler_json(job / "roteiro.json"); L0 = r["longo"]
    estudio = L0.get("layout", "estudio") != "classico"   # layout original (padrão desde 23/11)
    if estudio:
        from estudio import fundo_longo
        (job / "seg").mkdir(exist_ok=True)
        fpng = fundo_longo(job / "seg" / "estudio_l.png")
    T = ler_json(job / "voz" / "tempos.json")
    fonte = ler_json(job / "transc.json")["palavras"]
    src = job / "video.mp4"
    seg = job / "seg"; seg.mkdir(exist_ok=True)
    out = job / "saida"; out.mkdir(exist_ok=True)
    ordem, caps, ncap, tempo = [], [], 0, 0.0
    srt = []   # legenda em inglês com tempo global (vira base para as traduções)
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
        if estudio:
            L = [ln.replace(r"\pos(960,", r"\pos(688,").replace(r"\fad(200,250)}CHAPTER", r"\fad(200,0)}CHAPTER")
                 for ln in L]
            L = [ln.replace(f"{t(3.4)},CapNum", f"{t(d)},CapNum").replace(f"{t(3.4)},CapTit", f"{t(d)},CapTit")
                 .replace(r"\fad(0,250)}", r"}") for ln in L]
            nome_cap = s.get("cap") or (L0.get("titulo", "GTA 6 GUIDE") if i == 0 else "")
            if nome_cap:
                L += painel_l(s, info["palavras"], d, nome_cap)
            L.append(rf"Dialogue: 3,{t(0)},{t(d)},CapNum,,0,0,0,,{{\an9\pos(1880,40)\fs44\c&H00E5FF&}}HQ VAULT • GTA 6")
        ass = seg / f"{sid}.ass"; ass.write_text(cab() + "\n".join(L) + "\n", encoding="utf-8")
        grupo = []
        for k, w in enumerate(info["palavras"]):
            grupo.append(w)
            prox = info["palavras"][k + 1] if k + 1 < len(info["palavras"]) else None
            if len(grupo) >= 9 or prox is None or w["w"].strip()[-1:] in ".!?" or prox["s"] - w["e"] > 0.6:
                srt.append((tempo + LEAD + grupo[0]["s"], tempo + LEAD + grupo[-1]["e"] + 0.15,
                            " ".join(x["w"].strip() for x in grupo))); grupo = []
        if estudio:
            render_segmento(src, seg / f"{sid}_raw.mp4", takes(s["broll"], d), d, None, job / "voz" / f"{sid}.wav", LEAD)
            estudio_l(seg / f"{sid}_raw.mp4", ass, seg / f"{sid}.mp4", fpng)
        else:
            render_segmento(src, seg / f"{sid}.mp4", takes(s["broll"], d), d, ass, job / "voz" / f"{sid}.wav", LEAD)
        ordem.append(sid); tempo += d
        print("ok", sid, round(d, 1), flush=True)
        if s.get("quote"):
            a, b = s["quote"]; a -= 0.3; b += 0.5
            ws = [dict(w, s=w["s"] - a, e=w["e"] - a) for w in fonte if a <= w["s"] < b]
            assq = seg / f"{sid}_q.ass"
            assq.write_text(cab() + "\n".join(legendas(ws, 0, n=5, estilo="Quote", dest=CIANO)) + "\n", encoding="utf-8")
            if estudio:
                render_segmento(src, seg / f"{sid}_qraw.mp4", [a], b - a, None, vol_orig=1.0, take=b - a)
                estudio_l(seg / f"{sid}_qraw.mp4", assq, seg / f"{sid}_q.mp4", fpng)
            else:
                render_segmento(src, seg / f"{sid}_q.mp4", [a], b - a, assq, vol_orig=1.0, take=b - a)
            ordem.append(sid + "_q"); tempo += dur(seg / f"{sid}_q.mp4")
    (seg / "lista.txt").write_text("".join(f"file '{seg}/{o}.mp4'\n" for o in ordem))
    bruto = seg / "concat.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", seg / "lista.txt", "-c", "copy", bruto])
    # trilha original (synthwave) + whoosh/impacto nas trocas de capítulo — se falhar, segue sem trilha
    try:
        from trilha import sonorizar
        import zlib
        com_som = seg / "concat_som.mp4"
        sonorizar(bruto, com_som, marcas=[a for a, _ in caps[1:]], estilo=L0.get("trilha", "noite"),
                  semente=zlib.crc32(L0.get("titulo", "").encode()) % 1000, volume_db=-17)
        bruto = com_som; print("trilha ok")
    except Exception as e:
        print("AVISO trilha falhou, seguindo sem música:", e)
    # o longo sobe direto pela API do YouTube (não vai pro GitHub), então pode ter qualidade boa
    total = dur(bruto); vb = 3000
    run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{vb}k",
         "-maxrate", f"{int(vb*1.2)}k", "-bufsize", f"{vb*2}k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", out / "longo.mp4"])
    ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round(x%1*1000)) % 1000:03d}"
    (out / "legenda_en.srt").write_text("".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n" for i, (a, b, txt) in enumerate(srt, 1)),
                                        encoding="utf-8")
    (out / "capitulos.txt").write_text("".join(f"{int(a//60)}:{int(a%60):02d} {n}\n" for a, n in caps), encoding="utf-8")
    print(f"longo pronto: {total/60:.1f} min, {(out/'longo.mp4').stat().st_size/1e6:.0f} MB")


if __name__ == "__main__":
    main(sys.argv[1])
