"""O robô aprende com o próprio desempenho (grátis, sem gastar o Claude).
Lê estado/desempenho.json (gerado pelo relatorio.py), pede à IA grátis (Groq) para comparar os vídeos que mais
renderam com os que menos renderam e escreve estado/APRENDIZADOS.md — lido pela produção antes de criar
os vídeos do dia (títulos, ganchos, temas, capas, formato dos Shorts e dos longos)."""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

DES = RAIZ / "estado" / "desempenho.json"
OUT = RAIZ / "estado" / "APRENDIZADOS.md"
SISTEMA = ("You are a YouTube growth analyst for an English GTA 6 channel. Be concrete and practical. "
           "Base every conclusion ONLY on the data given; if the data is too small, say what to test next. "
           "Context: GTA 6 was RELEASED on November 19, 2026 — never suggest pre-launch/countdown titles; "
           "suggest titles for a game people are playing now (tips, secrets, records, changes, mistakes).")


def main():
    from ia import gerar
    d = json.loads(DES.read_text())
    vids = [v for v in d["videos"] if v["dias"] >= 0.12]   # a partir de ~3 h no ar
    if len(vids) < 4:
        print("poucos dados ainda"); return
    vids.sort(key=lambda v: -v["views_dia"])
    linhas = [f'{v["tipo"]} | {v["dur"]}s | {v["views"]} views | {v["views_dia"]}/day | {v["engaj"]}% engagement | posted {v["hora_brt"]}h BRT | "{v["titulo"]}"' for v in vids]
    hist = d.get("historico", [])[-8:]
    pedido = ("Channel videos sorted from best to worst (views per day):\n" + "\n".join(linhas) +
              "\n\nSubscribers/views history: " + json.dumps(hist) +
              "\n\nWrite in Brazilian Portuguese, in Markdown, max 350 words, with these sections:\n"
              "## O que está funcionando (padrões dos melhores: tipo de assunto, palavras do título, emoji, duração, horário)\n"
              "## O que evitar (padrões dos piores)\n"
              "## Fórmulas de título para amanhã (6 títulos-modelo em INGLÊS para Shorts e 2 para o vídeo longo, seguindo os padrões vencedores, sem inventar fatos — use [X] onde entra o fato do dia)\n"
              "## Ajustes no vídeo longo (como trazer os padrões vencedores dos Shorts para o longo: título, capa, gancho dos primeiros 30 s)\n"
              "## O que testar a seguir (1–2 testes)")
    txt = gerar(pedido, sistema=SISTEMA, max_tokens=2500)
    hoje = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    OUT.write_text(f"# Aprendizados automáticos do canal — {hoje}\n\n_Gerado pelo robô a partir do desempenho real dos vídeos. "
                   f"A produção DEVE aplicar isto no longo e nos Shorts do dia._\n\n{txt}\n", encoding="utf-8")
    print(txt[:600])


if __name__ == "__main__":
    main()
