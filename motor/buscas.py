"""O que as pessoas DIGITAM no YouTube sobre GTA 6 (autocompletar da busca, EUA, inglês) -> estado/BUSCAS.md.
Sem chave e sem custo. Ideia do vídeo 'Desconfuse' (26/11): os 10 primeiros vídeos de busca = as sugestões do autocompletar.
A produção usa: título do vídeo longo = a frase EXATA de uma sugestão; resposta logo no começo."""
import json, sys, urllib.parse, urllib.request
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

PREFIXOS = ["gta 6 how to", "gta 6 where", "gta 6 where to find", "gta 6 money", "gta 6 best", "gta 6 cheats",
            "gta 6 how to get", "gta 6 secret", "gta 6 safe code", "gta 6 fastest way", "gta 6 can you", "gta 6 mission"]


def sugestoes(q):
    u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "hl": "en", "gl": "us", "q": q})
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20))[1]
    except Exception as e:
        print("buscas:", q, e); return []


def main():
    usados = {p.get("yt_title", "").lower() for p in json.loads((RAIZ / "estado" / "publicacoes.json").read_text())} \
        if (RAIZ / "estado" / "publicacoes.json").exists() else set()
    L = [f"# Buscas reais no YouTube sobre GTA 6 (autocompletar, EUA) — {date.today().isoformat()}", "",
         "Use a frase EXATA como título do vídeo longo (com 1ª letra maiúscula). Resposta nos primeiros segundos + 2 dicas extras.",
         "Marcadas com ✓ = já temos vídeo parecido.", ""]
    todas = []
    for p in PREFIXOS:
        s = sugestoes(p)
        if not s:
            continue
        L.append(f"## {p}")
        for x in s[:10]:
            feito = any(x.lower() in u for u in usados)
            L.append(f"- {'✓ ' if feito else ''}{x}"); todas.append(x)
        L.append("")
    (RAIZ / "estado" / "BUSCAS.md").write_text("\n".join(L), encoding="utf-8")
    print("ok BUSCAS.md", len(todas), "buscas")


if __name__ == "__main__":
    main()
