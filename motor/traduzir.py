"""Traduções para alcançar público de fora (dica do GregoBeto — recurso oficial "Idiomas" do YouTube).
- titulo_desc(titulo, desc) -> {"es": {...}, "pt": {...}}  (usa Groq; Gemini de reserva)
- srt(texto_srt, lingua) -> SRT traduzido mantendo os tempos (usa Gemini; Groq de reserva)
- enviar_legenda(tok, video_id, lingua, nome, srt_texto)  (captions.insert — 400 de cota cada)"""
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

LINGUAS = {"es": "Spanish (Latin America)", "pt": "Brazilian Portuguese"}
NOMES = {"en": "English", "es": "Español", "pt": "Português"}


def _gemini(prompt, max_tokens=12000):
    k = os.environ.get("GEMINI_KEY")
    if not k:
        raise RuntimeError("sem GEMINI_KEY")
    for m in ("gemini-3.8-flash", "gemini-3-flash-preview", "gemini-flash-latest"):
        try:
            corpo = {"contents": [{"parts": [{"text": prompt}]}],
                     "generationConfig": {"maxOutputTokens": max_tokens, "responseMimeType": "application/json"}}
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}",
                                         json.dumps(corpo).encode(), {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=240))
            return json.loads("".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]))
        except Exception as e:
            ultimo = e
    raise RuntimeError(f"Gemini falhou: {ultimo}")


def _json(prompt, max_tokens=4000, preferir="groq"):
    ordem = ["groq", "gemini"] if preferir == "groq" else ["gemini", "groq"]
    erro = None
    for q in ordem:
        try:
            if q == "gemini":
                return _gemini(prompt, max_tokens)
            if os.environ.get("GROQ_KEY"):
                from ia import gerar
                return json.loads(gerar(prompt, json_saida=True, max_tokens=max_tokens))
        except Exception as e:
            erro = e
    raise RuntimeError(f"tradução falhou: {erro}")


def titulo_desc(titulo, desc):
    p = ("Translate this YouTube video title and description about GTA 6 into "
         + " and ".join(f"{v} (key \"{k}\")" for k, v in LINGUAS.items())
         + ". Keep it natural and catchy for gamers in that language, keep emojis, links, hashtags, timestamps and the name "
           "\"GTA 6\" unchanged, title max 100 characters. Reply ONLY JSON: {\"es\": {\"title\": \"\", \"description\": \"\"}, "
           f"\"pt\": {{\"title\": \"\", \"description\": \"\"}}}}\n\nTITLE: {titulo}\n\nDESCRIPTION:\n{desc[:3500]}")
    d = _json(p, max_tokens=4000)
    return {k: {"title": d[k]["title"][:100], "description": d[k]["description"][:4900]} for k in LINGUAS if k in d}


def srt(texto, lingua):
    blocos = [b for b in texto.strip().split("\n\n") if b.strip()]
    cab, linhas = [], []
    for b in blocos:
        partes = b.split("\n", 2)
        cab.append(partes[:2]); linhas.append(partes[2] if len(partes) > 2 else "")
    saida = []
    for i in range(0, len(linhas), 120):
        lote = linhas[i:i + 120]
        p = (f"Translate each subtitle line of a GTA 6 YouTube video from English into {LINGUAS[lingua]}. Natural, short, gamer tone. "
             "Keep \"GTA 6\", character and place names. Return ONLY JSON {\"lines\": [...]} with EXACTLY "
             f"{len(lote)} strings in the same order.\n\n" + json.dumps(lote, ensure_ascii=False))
        r = _json(p, max_tokens=12000, preferir="gemini").get("lines", [])
        if len(r) != len(lote):
            raise RuntimeError(f"tradução da legenda veio com {len(r)} linhas em vez de {len(lote)}")
        saida += r
    return "".join(f"{c[0]}\n{c[1]}\n{t}\n\n" for c, t in zip(cab, saida))


def enviar_legenda(tok, video_id, lingua, srt_texto):
    meta = json.dumps({"snippet": {"videoId": video_id, "language": lingua, "name": NOMES.get(lingua, lingua), "isDraft": False}})
    corpo = (f"--fronteira\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
             f"--fronteira\r\nContent-Type: application/octet-stream\r\n\r\n{srt_texto}\r\n--fronteira--\r\n").encode("utf-8")
    req = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/captions?part=snippet&uploadType=multipart", corpo,
                                 {"Authorization": f"Bearer {tok}", "Content-Type": "multipart/related; boundary=fronteira"})
    return json.load(urllib.request.urlopen(req, timeout=120)).get("id")
