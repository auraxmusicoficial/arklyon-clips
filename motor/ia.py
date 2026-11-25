"""IA grátis (sem gastar o Claude): Groq com troca automática de modelo quando um bate no limite.
Uso: from ia import gerar; texto = gerar("pergunta", sistema="...")
Precisa de GROQ_KEY no ambiente."""
import json, os, time, urllib.error, urllib.request

MODELOS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]   # do melhor para o reserva
URL = "https://api.groq.com/openai/v1/chat/completions"


def gerar(prompt, sistema="", max_tokens=2500, json_saida=False):
    msgs = ([{"role": "system", "content": sistema}] if sistema else []) + [{"role": "user", "content": prompt}]
    ultimo = None
    for modelo in MODELOS:
        corpo = {"model": modelo, "messages": msgs, "max_tokens": max_tokens, "temperature": 0.8}
        if modelo.startswith("openai/gpt-oss"):
            corpo["reasoning_effort"] = "low"
        if json_saida:
            corpo["response_format"] = {"type": "json_object"}
        for tentativa in range(2):
            req = urllib.request.Request(URL, json.dumps(corpo).encode(), {
                "Authorization": "Bearer " + os.environ["GROQ_KEY"], "Content-Type": "application/json", "User-Agent": "vault-clips"})
            try:
                out = json.load(urllib.request.urlopen(req, timeout=120))
                txt = (out["choices"][0]["message"].get("content") or "").strip()
                if txt:
                    return txt
                ultimo = "resposta vazia"
            except urllib.error.HTTPError as e:
                ultimo = f"{modelo}: HTTP {e.code} {e.read()[:200]!r}"
                if e.code == 429 and tentativa == 0:
                    time.sleep(20); continue
            except Exception as e:  # rede, timeout
                ultimo = f"{modelo}: {e}"
            break
    if os.environ.get("GEMINI_KEY"):   # reserva: Gemini (grátis, aceita textos bem maiores que o limite do Groq)
        for mod in ("gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.8-flash"):
            corpo = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                     "generationConfig": {"maxOutputTokens": max(4000, max_tokens * 2), "temperature": 0.8,
                                          **({"responseMimeType": "application/json"} if json_saida else {})}}
            if sistema:
                corpo["systemInstruction"] = {"parts": [{"text": sistema}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={os.environ['GEMINI_KEY']}"
            try:
                out = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(corpo).encode(),
                                                                              {"Content-Type": "application/json"}), timeout=180))
                txt = "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"]).strip()
                if txt:
                    return txt
            except Exception as e:
                ultimo = f"{mod}: {e}"
    raise RuntimeError("todas as IAs grátis falharam: " + str(ultimo))


if __name__ == "__main__":
    print(gerar("Say hi in 5 words."))
