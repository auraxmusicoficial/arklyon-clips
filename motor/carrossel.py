"""Máquina de CARROSSÉIS (Instagram e TikTok modo foto) no estilo GTA/Vice City.
Uso: python3 motor/carrossel.py JOB_DIR   -> lê JOB_DIR/carrossel.json e gera JOB_DIR/saida/car_<id>_NN.jpg (1080x1350)

carrossel.json = {"carrosseis": [{
  "id": "c1",
  "capa": ["GTA 6", "SAFE CODES", "YOU NEED"],     # 1–3 linhas; a 2ª sai grande em degradê
  "selo": "SAVE THIS",                           # selo no canto da capa (opcional)
  "fundo": {"video": "video.mp4", "t": 123.4},  # quadro do vídeo-fonte para a capa (opcional)
  "itens": [{"titulo": "Pelican Bay Pawn Shop", "valor": "0420", "texto": "Back room safe, top floor."}, ...],
  "fonte": "IGN, Rockstar Newswire",            # de onde vieram os dados (sai no último slide)
  "legenda": "...", "tt_title": "...", "hashtags": "#gta6 ..."}]}
Regras de conteúdo: só dados conferidos em fonte confiável (nunca inventar código, local ou número)."""
import json, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from comum import FONTES

W, H = 1080, 1350
ROSA, CIANO, LARANJA, AMARELO = (255, 43, 214), (0, 229, 255), (255, 140, 0), (255, 214, 0)
F_GTA = str(FONTES / "Pricedown.otf"); F_TXT = str(FONTES / "Anton-Regular.ttf")


def fonte(p, n):
    return ImageFont.truetype(p, n)


def base(fundo_img=None):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        k = y / H
        for x in range(W):
            px[x, y] = (int(30 + 70 * k), int(4 + 8 * k), int(70 + 30 * (1 - k)))
    d = ImageDraw.Draw(img, "RGBA")
    hy = 1080
    for i in range(10):
        y = hy + int((i / 9) ** 2 * (H - hy)); d.line((0, y, W, y), fill=ROSA + (90,), width=2)
    for i in range(-12, 13):
        d.line((540 + i * 16, hy, 540 + i * 120, H), fill=ROSA + (80,), width=2)
    if fundo_img is not None:
        f = fundo_img.convert("RGB")
        r = max(W / f.width, H / f.height); f = f.resize((int(f.width * r) + 1, int(f.height * r) + 1))
        f = f.crop(((f.width - W) // 2, (f.height - H) // 2, (f.width - W) // 2 + W, (f.height - H) // 2 + H))
        img = Image.blend(img, f, 0.62)
        sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sombra)
        for y in range(H):
            a = int(200 * max(0, (y - H * 0.35) / (H * 0.65)))
            ds.line((0, y, W, y), fill=(10, 0, 25, a))
        img.paste(sombra, (0, 0), sombra)
    return img


def texto_contorno(d, xy, txt, f, cor, contorno=(0, 0, 0), larg=8, anchor="mm"):
    d.text(xy, txt, font=f, fill=cor, anchor=anchor, stroke_width=larg, stroke_fill=contorno)


def degrade_texto(img, xy, txt, f, cores=(AMARELO, LARANJA, ROSA), larg=10):
    d = ImageDraw.Draw(img)
    xy = (int(xy[0]), int(xy[1]))
    caixa = [int(v) for v in d.textbbox(xy, txt, font=f, anchor="mm", stroke_width=larg)]
    w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    grad = Image.new("RGB", (w, h)); g = grad.load()
    for y in range(h):
        k = y / max(1, h - 1); c0, c1 = (cores[0], cores[1]) if k < 0.5 else (cores[1], cores[2]); kk = (k % 0.5) * 2
        cor = tuple(int(c0[i] + (c1[i] - c0[i]) * kk) for i in range(3))
        for x in range(w):
            g[x, y] = cor
    masc = Image.new("L", (W, H)); ImageDraw.Draw(masc).text(xy, txt, font=f, fill=255, anchor="mm")
    d.text(xy, txt, font=f, fill=(0, 0, 0), anchor="mm", stroke_width=larg, stroke_fill=(20, 0, 40))
    camada = Image.new("RGB", (W, H)); camada.paste(grad, (caixa[0], caixa[1]))
    img.paste(camada, (0, 0), masc)


def caber(d, txt, path, maxw, n0, nmin=40):
    n = n0
    while n > nmin and d.textlength(txt, font=fonte(path, n)) > maxw:
        n -= 4
    return fonte(path, n)


def marca(d, i, total):
    d.rectangle((0, 0, W, 78), fill=(10, 0, 30, 210)); d.line((0, 78, W, 78), fill=ROSA, width=4)
    d.text((40, 40), "HQ VAULT  •  GTA 6 SECRETS", font=fonte(F_TXT, 38), fill=AMARELO, anchor="lm")
    d.text((W - 40, 40), f"{i}/{total}", font=fonte(F_TXT, 38), fill=CIANO, anchor="rm")


def capa(c, job, total):
    fimg = None
    fz = c.get("fundo") or {}
    if fz.get("video"):
        import subprocess, tempfile
        tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(fz.get("t", 10)), "-i", str(job / fz["video"]),
                        "-frames:v", "1", str(tmp)], check=False)
        if tmp.exists() and tmp.stat().st_size:
            fimg = Image.open(tmp)
    img = base(fimg); d = ImageDraw.Draw(img, "RGBA")
    marca(d, 1, total)
    linhas = c["capa"]
    y = 760
    for k, ln in enumerate(linhas):
        if k == 1:
            f = caber(d, ln, F_GTA, 980, 200); degrade_texto(img, (540, y), ln, f); y += f.size * 0.95
        else:
            f = caber(d, ln, F_GTA, 960, 120)
            texto_contorno(d, (540, y), ln, f, CIANO if k == 2 else (255, 255, 255)); y += f.size * 1.0
    if c.get("selo"):
        s = c["selo"].upper(); f = fonte(F_TXT, 54); w = d.textlength(s, font=f) + 60
        d.rounded_rectangle((W - w - 40, 120, W - 40, 200), 16, fill=ROSA)
        d.text((W - 40 - w / 2, 160), s, font=f, fill=(255, 255, 255), anchor="mm")
    texto_contorno(d, (540, H - 90), "SWIPE  →", fonte(F_TXT, 64), AMARELO, larg=6)
    return img


