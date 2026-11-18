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
    raise RuntimeError("todas as IAs grátis falharam: " + str(ultimo))


if __name__ == "__main__":
    print(gerar("Say hi in 5 words."))
