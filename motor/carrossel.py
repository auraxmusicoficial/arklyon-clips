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


def gerar(job):
    job = Path(job); dados = json.loads((job / "carrossel.json").read_text())
    out = job / "saida"; out.mkdir(exist_ok=True); feitos = []
    for c in dados["carrosseis"]:
        itens = c["itens"][:8]; total = len(itens) + 2
        slides = [capa(c, job, total)] + [item(c, it, k, len(itens), total, job) for k, it in enumerate(itens)] + [final(c, total)]
        nomes = []
        for i, s in enumerate(slides, 1):
            p = out / f"car_{c['id']}_{i:02d}.jpg"; s.save(p, quality=92); nomes.append(p.name)
        feitos.append((c["id"], nomes)); print("ok carrossel", c["id"], len(nomes), "slides")
    return feitos


if __name__ == "__main__":
    gerar(sys.argv[1])
