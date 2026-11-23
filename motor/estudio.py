"""Layout ORIGINAL dos Shorts ("estúdio HQ Vault"): fundo próprio estilo Vice City, gameplay numa janela com moldura
neon e um painel de informação nosso (cartões com a dica/dado de cada parte da narração).
Motivo (23/11): TikTok marcou vídeos como "conteúdo não original" e o Instagram bloqueou a monetização — o gameplay
em tela cheia parecia repostagem. Aqui o gameplay é só uma parte da tela; o resto é design e informação nossos."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
JANELA = (24, 340, 1032, 580)          # x, y, largura, altura do gameplay (16:9)
PAINEL = (40, 980, 1040, 1500)         # caixa dos cartões
ROSA, CIANO, LARANJA = (255, 43, 214), (0, 229, 255), (255, 170, 0)


def fundo(saida, comparar=False):
    saida = Path(saida)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):   # degradê roxo-escuro -> magenta -> roxo
        k = y / H
        r = int(28 + 90 * (1 - abs(k - 0.55) * 1.8)) if 0.2 < k < 0.9 else 28
        g = int(6 + 10 * k)
        b = int(60 + 60 * (1 - k))
        for x in range(W):
            px[x, y] = (max(18, r), g, b)
    d = ImageDraw.Draw(img, "RGBA")
    # sol retrô (listrado, estilo synthwave) atrás da grade
    sol = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sol)
    cx, cy, r = 540, 1640, 230
    for yy in range(cy - r, cy + 1):
        k = (yy - (cy - r)) / r
        if k > 0.45 and int((yy - cy) / 9) % 2 == 0:
            continue   # listras vazadas na metade de baixo
        meia = int((r * r - (yy - cy) ** 2) ** 0.5)
        ds.line((cx - meia, yy, cx + meia, yy), fill=(255, int(210 - 120 * k), int(60 + 40 * k), 255))
    img.paste(sol, (0, 0), sol)
    # grade em perspectiva no rodapé
    hy = 1640
    for i in range(0, 12):
        y = hy + int((i / 11) ** 2 * (H - hy))
        d.line((0, y, W, y), fill=(255, 43, 214, 120), width=2)
    for i in range(-14, 15):
        d.line((540 + i * 18, hy, 540 + i * 140, H), fill=(255, 43, 214, 110), width=2)
    # faixa da marca no topo
    d.rectangle((0, 0, W, 96), fill=(10, 0, 30, 200))
    d.line((0, 96, W, 96), fill=ROSA + (255,), width=4)
    if not comparar:
        x, y, w, h = JANELA
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(glow)
        dg.rounded_rectangle((x - 14, y - 14, x + w + 14, y + h + 14), 22, outline=ROSA + (255,), width=14)
        glow = glow.filter(ImageFilter.GaussianBlur(10)); img.paste(glow, (0, 0), glow)
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle((x - 8, y - 8, x + w + 8, y + h + 8), 16, fill=(0, 0, 0, 255), outline=ROSA + (255,), width=6)
        x0, y0, x1, y1 = PAINEL
        d.rounded_rectangle((x0, y0, x1, y1), 34, fill=(12, 0, 34, 215), outline=CIANO + (255,), width=5)
        d.rounded_rectangle((x0 + 12, y0 + 12, x1 - 12, y1 - 12), 26, outline=(0, 229, 255, 70), width=2)
    img.save(saida, quality=95)
    return saida


if __name__ == "__main__":
    import sys
    fundo(sys.argv[1] if len(sys.argv) > 1 else "/tmp/estudio.png")


# ---------- versão 16:9 para o vídeo longo ----------
JANELA_L = (40, 196, 1296, 729)     # gameplay
PAINEL_L = (1372, 196, 1880, 925)   # painel de informação à direita


def fundo_longo(saida):
    saida = Path(saida); w, h = 1920, 1080
    img = Image.new("RGB", (w, h)); px = img.load()
    for y in range(h):
        k = y / h
        for x in range(w):
            px[x, y] = (int(26 + 80 * k), int(4 + 8 * k), int(66 + 40 * (1 - k)))
    d = ImageDraw.Draw(img, "RGBA")
    hy = 960
    for i in range(8):
        y = hy + int((i / 7) ** 2 * (h - hy)); d.line((0, y, w, y), fill=ROSA + (110,), width=2)
    for i in range(-20, 21):
        d.line((960 + i * 30, hy, 960 + i * 200, h), fill=ROSA + (90,), width=2)
    d.rectangle((0, 0, w, 168), fill=(10, 0, 30, 215)); d.line((0, 168, w, 168), fill=ROSA + (255,), width=4)
    x, y, ww, hh = JANELA_L
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dg = ImageDraw.Draw(glow)
    dg.rounded_rectangle((x - 12, y - 12, x + ww + 12, y + hh + 12), 20, outline=ROSA + (255,), width=12)
    glow = glow.filter(ImageFilter.GaussianBlur(9)); img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((x - 7, y - 7, x + ww + 7, y + hh + 7), 14, fill=(0, 0, 0, 255), outline=ROSA + (255,), width=5)
    d.rounded_rectangle(PAINEL_L, 28, fill=(12, 0, 34, 220), outline=CIANO + (255,), width=5)
    img.save(saida, quality=95)
    return saida
