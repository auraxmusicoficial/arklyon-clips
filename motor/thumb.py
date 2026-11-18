"""Thumbnails chamativas (estilo canais grandes de games): zoom no ponto de interesse, cores fortes,
texto gigante com contorno e sombra, círculo + seta vermelhos apontando o detalhe e selo de destaque.

Uso: thumb(src, tempo, linhas, selo, saida, vertical=False, x=0.5, foco=None, zoom=1.0, circulo=True, seta=True,
           estilo="gta", estrelas=0)
 - estilo "gta" (padrão): fonte Pricedown, cores Vice City (rosa/laranja/roxo/ciano), estrelas de procurado.
 - estrelas: 0 a 5 estrelas de "procurado" acima do título (ótimo p/ temas de polícia, crime, perigo, segredo).
 - linhas: 1 a 3 linhas CURTAS (1–3 palavras cada). A 2ª linha sai em amarelo e maior (é a palavra-gatilho).
 - foco: [fx, fy] de 0 a 1 no quadro original — o detalhe que gera curiosidade (rosto, objeto, placa...).
 - zoom: aproxima em direção ao foco (1.0 = sem zoom; 1.3–1.8 costuma ficar ótimo)."""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
from comum import FONTES

ANTON = str(FONTES / "Anton-Regular.ttf")
PRICEDOWN = FONTES / "Pricedown.otf"
GTA_FONTE = str(PRICEDOWN) if PRICEDOWN.exists() else ANTON
CIANO, LARANJA, SOL = (0, 229, 212), (255, 128, 48), (255, 214, 64)
BRANCO, AMARELO, ROSA, VERMELHO, ROXO, PRETO = (255, 255, 255), (255, 230, 0), (255, 62, 165), (255, 32, 32), (60, 26, 80), (0, 0, 0)


def _quadro(src, tempo):
    p = Path(tempfile.mkdtemp()) / "q.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{tempo:.2f}", "-i", str(src), "-frames:v", "1", str(p)], check=True)
    img = Image.open(p).convert("RGB")
    # corta tarjas pretas (letterbox) se houver
    g = img.convert("L"); w, h = g.size
    linhas_claras = [y for y in range(h) if max(g.crop((0, y, w, y + 1)).getdata()) > 40]
    if linhas_claras and (linhas_claras[0] > 4 or linhas_claras[-1] < h - 5):
        img = img.crop((0, linhas_claras[0], w, linhas_claras[-1] + 1))
    return img


def _enquadrar(img, W, H, foco, zoom, x):
    iw, ih = img.size
    esc = max(W / iw, H / ih) * zoom
    img = img.resize((int(iw * esc), int(ih * esc)), Image.LANCZOS)
    iw, ih = img.size
    fx, fy = foco if foco else (x, 0.4)
    cx, cy = fx * iw, fy * ih
    l = int(min(max(cx - W * (0.68 if not foco else 0.62), 0), iw - W)) if W > H else int(min(max(cx - W / 2, 0), iw - W))
    t = int(min(max(cy - H / 2, 0), ih - H))
    return img.crop((l, t, l + W, t + H)), (cx - l, cy - t)


