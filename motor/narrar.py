"""Gera a narração de todas as seções do roteiro e as marcações por palavra.
Voz principal: Gemini TTS, voz "Charon" (escolhida pelo Felipe em 20/11) — grátis com GEMINI_KEY.
Plano B automático: Piper (en_US-ryan). Um vídeo nunca mistura vozes: o longo inteiro é Gemini ou inteiro Piper;
cada Short decide sozinho.
Uso: python3 motor/narrar.py JOB_DIR"""
import base64, json, os, re, subprocess, sys, time, urllib.error, urllib.request, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ, dur, ler_json
from transcrever import transcrever

VOZ = RAIZ / "motor" / "modelos" / "en_US-ryan-high.onnx"
VOZ_GEMINI = os.environ.get("VOZ_GEMINI", "Charon")
MODELOS_TTS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]
PAUSA_API = 21          # o grátis aceita poucas chamadas por minuto
MAX_PALAVRAS_BLOCO = 650
MIN_SHORT = 59.8        # segundos de narração mínimos num Short (com abertura, fim e capa passa de 61 s)
_ultima = [0.0]


def falar_piper(texto, saida):
    subprocess.run(["python3", "-m", "piper", "-m", str(VOZ), "--sentence-silence", "0.35", "--length-scale", "1.1",
                    "-f", str(saida)], input=texto.encode(), check=True, capture_output=True)


def falar_gemini(texto, saida):
    k = os.environ.get("GEMINI_KEY")
    if not k:
        raise RuntimeError("sem GEMINI_KEY")
    corpo = {"contents": [{"parts": [{"text": texto}]}],
             "generationConfig": {"responseModalities": ["AUDIO"],
                                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOZ_GEMINI}}}}}
    erro = None
    for m in MODELOS_TTS:
        for tent in range(3):
            espera = PAUSA_API - (time.time() - _ultima[0])
            if espera > 0:
                time.sleep(espera)
            _ultima[0] = time.time()
            try:
                req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}",
                                             json.dumps(corpo).encode(), {"Content-Type": "application/json"})
                d = json.load(urllib.request.urlopen(req, timeout=300))
                pcm = base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
                tmp = Path(str(saida) + ".raw.wav")
                with wave.open(str(tmp), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
                # mesmo formato do resto da montagem; tira silêncio das pontas
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-af",
                                "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                                "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                                "-ar", "22050", "-ac", "1", str(saida)], check=True)
                tmp.unlink(missing_ok=True)
                return
            except urllib.error.HTTPError as e:
                erro = f"{m}: HTTP {e.code} {e.read()[:160]!r}"
                if e.code == 429 and tent < 2:
                    time.sleep(45); continue
                break
            except Exception as e:
                erro = f"{m}: {e}"
                if tent < 1:
                    continue
                break
    raise RuntimeError("Gemini TTS falhou: " + str(erro))


def alinhar(texto, palavras):
    """Troca as palavras reconhecidas pelo texto exato do roteiro (mantendo os tempos), para a legenda sair sem erros."""
    import difflib
    roteiro = texto.split()
    n = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    a, b = [n(w) for w in roteiro], [n(w["w"]) for w in palavras]
    out = [dict(w) for w in palavras]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace") and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                out[j1 + k]["w"] = roteiro[i1 + k]
    return out


def mapa_palavras(texto, palavras):
    """Para cada palavra do roteiro, o índice da palavra reconhecida correspondente (ou None)."""
    import difflib
    n = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    a, b = [n(w) for w in texto.split()], [n(w["w"]) for w in palavras]
    mp = [None] * len(a)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(min(i2 - i1, j2 - j1)):
                mp[i1 + k] = j1 + k
    return mp