def imagem(job, spec):
    """spec = {"video": "video.mp4", "t": 12.3} (quadro do vídeo) ou {"arquivo": "img.jpg"} (imagem na pasta do job)."""
    if not spec or job is None:
        return None
    if spec.get("arquivo"):
        p = Path(job) / spec["arquivo"]
        return Image.open(p) if p.exists() else None
    return quadro(Path(job), spec.get("video", "video.mp4"), spec.get("t", 10))


def setas(img, seq, y, larg_max=960):
    """Desenha a sequência do D-pad (U/D/L/R) como setas próprias, em até 2 linhas."""
    d = ImageDraw.Draw(img, "RGBA"); seq = [x.strip().upper()[0] for x in seq if x.strip()]
    por_linha = 5 if len(seq) > 5 else len(seq); tam = min(150, int(larg_max / max(1, por_linha) - 24))
    linhas = [seq[i:i + por_linha] for i in range(0, len(seq), por_linha)]
    for li, linha in enumerate(linhas):
        x = 540 - (len(linha) * (tam + 24) - 24) / 2; yy = y + li * (tam + 30)
        for k, dirc in enumerate(linha):
            cx, cy, r = x + tam / 2, yy + tam / 2, tam / 2
            d.rounded_rectangle((x, yy, x + tam, yy + tam), 24, fill=(10, 0, 30, 235), outline=AMARELO, width=6)
            a = r * 0.55
            pts = {"U": [(cx, cy - a), (cx - a, cy + a * 0.6), (cx + a, cy + a * 0.6)],
                   "D": [(cx, cy + a), (cx - a, cy - a * 0.6), (cx + a, cy - a * 0.6)],
                   "L": [(cx - a, cy), (cx + a * 0.6, cy - a), (cx + a * 0.6, cy + a)],
                   "R": [(cx + a, cy), (cx - a * 0.6, cy - a), (cx - a * 0.6, cy + a)]}.get(dirc)
            if pts:
                d.polygon(pts, fill=AMARELO)
            d.text((x + 16, yy + 10), str(li * por_linha + k + 1), font=fonte(F_TXT, 30), fill=(200, 200, 230))
            x += tam + 24
    return y + len(linhas) * (tam + 30)


