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
    yt = [n for n in novos if n["channelService"] == "youtube" and "limit" in ((n.get("error") or {}).get("message", "").lower())]
    if yt:
        plano_b_youtube(yt)


def subir_direto(p):
    """Plano B quando o Buffer recusa um Short no YouTube: envia direto pela API do YouTube (grátis)."""
    import youtube_ajustes as ya
    m = p["thumb"].rsplit("/", 1)
    sid = m[1].replace("thumb_", "").replace(".jpg", "")
    url = f"{m[0]}/short_{sid}{'_yt' if p.get('formato_yt') == 'rapido' else ''}.mp4"
    arq = "/tmp/plano_b.mp4"
    subprocess.run(["curl", "-sSfL", "-o", arq, url], check=True)
    quando = datetime.fromisoformat(p["quando"])
    agora = datetime.now(timezone.utc)
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "publicStatsViewable": True}
    if quando > agora + timedelta(minutes=15):
        status["publishAt"] = quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        status["privacyStatus"] = "public"
    meta = {"snippet": {"title": p["yt_title"], "description": p["descricao"][:4900], "tags": p.get("tags", []),
                        "categoryId": "20", "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": status}
    tok = ya.token(); tam = os.path.getsize(arq)
    h = subprocess.run(["curl", "-sS", "-D", "-", "-o", "/dev/null", "-X", "POST",
                        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                        "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: application/json; charset=UTF-8",
                        "-H", "X-Upload-Content-Type: video/mp4", "-H", f"X-Upload-Content-Length: {tam}",
                        "-d", json.dumps(meta)], capture_output=True, text=True).stdout
    loc = [l.split(":", 1)[1].strip() for l in h.splitlines() if l.lower().startswith("location:")][0]
    r = json.loads(subprocess.run(["curl", "-sS", "-X", "PUT", loc, "-H", "Content-Type: video/mp4", "--data-binary", f"@{arq}"],
                                  capture_output=True, text=True).stdout)
    return r["id"]


def plano_b_youtube(falhas):
    est = Path(__file__).resolve().parent.parent / "estado" / "publicacoes.json"
    plano = json.loads(est.read_text())
    mudou = False
    for n in falhas:
        p = next((x for x in plano if isinstance(x, dict) and x.get("tipo") == "short"
                  and (x.get("buffer") or {}).get("youtube") == n["id"]), None)
        if not p or p.get("yt_direto"):
            continue
        try:
            vid = subir_direto(p)
            p["yt_direto"] = vid; mudou = True
            avisos.append(f"✅ Plano B: '{p['yt_title'][:50]}' foi enviado direto pro YouTube (sem o Buffer).")
        except Exception as e:
            avisos.append(f"Plano B falhou para '{p['yt_title'][:50]}': {str(e)[:120]}")
    if mudou:
        est.write_text(json.dumps(plano, ensure_ascii=False, indent=1))


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
        import redes
        etapa("Desempenho por rede (YouTube x TikTok x Instagram)", redes.main)
        import controle
        etapa("Controle diário (posts de ontem)", controle.main)
        if hora < 20:   # resgate de flops 1x por dia (de manhã)
            import resgate
            _, out_r = etapa("Resgate de vídeos flopados (título novo)", resgate.main)
    sc_f = Path(__file__).resolve().parent.parent / "estado" / "segunda_chance_dia.txt"
    if 9 <= hora <= 11 and (not sc_f.exists() or sc_f.read_text().strip() != datetime.now(BRT).strftime("%Y-%m-%d")):
        import segunda_chance   # 1x por dia, de manhã (depois que a produção agendou o dia)
        msgs_sc, _ = etapa("Segunda chance (vídeo que bombou numa rede vai pras outras)", segunda_chance.main)
        sc_f.write_text(datetime.now(BRT).strftime("%Y-%m-%d"))
        if msgs_sc:
            avisos.extend(msgs_sc)
    _, out = etapa("Buffer: posts com falha", vigiar_buffer)
    import sincronizar
    etapa("Salvar no GitHub", lambda: sincronizar.main(f"robô do GitHub: ajustes {datetime.now(BRT):%d/%m %Hh}"))
    if avisos:
        avisar("⚠️ " + "\n".join(avisos)[:1500])
    elif n:
        print(f"{n} comentário(s) respondido(s)")


if __name__ == "__main__":
    main()
