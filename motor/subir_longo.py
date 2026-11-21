"""Sobe o vídeo longo DIRETO pela API do YouTube (sem gastar o limite do Metricool) e agenda a estreia pública.
Teste A/B (dica do Lucas Roudi): alterna dia sim, dia não entre AVISAR e NÃO AVISAR os inscritos
(notifySubscribers). O relatório compara os dois grupos.
Uso: python3 motor/subir_longo.py JOB_DIR DATA(YYYY-MM-DD) COMMIT_SHA [HH:MM, padrão 12:00]
Precisa de YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Se falhar, sai com código 1 → use o Metricool (plano B)."""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from youtube_ajustes import token

RAIZ = Path(__file__).resolve().parent.parent
BRT = timezone(timedelta(hours=-3))


def main(job, data, sha, hora="12:00"):
    job = Path(job)
    r = json.loads((job / "roteiro.json").read_text(encoding="utf-8"))
    L = r["longo"]
    video = job / "saida" / "longo.mp4"
    capa = job / "saida" / "thumb_longo.jpg"
    caps = job / "saida" / "capitulos.txt"
    quando = datetime.fromisoformat(f"{data}T{hora}:00").replace(tzinfo=BRT)
    notificar = quando.toordinal() % 2 == 0          # alterna por dia
    desc = L["descricao"].strip()
    if caps.exists():
        desc += "\n\n" + caps.read_text(encoding="utf-8").strip()
    if r.get("credito_fonte"):
        desc += f"\n\nFootage: {r['credito_fonte']}"
    desc += "\n\n🔔 Subscribe for daily GTA 6 secrets, tips & news: https://www.youtube.com/@hqvaultclips?sub_confirmation=1"
    if L.get("hashtags"):
        desc += "\n\n" + " ".join(L["hashtags"][:3])
    meta = {"snippet": {"title": L["titulo"][:100], "description": desc[:4900], "tags": L.get("tags", [])[:30],
                        "categoryId": "20", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "publishAt": quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "selfDeclaredMadeForKids": False, "publicStatsViewable": True}}
    tok = token(); tam = video.stat().st_size
    url = ("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
           f"&notifySubscribers={'true' if notificar else 'false'}")
    h = subprocess.run(["curl", "-sS", "-D", "-", "-o", "/dev/null", "-X", "POST", url,
                        "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: application/json; charset=UTF-8",
                        "-H", "X-Upload-Content-Type: video/mp4", "-H", f"X-Upload-Content-Length: {tam}",
                        "-d", json.dumps(meta)], capture_output=True, text=True).stdout
    loc = [l.split(":", 1)[1].strip() for l in h.splitlines() if l.lower().startswith("location:")]
    if not loc:
        raise SystemExit("YouTube não abriu o envio: " + h[-400:])
    out = subprocess.run(["curl", "-sS", "-X", "PUT", loc[0], "-H", "Content-Type: video/mp4", "--data-binary", f"@{video}"],
                         capture_output=True, text=True).stdout
    vid = json.loads(out).get("id")
    if not vid:
        raise SystemExit("envio falhou: " + out[-400:])
    if capa.exists():
        subprocess.run(["curl", "-sS", "-X", "POST", f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                        "-H", f"Authorization: Bearer {tok}", "-H", "Content-Type: image/jpeg", "--data-binary", f"@{capa}"],
                       capture_output=True, text=True)
    base = f"https://raw.githubusercontent.com/auraxmusicoficial/arklyon-clips/{sha}/publicar/{data}"
    entrada = {"tipo": "longo", "quando": quando.isoformat(), "upload": datetime.now(BRT).isoformat(), "yt_title": L["titulo"][:100],
               "descricao": desc, "tags": L.get("tags", []), "thumb": f"{base}/thumb_longo.jpg", "video_id": vid,
               "ajustado": False, "comentario": L.get("comentario_youtube", ""), "fb_textos": L.get("fb_textos", []),
               "playlist": L.get("playlist", "news"), "via": "api", "notificar": notificar}
    est = RAIZ / "estado" / "publicacoes.json"
    todos = json.loads(est.read_text()) if est.exists() else []
    est.write_text(json.dumps(todos + [entrada], ensure_ascii=False, indent=1))
    print(f"longo enviado direto: https://youtu.be/{vid} — estreia {quando:%d/%m %H:%M} — "
          f"{'COM' if notificar else 'SEM'} aviso aos inscritos (teste A/B)")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[2], a[3] if len(a) > 3 else "12:00")