def colar(img, foto, caixa, borda=ROSA, vazio=None):
    """Cola a foto preenchendo a caixa (corta o excesso) com moldura."""
    if foto is None:
        if vazio:
            d = ImageDraw.Draw(img, "RGBA"); d.rounded_rectangle([int(v) for v in caixa], 18, fill=(10, 0, 30, 220), outline=borda, width=6)
            d.text(((caixa[0] + caixa[2]) / 2, (caixa[1] + caixa[3]) / 2), vazio, font=fonte(F_GTA, 90), fill=borda, anchor="mm")
        return
    x0, y0, x1, y1 = [int(v) for v in caixa]; w, h = x1 - x0, y1 - y0
    f = foto.convert("RGB"); r = max(w / f.width, h / f.height)
    f = f.resize((int(f.width * r) + 1, int(f.height * r) + 1))
    f = f.crop(((f.width - w) // 2, (f.height - h) // 2, (f.width - w) // 2 + w, (f.height - h) // 2 + h))
    ImageDraw.Draw(img).rounded_rectangle((x0 - 7, y0 - 7, x1 + 7, y1 + 7), 18, fill=borda)
    img.paste(f, (x0, y0))


def multilinha(img, d, centro_y, txt, path, maxw, n0, cor=(255, 255, 255), larg=6, max_linhas=4, chars=18):
    linhas = textwrap.wrap(txt, chars)[:max_linhas] or [txt]
    f = min((caber(d, ln, path, maxw, n0) for ln in linhas), key=lambda x: x.size)
    alt = f.size * 1.08; y = centro_y - alt * (len(linhas) - 1) / 2
    for ln in linhas:
        texto_contorno(d, (540, y), ln, f, cor, larg=larg); y += alt
    return y


# ---------- formato "vs": GTA V x GTA VI (curtir = um, comentar = outro) ----------
def vs_capa(c, job, total):
    img = base(); d = ImageDraw.Draw(img, "RGBA"); marca(d, 1, total)
    colar(img, imagem(job, c.get("img_a")), (40, 300, 530, 900), CIANO, vazio=c.get("rotulo_a", "GTA V"))
    colar(img, imagem(job, c.get("img_b")), (550, 300, 1040, 900), ROSA, vazio=c.get("rotulo_b", "GTA VI"))
    d = ImageDraw.Draw(img, "RGBA")
    texto_contorno(d, (285, 250), c.get("rotulo_a", "GTA V"), fonte(F_GTA, 110), CIANO)
    texto_contorno(d, (795, 250), c.get("rotulo_b", "GTA VI"), fonte(F_GTA, 110), ROSA)
    d.ellipse((470, 530, 610, 670), fill=AMARELO, outline=(0, 0, 0), width=6)
    d.text((540, 602), "VS", font=fonte(F_GTA, 90), fill=(0, 0, 0), anchor="mm")
    multilinha(img, d, 1010, c["capa"][0].upper(), F_TXT, 980, 96, chars=22, max_linhas=2)
    texto_contorno(d, (540, 1150), c.get("acao", "LIKE = GTA V   •   COMMENT = GTA VI"), fonte(F_TXT, 54), AMARELO, larg=5)
    if total > 2:
        texto_contorno(d, (540, H - 70), "SWIPE  →", fonte(F_TXT, 56), (255, 255, 255), larg=5)
    return img


def vs_item(c, it, k, total, job):
    img = base(); d = ImageDraw.Draw(img, "RGBA"); marca(d, k + 2, total)
    multilinha(img, d, 170, it["titulo"].upper(), F_GTA, 980, 120, AMARELO, chars=16, max_linhas=2)
    for lado, (x0, cor, rot) in enumerate(((40, CIANO, c.get("rotulo_a", "GTA V")), (550, ROSA, c.get("rotulo_b", "GTA VI")))):
        chave = "a" if lado == 0 else "b"
        colar(img, imagem(job, it.get(f"img_{chave}")), (x0, 330, x0 + 490, 700), cor, vazio=rot)
        d = ImageDraw.Draw(img, "RGBA")
        texto_contorno(d, (x0 + 245, 760), rot, fonte(F_GTA, 80), cor)
        yy = 840
        for ln in textwrap.wrap(str(it.get(chave, "")), 14)[:5]:
            texto_contorno(d, (x0 + 245, yy), ln, caber(d, ln, F_TXT, 470, 58), (255, 255, 255), larg=4); yy += 70
    return img


def vs_final(c, total):
    img = base(); d = ImageDraw.Draw(img, "RGBA"); marca(d, total, total)
    texto_contorno(d, (540, 380), "WHO WINS?", fonte(F_GTA, 170), AMARELO, larg=10)
    multilinha(img, d, 620, c.get("pergunta", "Comment V or VI and defend your pick"), F_TXT, 960, 76, chars=22)
    d = ImageDraw.Draw(img, "RGBA")
    texto_contorno(d, (540, 900), "Send this to the friend who disagrees", fonte(F_TXT, 54), CIANO, larg=4)
    texto_contorno(d, (540, 1050), "@hqvaultclips", fonte(F_TXT, 70), ROSA, larg=5)
    return img


# ---------- formato "tag": marque um amigo ----------
def tag_slide(c, it, k, total, job, capa=False):
    img = base(imagem(job, it.get("img"))); d = ImageDraw.Draw(img, "RGBA"); marca(d, k + 1, total)
    if capa:
        texto_contorno(d, (540, 330), c.get("chamada", "TAG YOUR"), fonte(F_GTA, 130), (255, 255, 255))
        degrade_texto(img, (540, 520), c["capa"][1].upper() if len(c["capa"]) > 1 else "PARTNER", caber(d, c["capa"][1] if len(c["capa"]) > 1 else "PARTNER", F_GTA, 980, 210))
        d = ImageDraw.Draw(img, "RGBA")
        multilinha(img, d, 1060, it["texto"], F_TXT, 960, 70, chars=24)
    else:
        multilinha(img, d, 1000, it["texto"].upper(), F_TXT, 960, 84, chars=20)
    texto_contorno(d, (540, H - 70), it.get("rodape", "TAG THEM 👇").replace("👇", "BELOW"), fonte(F_TXT, 56), AMARELO, larg=5)
    return img


# ---------- formato "unico" / "teaser": post de 1 ou 2 páginas ----------
def unico(c, job, i=1, total=1, texto=None, rodape=None):
    img = base(imagem(job, c.get("img"))); d = ImageDraw.Draw(img, "RGBA"); marca(d, i, total)
    linhas = c["capa"] if texto is None else [texto]
    blocos = []
    for k, ln in enumerate(linhas):
        if texto is None and k == 1:
            blocos.append(("grad", ln, caber(d, ln, F_GTA, 980, 190)))
        else:
            path, n0, ch = (F_GTA, 120, 16) if texto is None else (F_TXT, 80, 22)
            for sub in textwrap.wrap(ln.upper() if texto is None else ln, ch)[:7]:
                blocos.append(("txt", sub, caber(d, sub, path, 980, n0 if k == 0 or texto else 84)))
    altura = sum(f.size * 1.1 for _, _, f in blocos)
    y = (H - altura) / 2 + 40
    for tipo, ln, f in blocos:
        yc = int(y + f.size * 0.55)
        if tipo == "grad":
            degrade_texto(img, (540, yc), ln, f); d = ImageDraw.Draw(img, "RGBA")
        else:
            texto_contorno(d, (540, yc), ln, f, (255, 255, 255), larg=6)
        y += f.size * 1.1
    if rodape or c.get("rodape"):
        texto_contorno(d, (540, H - 80), (rodape or c["rodape"]).upper(), fonte(F_TXT, 58), AMARELO, larg=5)
    return img


def quadro(job, video, t):
    import subprocess, tempfile
    tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(job / video), "-frames:v", "1", str(tmp)], check=False)
    return Image.open(tmp) if tmp.exists() and tmp.stat().st_size else None