def longo_gemini(secoes, voz, m, nomes):
    """Narra o longo em poucos blocos (economiza chamadas) e corta de volta por seção."""
    blocos, atual, n = [], [], 0
    for s in secoes:
        w = len(s["texto"].split())
        if atual and n + w > MAX_PALAVRAS_BLOCO:
            blocos.append(atual); atual, n = [], 0
        atual.append(s); n += w
    if atual:
        blocos.append(atual)
    for bi, bloco in enumerate(blocos):
        texto = "\n\n".join(s["texto"] for s in bloco)
        wav = voz / f"_bloco{bi}.wav"
        falar_gemini(texto, wav)
        tr = transcrever(wav, "en", prompt=nomes, modelo=m)["palavras"]
        mp = mapa_palavras(texto, tr)
        total = dur(wav); pos = 0; limites = []
        for s in bloco:
            k = len(s["texto"].split())
            ini = next((mp[i] for i in range(pos, pos + k) if mp[i] is not None), None)
            fim = next((mp[i] for i in range(pos + k - 1, pos - 1, -1) if mp[i] is not None), None)
            if ini is None or fim is None:
                raise RuntimeError(f"não consegui achar a seção {s['id']} no áudio")
            limites.append((tr[ini]["s"], tr[fim]["e"])); pos += k
        for i, s in enumerate(bloco):
            a = 0.0 if i == 0 else (limites[i - 1][1] + limites[i][0]) / 2
            b = total if i == len(bloco) - 1 else (limites[i][1] + limites[i + 1][0]) / 2
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(wav),
                            "-af", "afade=t=in:d=0.03,areverse,afade=t=in:d=0.05,areverse", "-ar", "22050", "-ac", "1",
                            str(voz / f"{s['id']}.wav")], check=True)
        wav.unlink(missing_ok=True)


def main(job):
    job = Path(job); r = ler_json(job / "roteiro.json")
    voz = job / "voz"; voz.mkdir(exist_ok=True)
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
    nomes = " ".join(r.get("nomes_proprios", []))
    secoes = (r.get("longo") or {}).get("secoes", [])   # Short urgente: "longo": null
    tempos, quem = {}, {}
    if secoes:
        try:
            longo_gemini(secoes, voz, m, nomes); quem["longo"] = f"Gemini ({VOZ_GEMINI})"
        except Exception as e:
            print("AVISO voz Gemini falhou no longo, usando Piper no longo inteiro:", e)
            for s in secoes:
                falar_piper(s["texto"], voz / f"{s['id']}.wav")
            quem["longo"] = "Piper"
    for s in r["shorts"]:
        try:
            w = voz / f"{s['id']}.wav"
            falar_gemini(s["narracao"], w)
            d = dur(w)
            if d < MIN_SHORT:   # o Short precisa passar de 60 s: desacelera um pouco a voz (até 12%) ou cai pro Piper
                fator = d / MIN_SHORT
                if fator < 0.88:
                    raise RuntimeError(f"narração curta demais ({d:.1f}s)")
                tmp = voz / f"{s['id']}_lento.wav"
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(w), "-af", f"atempo={fator:.3f}", str(tmp)], check=True)
                tmp.replace(w)
            quem[s["id"]] = f"Gemini ({VOZ_GEMINI})"
        except Exception as e:
            print(f"AVISO voz Gemini falhou no Short {s['id']}, usando Piper:", e)
            falar_piper(s["narracao"], voz / f"{s['id']}.wav"); quem[s["id"]] = "Piper"
    itens = [(s["id"], s["texto"]) for s in secoes] + [(s["id"], s["narracao"]) for s in r["shorts"]]
    for sid, texto in itens:
        wav = voz / f"{sid}.wav"
        tr = transcrever(wav, "en", prompt=nomes, modelo=m)
        tempos[sid] = {"dur": dur(wav), "palavras": alinhar(texto, tr["palavras"])}
        print("voz", sid, round(tempos[sid]["dur"], 1), flush=True)
    json.dump(tempos, open(voz / "tempos.json", "w"))
    total = sum(tempos[s["id"]]["dur"] for s in secoes)
    print(f"narração do longo: {total/60:.1f} min")
    for s in r["shorts"]:
        print(f"short {s['id']}: {tempos[s['id']]['dur']:.1f}s de narração")
    print("vozes usadas:", quem)


if __name__ == "__main__":
    main(sys.argv[1])
