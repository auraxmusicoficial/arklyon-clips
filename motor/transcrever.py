"""Transcreve um áudio/vídeo com marcação por palavra.  Uso: python3 motor/transcrever.py ENTRADA SAIDA.json [idioma]"""
import json, subprocess, sys
import numpy as np


def carregar(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def transcrever(entrada, idioma=None, prompt=None, modelo=None):
    from faster_whisper import WhisperModel
    m = modelo or WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
    segs, info = m.transcribe(carregar(entrada), language=idioma, word_timestamps=True, vad_filter=True, initial_prompt=prompt)
    S, Wd = [], []
    for s in segs:
        S.append({"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip()})
        for w in s.words or []:
            Wd.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})
    return {"idioma": info.language, "segmentos": S, "palavras": Wd}


if __name__ == "__main__":
    r = transcrever(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else None)
    json.dump(r, open(sys.argv[2], "w"), ensure_ascii=False)
    with open(sys.argv[2].replace(".json", ".txt"), "w") as f:
        for s in r["segmentos"]:
            f.write(f"[{s['s']:.0f}-{s['e']:.0f}] {s['t']}\n")
    print("ok", r["idioma"], len(r["segmentos"]), "trechos")