def item(c, it, k, n_itens, total, job=None):
    img = base(); d = ImageDraw.Draw(img, "RGBA")
    marca(d, k + 2, total)
    d.ellipse((60, 140, 260, 340), fill=ROSA, outline=(255, 255, 255), width=6)
    d.text((160, 242), f"#{k + 1}", font=fonte(F_GTA, 110), fill=(255, 255, 255), anchor="mm")
    tit = it["titulo"].upper()
    linhas = textwrap.wrap(tit, 16) or [tit]
    y = 200 if len(linhas) == 1 else 170
    for ln in linhas[:3]:
        f = caber(d, ln, F_TXT, 740, 92)
        texto_contorno(d, (300, y), ln, f, (255, 255, 255), larg=5, anchor="lm"); y += f.size * 1.08
    y = max(y + 50, 420)
    if it.get("valor"):
        v = str(it["valor"]); f = caber(d, v, F_GTA, 860, 220, 90)
        caixa = (90, y, W - 90, y + f.size + 90)
        d.rounded_rectangle(caixa, 30, fill=(10, 0, 30, 230), outline=AMARELO, width=8)
        degrade_texto(img, (540, (caixa[1] + caixa[3]) // 2), v, f, cores=(AMARELO, AMARELO, LARANJA), larg=8)
        d = ImageDraw.Draw(img, "RGBA"); y = caixa[3] + 60
    if it.get("setas"):   # código de controle (D-pad): ["Up", "Right", ...]
        y = setas(img, it["setas"], y) + 20; d = ImageDraw.Draw(img, "RGBA")
    if it.get("texto"):
        f = fonte(F_TXT, 60)
        for ln in textwrap.wrap(it["texto"], 26)[:6]:
            texto_contorno(d, (540, y + 30), ln, f, (240, 240, 255), larg=4); y += 76
    if it.get("t") is not None and job is not None:   # print do jogo ilustrando o item (opcional)
        q = quadro(job, (c.get("fundo") or {}).get("video", "video.mp4"), it["t"])
        topo = int(max(y + 40, 700)); alt = H - 150 - topo
        if q is not None and alt > 220:
            larg = min(900, int(alt * 16 / 9)); alt = int(larg * 9 / 16)
            q = q.convert("RGB").resize((larg, alt)); x0 = (W - larg) // 2
            d.rounded_rectangle((x0 - 8, topo - 8, x0 + larg + 8, topo + alt + 8), 20, fill=ROSA)
            img.paste(q, (x0, topo)); d = ImageDraw.Draw(img, "RGBA")
    if k == n_itens - 1:
        texto_contorno(d, (540, H - 90), "ONE MORE  →", fonte(F_TXT, 56), CIANO, larg=5)
    return img


def final(c, total):
    img = base(); d = ImageDraw.Draw(img, "RGBA")
    marca(d, total, total)
    texto_contorno(d, (540, 330), "SAVE THIS", fonte(F_GTA, 170), AMARELO, larg=10)
    texto_contorno(d, (540, 470), "you'll need it in-game", fonte(F_TXT, 64), (255, 255, 255), larg=5)
    d.rounded_rectangle((90, 600, W - 90, 900), 34, fill=(10, 0, 30, 230), outline=CIANO, width=6)
    degrade_texto(img, (540, 700), "FOLLOW", fonte(F_GTA, 150))
    d = ImageDraw.Draw(img, "RGBA")
    texto_contorno(d, (540, 830), "1 new GTA 6 secret every day", fonte(F_TXT, 56), (255, 255, 255), larg=4)
    texto_contorno(d, (540, 1000), "@hqvaultclips", fonte(F_TXT, 70), ROSA, larg=5)
    if c.get("fonte"):
        d.text((540, H - 60), f"Source: {c['fonte']}"[:70], font=fonte(F_TXT, 34), fill=(210, 200, 230), anchor="mm")
    return img


def video_reel(job, cid, saida=None, seg_slide=3.2, seg_capa=2.4):
    """Transforma os slides de um post num REEL 9:16 (para o Instagram/Facebook: lá o post de imagem só chega a quem
    já segue — 25/11: carrosséis com 6–25 views — e o Reel é que leva para gente nova). Slide sobre o fundo do estúdio,
    zoom leve, whoosh nas trocas e trilha própria."""
    import subprocess, zlib
    from estudio import fundo
    job = Path(job); out = job / "saida"; slides = sorted(out.glob(f"car_{cid}_*.jpg"))
    if not slides:
        return None
    saida = Path(saida or out / f"reel_{cid}.mp4"); fpng = fundo(out / f"fundo_reel_{cid}.png", comparar=True)
    try:   # título do post no topo e chamada para seguir embaixo (o slide fica no meio)
        dados = json.loads((job / "carrossel.json").read_text())
        c = next(x for x in dados["carrosseis"] if x["id"] == cid)
        img = Image.open(fpng).convert("RGB"); d = ImageDraw.Draw(img, "RGBA")
        tit = (c.get("capa") or [""])[1] if len(c.get("capa") or []) > 1 else (c.get("capa") or [""])[0]
        degrade_texto(img, (540, 215), tit.upper(), caber(d, tit.upper(), F_GTA, 1000, 150))
        d = ImageDraw.Draw(img, "RGBA")
        texto_contorno(d, (540, 1700), "FOLLOW FOR DAILY", fonte(F_TXT, 64), (255, 255, 255), larg=5)
        texto_contorno(d, (540, 1785), "GTA 6 SECRETS", fonte(F_GTA, 96), AMARELO, larg=7)
        img.save(fpng, quality=95)
    except Exception as e:
        print("AVISO texto do fundo do reel:", e)
    durs = [seg_capa] + [seg_slide] * (len(slides) - 1) if len(slides) > 1 else [6.0]
    if len(slides) == 2:
        durs = [3.0, 4.5]
    ent = ["-loop", "1", "-framerate", "30", "-t", f"{sum(durs):.2f}", "-i", str(fpng)]
    fc = "[0:v]scale=1080:1920,setsar=1[bg0];"; ant = "bg0"; t0 = 0.0; marcas = []
    for k, (sl, d) in enumerate(zip(slides, durs)):
        ent += ["-loop", "1", "-framerate", "30", "-t", f"{d:.2f}", "-i", str(sl)]
        fc += (f"[{k+1}:v]scale=1020:1275,zoompan=z='min(1.0+0.0009*on,1.06)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":s=1020x1275:fps=30,setpts=PTS-STARTPTS+{t0:.2f}/TB[s{k}];"
               f"[{ant}][s{k}]overlay=30:330:enable='between(t,{t0:.2f},{t0 + d:.2f})'[bg{k+1}];")
        ant = f"bg{k+1}"; marcas.append(t0); t0 += d
    fc += f"[{ant}]format=yuv420p[v]"
    tmp = out / f"reel_{cid}_mudo.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ent, "-f", "lavfi", "-t", f"{t0:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", fc, "-map", "[v]", "-map", f"{len(slides)+1}:a", "-t", f"{t0:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-shortest", str(tmp)], check=True)
    try:
        from trilha import sonorizar
        sonorizar(tmp, saida, marcas=marcas[1:], estilo="acao", semente=zlib.crc32(cid.encode()) % 1000, volume_db=-8)
        tmp.unlink()
    except Exception as e:
        print("AVISO trilha do reel falhou:", e); tmp.replace(saida)
    print("ok reel do post", cid, f"{t0:.1f}s")
    return saida


def gerar(job):
    job = Path(job); dados = json.loads((job / "carrossel.json").read_text())
    out = job / "saida"; out.mkdir(exist_ok=True); feitos = []
    for c in dados["carrosseis"]:
        fmt = c.get("formato", "lista"); itens = c.get("itens", [])[:8]
        if fmt == "vs":
            total = len(itens) + 2
            slides = [vs_capa(c, job, total)] + [vs_item(c, it, k, total, job) for k, it in enumerate(itens)] + [vs_final(c, total)]
            if not itens:   # versão de 1 página: só a capa "curtir x comentar"
                slides = [vs_capa(c, job, 1)]
        elif fmt == "tag":
            total = len(itens)
            slides = [tag_slide(c, it, k, total, job, capa=(k == 0)) for k, it in enumerate(itens)]
        elif fmt == "teaser":   # 2 páginas: pergunta/gancho -> resposta
            slides = [unico(c, job, 1, 2, rodape="SWIPE FOR THE ANSWER  →"), unico(c, job, 2, 2, texto=c["resposta"], rodape="SAVE THIS")]
        elif fmt == "unico":
            slides = [unico(c, job)]
        else:
            total = len(itens) + 2
            slides = [capa(c, job, total)] + [item(c, it, k, len(itens), total, job) for k, it in enumerate(itens)] + [final(c, total)]
        nomes = []
        for i, s in enumerate(slides, 1):
            p = out / f"car_{c['id']}_{i:02d}.jpg"; s.save(p, quality=92); nomes.append(p.name)
        feitos.append((c["id"], nomes)); print("ok carrossel", c["id"], len(nomes), "slides")
        try:
            video_reel(job, c["id"])
        except Exception as e:
            print("AVISO reel do post falhou (o Instagram recebe o carrossel):", e)
    return feitos


if __name__ == "__main__":
    gerar(sys.argv[1])
