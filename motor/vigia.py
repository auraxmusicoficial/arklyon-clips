"""Vigia de notícias de GTA 6 SEM Claude: Groq (gpt-oss) com busca na web embutida, grátis.
Procura notícias das últimas ~6 h, compara com estado/noticias.json e, se houver notícia GRANDE e NOVA, registra
em estado/noticias.json (urgente: true, produzido: false) e avisa o Felipe no ntfy. A produção diária usa isso como
tema prioritário (e, depois da migração, o robô produz o Short urgente sozinho)."""
import json, os, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ

EST = RAIZ / "estado" / "noticias.json"
URL = "https://api.groq.com/openai/v1/chat/completions"
BRT = timezone(timedelta(hours=-3))


def buscar(pergunta, modelo="openai/gpt-oss-20b"):
    corpo = {"model": modelo, "tools": [{"type": "browser_search"}], "reasoning_effort": "low",
             "messages": [{"role": "user", "content": pergunta}]}
    for t in range(3):
        try:
            req = urllib.request.Request(URL, json.dumps(corpo).encode(), {
                "Authorization": "Bearer " + os.environ["GROQ_KEY"], "Content-Type": "application/json", "User-Agent": "vault-clips"})
            return json.load(urllib.request.urlopen(req, timeout=170))["choices"][0]["message"]["content"]
        except Exception as e:
            print("vigia: tentativa falhou:", e); time.sleep(20)
            modelo = "openai/gpt-oss-120b"
    return ""


def main():
    vistas = json.loads(EST.read_text()) if EST.exists() else []
    recentes = [v.get("titulo", "") for v in vistas[-40:]]
    hoje = datetime.now(BRT).strftime("%B %d, %Y")
    txt = buscar(
        f"Today is {hoje}. Search the web for GTA 6 (Grand Theft Auto VI) NEWS published in the last 6 hours "
        f"(official Rockstar announcements, patches/updates, records, major discoveries, big controversies). "
        f"Ignore guides/tips, rumors without a reliable source, and anything older than 24 hours. "
        f"Already covered (do NOT repeat): {json.dumps(recentes)[:2500]}\n"
        f"Answer ONLY with JSON: {{\"noticias\": [{{\"titulo\": \"short headline\", \"fonte\": \"site\", \"url\": \"...\", "
        f"\"quando\": \"date/time\", \"grande\": true/false, \"porque\": \"one line\"}}]}} — 'grande' = would most GTA 6 players "
        f"care today (official news, update, record, huge discovery). Max 5 items. Empty list if nothing new.")
    try:
        ini, fim = txt.index("{"), txt.rindex("}") + 1
        nots = json.loads(txt[ini:fim]).get("noticias", [])
    except Exception:
        print("vigia: resposta sem JSON"); return []
    agora = datetime.now(BRT).isoformat(timespec="minutes")
    novas = [n for n in nots if n.get("titulo") and n["titulo"] not in recentes]
    for n in novas:
        vistas.append({**n, "visto": agora, "urgente": bool(n.get("grande")), "produzido": False, "via": "robo-groq"})
    EST.write_text(json.dumps(vistas[-300:], ensure_ascii=False, indent=1))
    grandes = [n for n in novas if n.get("grande")]
    msgs = []
    if grandes and os.environ.get("NTFY_TOPIC"):
        corpo = "Notícia grande de GTA 6 (o robô vai usar como tema prioritário):\n" + "\n".join(
            f"- {n['titulo']} ({n.get('fonte', '')})" for n in grandes[:3])
        urllib.request.urlopen(urllib.request.Request(f"https://ntfy.sh/{os.environ['NTFY_TOPIC']}", corpo.encode(),
                                                      {"Title": "HQ Vault Clips - noticia"}), timeout=30)
        msgs.append(f"📰 {len(grandes)} notícia(s) grande(s) de GTA 6 registrada(s)")
    print(f"vigia: {len(novas)} novas, {len(grandes)} grandes")
    return msgs


if __name__ == "__main__":
    main()