def _texto(d, xy, txt, size, cor, anchor="la", stroke=12):
    f = ImageFont.truetype(ANTON, size)
    x, y = xy
    d.text((x + 8, y + 10), txt, font=f, fill=(0, 0, 0, 160), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
    d.text((x, y), txt, font=f, fill=cor, anchor=anchor, stroke_width=stroke, stroke_fill=PRETO)
    return d.textbbox((x, y), txt, font=f, anchor=anchor, stroke_width=stroke)


def _ajusta(d, txt, size, largura_max):
    while size > 40 and d.textlength(txt, font=ImageFont.truetype(ANTON, size)) > largura_max:
        size -= 6
    return size


def _seta(d, a, b, cor=VERMELHO, w=22):
    import math
    (x1, y1), (x2, y2) = a, b
    ang = math.atan2(y2 - y1, x2 - x1)
    x2b, y2b = x2 - 55 * math.cos(ang), y2 - 55 * math.sin(ang)
    d.line([(x1, y1), (x2b, y2b)], fill=PRETO, width=w + 12)
    d.line([(x1, y1), (x2b, y2b)], fill=cor, width=w)
    p = [(x2, y2), (x2b + 38 * math.cos(ang + 1.9), y2b + 38 * math.sin(ang + 1.9)),
         (x2b + 38 * math.cos(ang - 1.9), y2b + 38 * math.sin(ang - 1.9))]
    d.polygon(p, fill=cor, outline=PRETO)



def _degrade(w, h, cores, vertical=True):
    """Imagem com degradê entre várias cores (de cima pra baixo)."""
    g = Image.new("RGB", (w, h)); d = ImageDraw.Draw(g)
    n = len(cores) - 1
    for i in range(h if vertical else w):
        t = i / max(1, (h if vertical else w) - 1); k = min(int(t * n), n - 1); u = t * n - k
        c = tuple(int(cores[k][j] + (cores[k + 1][j] - cores[k][j]) * u) for j in range(3))
        d.line([(0, i), (w, i)] if vertical else [(i, 0), (i, h)], fill=c)
    return g


def _texto_gta(img, xy, txt, size, preench, anchor="la", stroke=None):
    """Texto no estilo dos títulos de GTA: fonte Pricedown, contorno preto grosso, sombra dura deslocada,
    preenchimento sólido ou em degradê (lista de cores)."""
    f = ImageFont.truetype(GTA_FONTE, size)
    stroke = stroke or max(6, size // 12)
    d = ImageDraw.Draw(img, "RGBA")
    x, y = xy
    sh = max(5, size // 16)
    d.text((x + sh, y + sh), txt, font=f, fill=PRETO, anchor=anchor, stroke_width=stroke, stroke_fill=PRETO)
    d.text((x, y), txt, font=f, fill=PRETO, anchor=anchor, stroke_width=stroke, stroke_fill=PRETO)
    caixa = d.textbbox((x, y), txt, font=f, anchor=anchor, stroke_width=stroke)
    if isinstance(preench, list):
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).text((x, y), txt, font=f, fill=255, anchor=anchor)
        l, t, r, b = caixa
        g = _degrade(max(1, r - l), max(1, b - t), preench)
        camada = Image.new("RGB", img.size); camada.paste(g, (l, t))
        img.paste(camada, (0, 0), m)
    else:
        d.text((x, y), txt, font=f, fill=preench, anchor=anchor)
    return caixa


def _ajusta_gta(txt, size, largura_max):
    while size > 40 and ImageFont.truetype(GTA_FONTE, size).getlength(txt) > largura_max:
        size -= 6
    return size


def _estrela(d, cx, cy, r, cheia=True):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=BRANCO if cheia else (0, 0, 0, 110), outline=PRETO, width=max(3, r // 6))


def _estrelas(d, x, y, r, n, anchor_centro=False):
    """Fileira de 5 estrelas de 'procurado' (n cheias)."""
    passo = r * 2.25
    x0 = x - passo * 2 if anchor_centro else x + r
    for i in range(5):
        _estrela(d, x0 + i * passo, y, r, i < n)


def _grade_vice(img, W, H, vertical):
    """Correção de cor Vice City: realces rosados/laranja e sombras roxas/ciano, céu de pôr do sol."""
    img = ImageEnhance.Color(img).enhance(1.5)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    por_do_sol = _degrade(W, H, [(255, 70, 160), (255, 120, 60), (40, 10, 70)])
    img = Image.blend(img, por_do_sol, 0.16)
    # faixa escura roxa do lado do texto (legibilidade)
    sombra = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sombra)
    if vertical:
        for i in range(980):
            ds.line([(0, i), (W, i)], fill=int(215 * (1 - i / 980) ** 1.2))
        for i in range(500):
            ds.line([(0, H - i), (W, H - i)], fill=int(170 * (1 - i / 500) ** 1.4))
    else:
        for i in range(800):
            ds.line([(i, 0), (i, H)], fill=int(225 * (1 - i / 800) ** 1.1))
    sombra = sombra.filter(ImageFilter.GaussianBlur(30))
    return Image.composite(_degrade(W, H, [(48, 8, 78), (22, 4, 44)]), img, sombra)


def thumb_gta(img, W, H, fx, fy, linhas, selo, vertical, foco, circulo, seta, estrelas):
    img = _grade_vice(img, W, H, vertical)
    if vertical:
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
        if foco and fy < 1150:   # foco embaixo do texto: círculo/seta atrapalham a leitura
            circulo = seta = False
    d = ImageDraw.Draw(img, "RGBA")
    if circulo and foco:
        r = int(min(W, H) * (0.17 if not vertical else 0.13))
        for wdt, cor in ((26, PRETO), (14, ROSA)):
            d.ellipse([fx - r, fy - r, fx + r, fy + r], outline=cor, width=wdt)
    linhas = [l.upper() for l in linhas[:3]]
    cores = [BRANCO, [SOL, LARANJA, ROSA], CIANO]
    caixas = []
    if vertical:
        y = 150
        if estrelas:
            _estrelas(d, W // 2, y + 40, 46, estrelas, anchor_centro=True); y += 120
        for i, l in enumerate(linhas):
            s = _ajusta_gta(l, [160, 220, 150][i], W - 110)
            caixas.append(_texto_gta(img, (W // 2, y), l, s, cores[i], anchor="ma"))
            y = caixas[-1][3] + 10
        ancora = (W // 2, y + 20)
    else:
        y = 34
        if estrelas:
            _estrelas(d, 46, y + 30, 30, estrelas); y += 78
        for i, l in enumerate(linhas):
            s = _ajusta_gta(l, [128, 178, 118][i], 650)
            caixas.append(_texto_gta(img, (44, y), l, s, cores[i]))
            y = caixas[-1][3] + 4
        ancora = (caixas[-1][2] + 20, (caixas[-1][1] + caixas[-1][3]) // 2) if caixas else (600, 360)
    d = ImageDraw.Draw(img, "RGBA")
    if seta and foco:
        import math
        r = int(min(W, H) * (0.17 if not vertical else 0.13))
        ang = math.atan2(fy - ancora[1], fx - ancora[0])
        alvo = (fx - (r + 18) * math.cos(ang), fy - (r + 18) * math.sin(ang))
        if math.dist(ancora, alvo) > 90:
            _seta(d, ancora, alvo, cor=ROSA)
    if selo:
        f = ImageFont.truetype(GTA_FONTE, 66 if vertical else 50)
        tw = d.textlength(selo.upper(), font=f)
        bx, by = ((W - tw) / 2 - 30, H - 330) if vertical else (W - tw - 84, 30)
        bh = 104 if vertical else 80
        tag = _degrade(int(tw + 60), bh, [ROSA, LARANJA])
        mk = Image.new("L", tag.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, tag.size[0] - 1, bh - 1], radius=16, fill=255)
        d.rounded_rectangle([bx - 6, by - 6, bx + tw + 66, by + bh + 6], radius=20, fill=PRETO)
        img.paste(tag, (int(bx), int(by)), mk)
        d = ImageDraw.Draw(img, "RGBA")
        d.text((bx + 30 + tw / 2, by + bh / 2), selo.upper(), font=f, fill=BRANCO, anchor="mm", stroke_width=4, stroke_fill=PRETO)
    return img


def thumb(src, tempo, linhas, selo, saida, vertical=False, x=0.5, foco=None, zoom=1.0, circulo=True, seta=True,
          estilo="gta", estrelas=0):
    W, H = (1080, 1920) if vertical else (1280, 720)
    img = _quadro(src, tempo)
    img, (fx, fy) = _enquadrar(img, W, H, foco, max(1.0, zoom), x)
    if estilo == "gta":
        thumb_gta(img, W, H, fx, fy, linhas, selo, vertical, foco, circulo, seta, estrelas).save(saida, quality=93)
        return saida
    img = ImageEnhance.Color(img).enhance(1.45)
    img = ImageEnhance.Contrast(img).enhance(1.18)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    # vinheta + faixa escura do lado do texto
    sombra = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sombra)
    if vertical:
        for i in range(900):
            ds.line([(0, i), (W, i)], fill=int(200 * (1 - i / 900) ** 1.3))
    else:
        for i in range(760):
            ds.line([(i, 0), (i, H)], fill=int(215 * (1 - i / 760) ** 1.2))
    sombra = sombra.filter(ImageFilter.GaussianBlur(25))
    img = Image.composite(Image.new("RGB", (W, H), (20, 6, 35)), img, sombra)
    d = ImageDraw.Draw(img, "RGBA")
    if circulo and foco:
        r = int(min(W, H) * (0.17 if not vertical else 0.13))
        for wdt, cor in ((26, PRETO), (14, VERMELHO)):
            d.ellipse([fx - r, fy - r, fx + r, fy + r], outline=cor, width=wdt)
    # texto
    linhas = [l.upper() for l in linhas[:3]]
    if vertical:
        y = 170; caixas = []
        for i, l in enumerate(linhas):
            s = _ajusta(d, l, [170, 230, 160][i], W - 120)
            cor = [BRANCO, AMARELO, ROSA][i]
            caixas.append(_texto(d, (W // 2, y), l, s, cor, anchor="ma", stroke=14))
            y = caixas[-1][3] + 18
        ancora = (W // 2, y + 20)
    else:
        y = 40; caixas = []
        for i, l in enumerate(linhas):
            s = _ajusta(d, l, [150, 205, 140][i], 640)
            cor = [BRANCO, AMARELO, ROSA][i]
            caixas.append(_texto(d, (42, y), l, s, cor, stroke=12))
            y = caixas[-1][3] + 6
        ancora = (caixas[-1][2] + 20, (caixas[-1][1] + caixas[-1][3]) // 2) if caixas else (600, 360)
    if seta and foco:
        r = int(min(W, H) * (0.17 if not vertical else 0.13))
        import math
        ang = math.atan2(fy - ancora[1], fx - ancora[0])
        alvo = (fx - (r + 18) * math.cos(ang), fy - (r + 18) * math.sin(ang))
        if math.dist(ancora, alvo) > 90:
            _seta(d, ancora, alvo)
    if selo:
        f = ImageFont.truetype(ANTON, 62 if vertical else 46)
        tw = d.textlength(selo.upper(), font=f)
        if vertical:
            bx, by = (W - tw) / 2 - 30, H - 330
        else:
            bx, by = W - tw - 80, 34
        d.rounded_rectangle([bx, by, bx + tw + 60, by + (100 if vertical else 76)], radius=18, fill=VERMELHO, outline=PRETO, width=6)
        d.text((bx + 30, by + (14 if vertical else 10)), selo.upper(), font=f, fill=BRANCO)
    img.save(saida, quality=93)
    return saida
