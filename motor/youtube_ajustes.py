"""Ajustes no YouTube depois que o Buffer sobe o vídeo como NÃO LISTADO (90 min antes do horário):
 1. título, descrição completa, tags, categoria Gaming, idioma inglês e local de gravação (EUA);
 2. capa personalizada;
 3. confere bloqueios de direitos autorais (regionRestriction) e avisa;
 4. programa a estreia pública no horário do plano (privado + publishAt) — ou publica já, se o horário passou;
 5. coloca o vídeo na playlist do tema (motor/playlists.py);
 6. depois de público, posta a pergunta como 1º comentário.
Uso: YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... python3 motor/youtube_ajustes.py"""
import json, os, subprocess, sys, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

EST = RAIZ / "estado" / "publicacoes.json"
LOCAL_EUA = {"locationDescription": "United States", "location": {"latitude": 39.8283, "longitude": -98.5795}}


def token():
    d = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    out = subprocess.run(["curl", "-sS", "https://oauth2.googleapis.com/token", "-d", d], capture_output=True, text=True).stdout
    return json.loads(out)["access_token"]


def api(tok, method, path, body=None):
    cmd = ["curl", "-sS", "-X", method, "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: application/json",
           "https://www.googleapis.com/youtube/v3/" + path]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout or "{}")


def enviar_capa(tok, vid, url):
    img = "/tmp/capa.jpg"
    if (RAIZ / url).is_file():  # caminho local no repositório (ex.: publicar/AAAA-MM-DD/thumb_longo.jpg)
        img = str(RAIZ / url)
    else:
        subprocess.run(["curl", "-sSL", "-o", img, url], check=True)
    out = subprocess.run(["curl", "-sS", "-X", "POST", "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: image/jpeg",
                          "--data-binary", f"@{img}", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}"],
                         capture_output=True, text=True).stdout
    return "error" not in out, out[:300]


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def main():
    if not EST.exists():
        print("nada a ajustar"); return
    plano = json.loads(EST.read_text()); agora = datetime.now(timezone.utc)
    vigiar = [p for p in plano if p.get("video_id") and p["ajustado"] is True and not p.get("publico_ok")
              and datetime.fromisoformat(p["quando"]) + timedelta(minutes=15) <= agora]
    pend = [p for p in plano if (not p["ajustado"] and datetime.fromisoformat(p.get("upload", p["quando"])) <= agora)
            or (p["ajustado"] is True and p.get("comentario") and not p.get("comentou")
                and datetime.fromisoformat(p["quando"]) <= agora)]
    if not pend and not vigiar:
        print("nada pendente"); return
    tok = token()
    avisos = []
    # vigia: vídeo que já devia estar público mas ficou não listado/privado (ex.: estreia não aplicada) → publica
    for p in vigiar:
        it = api(tok, "GET", f"videos?part=status&id={p['video_id']}").get("items", [])
        if not it:
            continue
        st = it[0]["status"]
        if st.get("privacyStatus") != "public":
            rs = api(tok, "PUT", "videos?part=status", {"id": p["video_id"], "status": {
                "privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True}})
            avisos.append(f"'{p['yt_title']}' estava {st.get('privacyStatus')} depois do horário — "
                          + ("publiquei agora" if "error" not in rs else f"erro ao publicar: {rs['error'].get('message')}"))
        else:
            p["publico_ok"] = True
    up = api(tok, "GET", "channels?part=contentDetails&mine=true")["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids = api(tok, "GET", f"playlistItems?part=snippet&maxResults=50&playlistId={up}").get("items", [])
    por_titulo = {norm(v["snippet"]["title"]): v["snippet"]["resourceId"]["videoId"] for v in vids}
    for p in pend:
        vid = p.get("video_id") or por_titulo.get(norm(p["yt_title"]))
        if not vid:
            if agora - datetime.fromisoformat(p["quando"]) > timedelta(days=2):
                p["ajustado"] = "nao_encontrado"; avisos.append(f"não encontrei no YouTube: {p['yt_title']}")
            print("ainda não apareceu:", p["yt_title"]); continue
        if p["ajustado"] is not True:
            v = api(tok, "GET", f"videos?part=status,contentDetails&id={vid}")["items"][0]
            corpo = {"id": vid,
                     "snippet": {"title": p["yt_title"], "description": p["descricao"][:4900],
                                 "tags": [t[:30] for t in p["tags"]][:30], "categoryId": "20",
                                 "defaultLanguage": "en", "defaultAudioLanguage": "en"},
                     "recordingDetails": LOCAL_EUA}
            res = api(tok, "PUT", "videos?part=snippet,recordingDetails", corpo)
            if "error" in res:  # se o local for recusado, salva ao menos os metadados
                corpo.pop("recordingDetails")
                res = api(tok, "PUT", "videos?part=snippet", corpo)
            ok_capa, msg = enviar_capa(tok, vid, p["thumb"])
            bloqueio = v.get("contentDetails", {}).get("regionRestriction")
            if bloqueio:
                avisos.append(f"⚠️ '{p['yt_title']}' tem bloqueio por direitos autorais: {bloqueio}")
            estreia = datetime.fromisoformat(p["quando"])
            status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "embeddable": True}
            if estreia > agora + timedelta(minutes=10):
                status = {"privacyStatus": "private", "publishAt": estreia.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                          "selfDeclaredMadeForKids": False, "embeddable": True}
            rs = api(tok, "PUT", "videos?part=status", {"id": vid, "status": status})
            p["ajustado"] = True; p["video_id"] = vid
            if not p.get("na_playlist"):
                from playlists import adicionar
                p["na_playlist"] = adicionar(tok, vid, p.get("playlist") or ("shorts" if p.get("tipo") == "short" else "news"))
            print(f"ajustado {vid} | metadados={'ok' if 'error' not in res else res['error'].get('message')} | "
                  f"capa={'ok' if ok_capa else msg} | estreia={status.get('publishAt', 'agora')} "
                  f"| status={'ok' if 'error' not in rs else rs['error'].get('message')}")
            if "error" in res or "error" in rs or not ok_capa:
                avisos.append(f"erro ao ajustar '{p['yt_title']}' — veja o log")
        if p.get("comentario") and not p.get("comentou") and datetime.fromisoformat(p["quando"]) <= agora:
            c = api(tok, "POST", "commentThreads?part=snippet",
                    {"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": p["comentario"]}}}})
            p["comentou"] = "error" not in c
            print("comentário:", "ok" if p["comentou"] else c.get("error", {}).get("message"))
    EST.write_text(json.dumps(plano, ensure_ascii=False, indent=1))
    if avisos:
        print("AVISOS:\n" + "\n".join(avisos))


if __name__ == "__main__":
    main()
