"""Kit de divulgação para grupos de Facebook (imagem 1200x630 + legendas em inglês + link do vídeo).
Gera/atualiza divulgar/README.md (mais recente primeiro) e as imagens em divulgar/img/.
Usa as entradas de estado/publicacoes.json que já têm video_id e "fb_textos" (lista de 2–3 variações).
Uso: python3 motor/divulgar.py"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
from comum import FONTES, RAIZ

EST = RAIZ / "estado" / "publicacoes.json"
DIV = RAIZ / "divulgar"; IMG = DIV / "img"
REPO_RAW = "https://raw.githubusercontent.com/auraxmusicoficial/arklyon-clips/main/divulgar/img"


def imagem(vid, saida, selo="▶ WATCH NOW"):
    src = Path(f"/tmp/{vid}.jpg")
    subprocess.run(["curl", "-sS", "-o", str(src), f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"], check=True)
    th = Image.open(src).convert("RGB")
    W, H = 1200, 630
    bg = th.resize((W, int(W * th.height / th.width)))
    canvas = Image.new("RGB", (W, H), (20, 6, 35))
    canvas.paste(bg, (0, (H - bg.height) // 2))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(str(FONTES / "Anton-Regular.ttf"), 44)
    tw = d.textlength(selo, font=f)
    d.rounded_rectangle([W - tw - 70, H - 96, W - 24, H - 26], radius=16, fill=(255, 32, 32), outline=(0, 0, 0), width=5)
    d.text((W - tw - 47, H - 92), selo, font=f, fill=(255, 255, 255))
    canvas.save(saida, quality=92)


def main():
    plano = json.loads(EST.read_text()) if EST.exists() else []
    IMG.mkdir(parents=True, exist_ok=True)
    novos = sorted([p for p in plano if p.get("video_id") and p.get("fb_textos") and not p.get("fb_feito")],
                   key=lambda p: p["quando"], reverse=True)
    if not novos:
        print("nada novo para divulgar"); return
    blocos = []
    for p in novos:
        vid = p["video_id"]; link = f"https://youtu.be/{vid}"
        imagem(vid, IMG / f"{vid}.jpg")
        b = [f"## {p['yt_title']}", f"_Publicado: {p['quando'][:16].replace('T', ' ')}_", "",
             f"![imagem]({REPO_RAW}/{vid}.jpg)", "",
             "Toque e segure a imagem para salvar. Use uma legenda diferente em cada grupo:", ""]
        for i, t in enumerate(p["fb_textos"], 1):
            b += [f"**Opção {i}**", "```", f"{t.strip()}\n\n▶️ {link}", "```", ""]
        blocos.append("\n".join(b)); p["fb_feito"] = True
    antigo = (DIV / "README.md").read_text(encoding="utf-8").split("\n---\n", 1)[-1] if (DIV / "README.md").exists() else ""
    topo = ("# 📣 Kit de divulgação — grupos de Facebook\n\n"
            "Regras para não ser bloqueado: leia as regras de cada grupo (muitos só aceitam divulgação em dias específicos), "
            "poste em no máximo 3–5 grupos por dia, use legendas diferentes e responda quem comentar.\n")
    (DIV / "README.md").write_text(topo + "\n---\n" + "\n\n---\n\n".join(blocos) + ("\n\n---\n\n" + antigo if antigo.strip() else ""),
                                   encoding="utf-8")
    EST.write_text(json.dumps(plano, ensure_ascii=False, indent=1))
    print(f"{len(novos)} vídeo(s) adicionados ao kit de divulgação")


if __name__ == "__main__":
    main()
