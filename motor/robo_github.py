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


def vigiar_buffer():
    """Avisa (uma vez por post) quando um post do Buffer falhou."""
    k = os.environ.get("BUFFER_KEY")
    if not k:
        return
    def g(q, v=None):
        r = urllib.request.Request("https://api.buffer.com", json.dumps({"query": q, "variables": v or {}}).encode(),
                                   {"Authorization": "Bearer " + k, "Content-Type": "application/json", "User-Agent": "vault"})
        return json.load(urllib.request.urlopen(r, timeout=30))
    org = g("{ account { organizations { id } } }")["data"]["account"]["organizations"][0]["id"]
    out = g("query($o:OrganizationId!){ posts(input:{organizationId:$o, filter:{status:[error]}}, first:30)"
            "{ edges{ node{ id dueAt channelService text error { message } } } } }", {"o": org})
    est = Path(__file__).resolve().parent.parent / "estado" / "buffer_falhas.json"
    vistos = set(json.loads(est.read_text())) if est.exists() else set()
    novos = [e["node"] for e in out.get("data", {}).get("posts", {}).get("edges", []) if e["node"]["id"] not in vistos]
    for n in novos:
        quando = datetime.fromisoformat(n["dueAt"].replace("Z", "+00:00")).astimezone(BRT).strftime("%d/%m %Hh%M")
        motivo = (n.get("error") or {}).get("message", "")[:160]
        avisos.append(f"Post do Buffer FALHOU ({n['channelService']}, {quando}): {n['text'][:60]}… — {motivo}")
        vistos.add(n["id"])
    est.write_text(json.dumps(sorted(vistos)))
    print(len(novos), "falha(s) nova(s)")


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
    des = Path(__file__).resolve().parent.parent / "estado" / "desempenho.json"
    ultimo = json.loads(des.read_text()).get("historico", [{}])[-1].get("data") if des.exists() else None
    if ultimo != datetime.now(BRT).strftime("%Y-%m-%d") or hora == 20:   # 1x de manhã + 1x à noite
        etapa("Relatório", relatorio.main)
        import aprender
        etapa("Aprendizados (IA grátis)", aprender.main)
    _, out = etapa("Buffer: posts com falha", vigiar_buffer)
    import sincronizar
    etapa("Salvar no GitHub", lambda: sincronizar.main(f"robô do GitHub: ajustes {datetime.now(BRT):%d/%m %Hh}"))
    if avisos:
        avisar("⚠️ " + "\n".join(avisos)[:1500])
    elif n:
        print(f"{n} comentário(s) respondido(s)")


if __name__ == "__main__":
    main()
