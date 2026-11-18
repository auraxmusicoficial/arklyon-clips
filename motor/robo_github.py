"""Robô que roda de hora em hora no GitHub (grátis, sem gastar o Claude):
estreias/capas/tags/local/playlists no YouTube, vigia de vídeos escondidos, respostas a comentários (IA grátis),
kit de divulgação, relatório diário e avisos no celular (ntfy).
Lê os segredos de VAULT_SECRETS (JSON) — configurado em Settings → Secrets → Actions."""
import io, json, os, subprocess, sys, traceback, urllib.request
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
BRT = timezone(timedelta(hours=-3))
avisos = []


def avisar(msg, titulo="HQ Vault Clips"):
    topico = os.environ.get("NTFY_TOPIC")
    print("AVISO:", msg)
    if topico:
        try:
            urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + topico, msg.encode(), {"Title": titulo}), timeout=20)
        except Exception as e:
            print("ntfy falhou:", e)


def etapa(nome, func):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            r = func()
        saida = buf.getvalue(); print(f"== {nome}\n{saida}")
        return r, saida
    except Exception:
        saida = buf.getvalue(); print(f"== {nome} (ERRO)\n{saida}"); traceback.print_exc()
        avisos.append(f"{nome}: erro — {traceback.format_exc().strip().splitlines()[-1][:200]}")
        return None, saida


def main():
    s = json.loads(os.environ.get("VAULT_SECRETS", "{}"))
    for k, v in s.items():
        os.environ.setdefault(k, v)
    hora = datetime.now(BRT).hour

    import youtube_ajustes, comentarios, divulgar, relatorio
    _, out = etapa("YouTube: estreia, capa, tags, playlists", youtube_ajustes.main)
    if "AVISOS:" in out:
        avisos.append(out.split("AVISOS:", 1)[1].strip())
    n, _ = etapa("Comentários (IA grátis)", comentarios.auto)
    _, out = etapa("Kit de divulgação", divulgar.main)
    if "adicionados" in out:
        avisar("Kit de divulgação atualizado: github.com/auraxmusicoficial/arklyon-clips/blob/main/divulgar/README.md")
    if hora == 8:
        etapa("Relatório", relatorio.main)
    import sincronizar
    etapa("Salvar no GitHub", lambda: sincronizar.main(f"robô do GitHub: ajustes {datetime.now(BRT):%d/%m %Hh}"))
    if avisos:
        avisar("⚠️ " + "\n".join(avisos)[:1500])
    elif n:
        print(f"{n} comentário(s) respondido(s)")


if __name__ == "__main__":
    main()
