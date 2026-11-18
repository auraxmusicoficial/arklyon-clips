"""Funções comuns do motor Vault Clips: legendas ASS, escolha de takes e render de segmentos 16:9."""
import json, subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "motor" / "fontes"
W, H = 1920, 1080
LEAD, TAIL, SHOT, DUCK = 0.7, 0.6, 3.6, 0.0   # DUCK=0: sem áudio original sob a narração (evita Content ID)
# Paleta inspirada em Vice City (ASS usa &HBBGGRR&)
ROSA, CIANO, LARANJA, ROXO = "&H00A53EFF&", "&H00E6E22D&", "&H001C9FFF&", "&H00501A3C&"


def t(s):
    s = max(0.0, s)
    return f"{int(s//3600)}:{int(s%3600//60):02d}:{s%60:05.2f}"


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def cab(w=W, h=H, vertical=False):
    if vertical:
        estilos = f"""Style: Cap,Anton,96,&H00FFFFFF&,&H00FFFFFF&,{ROXO},&H96000000&,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0,1
Style: Quote,Anton,92,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,0,0,0,0,100,100,1,0,1,6,3,5,60,60,0,1
Style: Tit,Anton,92,&H00FFFFFF&,&H00FFFFFF&,{ROSA},&H00000000&,0,0,0,0,100,100,2,0,3,20,0,5,60,60,0,1
Style: End,Anton,70,{LARANJA},{LARANJA},{ROXO},&H96000000&,0,0,0,0,100,100,2,0,1,6,2,5,60,60,0,1"""
    else:
        estilos = f"""Style: Cap,Anton,72,&H00FFFFFF&,&H00FFFFFF&,{ROXO},&H96000000&,0,0,0,0,100,100,1,0,1,5,3,2,80,80,70,1
Style: Quote,Anton,62,&H00FFFFFF&,&H00FFFFFF&,&H00000000&,&H96000000&,0,0,0,0,100,100,1,0,1,4,2,2,80,80,90,1
Style: CapNum,Anton,40,{CIANO},{CIANO},{ROXO},&H00000000&,0,0,0,0,100,100,3,0,1,4,0,7,0,0,0,1
Style: CapTit,Anton,86,&H00FFFFFF&,&H00FFFFFF&,{ROSA},&H00000000&,0,0,0,0,100,100,2,0,3,16,0,7,0,0,0,1
Style: Hook,Anton,104,&H00FFFFFF&,&H00FFFFFF&,{ROXO},&H96000000&,0,0,0,0,100,100,2,0,1,8,4,5,0,0,0,1
Style: Sub,Anton,120,{LARANJA},{LARANJA},{ROXO},&H96000000&,0,0,0,0,100,100,4,0,1,8,4,5,0,0,0,1"""
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{estilos}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def legendas(palavras, off, n=4, estilo="Cap", dest=ROSA, pos=None):
    """Legenda palavra a palavra, com a palavra falada em destaque."""
    ws = [dict(w, w=w["w"].strip().upper().replace("{", "").replace("}", "")) for w in palavras if w["w"].strip()]
    grupos, g = [], []
    for i, w in enumerate(ws):
        g.append(w)
        prox = ws[i + 1] if i + 1 < len(ws) else None
        if len(g) >= n or prox is None or prox["s"] - w["e"] > 0.5 or w["w"][-1:] in ".!?,":
            grupos.append(g); g = []
    L = []
    p = (r"{\pos(%d,%d)}" % pos) if pos else ""
    for g in grupos:
        for i, w in enumerate(g):
            a = g[0]["s"] if i == 0 else w["s"]
            b = g[i + 1]["s"] if i + 1 < len(g) else g[-1]["e"] + 0.1
            if b <= a:
                continue
            txt = " ".join((r"{\c" + dest + r"\fscx108\fscy108}" + x["w"] + r"{\c&H00FFFFFF&\fscx100\fscy100}") if j == i else x["w"]
                           for j, x in enumerate(g))
            L.append(f"Dialogue: 0,{t(a+off)},{t(b+off)},{estilo},,0,0,0,,{p}{txt}")
    return L


def takes(ranges, d):
    """Escolhe takes curtos espalhados pelos intervalos de b-roll até cobrir a duração d."""
    n = max(1, int(d / SHOT + 0.999))
    total = sum(b - a for a, b in ranges)
    out = []
    for k in range(n):
        pos = (k + 0.5) * total / n
        for a, b in ranges:
            if pos <= b - a:
                out.append(max(a, min(a + pos, b - SHOT))); break
            pos -= b - a
    return out


def render_segmento(src, saida, inicios, d, ass=None, narr=None, narr_off=0.0, vol_orig=DUCK, take=SHOT):
    """Renderiza um segmento 16:9 com takes do vídeo-fonte, zoom leve, áudio original baixo + narração."""
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for s in inicios:
        cmd += ["-ss", f"{s:.2f}", "-t", f"{take + 0.1:.2f}", "-i", str(src)]
    if narr:
        cmd += ["-i", str(narr)]
    fc = []
    for i in range(len(inicios)):
        dd = "1" if i % 2 == 0 else "-1"
        fc.append(f"[{i}:v]scale=2112:1188,crop={W}:{H}:x='(iw-ow)/2+{dd}*(iw-ow)/2*(t/{take:.2f}-0.5)':y='(ih-oh)/2',"
                  f"setsar=1,fps=30,trim=0:{take:.2f},setpts=PTS-STARTPTS[v{i}];")
        fc.append(f"[{i}:a]atrim=0:{take:.2f},asetpts=PTS-STARTPTS,volume={vol_orig}[a{i}];")
    fc.append("".join(f"[v{i}][a{i}]" for i in range(len(inicios))) + f"concat=n={len(inicios)}:v=1:a=1[vc][ac];")
    filtro_ass = f"ass='{ass}':fontsdir={FONTES}," if ass else ""
    fc.append(f"[vc]trim=0:{d:.2f},setpts=PTS-STARTPTS,{filtro_ass}fade=t=in:st=0:d=0.25,fade=t=out:st={d-0.25:.2f}:d=0.25[v];")
    if narr:
        ni = len(inicios); ms = int(narr_off * 1000)
        fc.append(f"[{ni}:a]aresample=48000,adelay={ms}|{ms},volume=1.35[n];")
        fc.append(f"[ac]aresample=48000[ac2];[ac2][n]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89,atrim=0:{d:.2f}[a]")
    else:
        fc.append(f"[ac]aresample=48000,alimiter=limit=0.89,atrim=0:{d:.2f}[a]")
    cmd += ["-filter_complex", "".join(fc), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(saida)]
    run(cmd)


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
