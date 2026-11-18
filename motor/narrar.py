"""Gera a narração (voz de IA, Piper) de todas as seções do roteiro e as marcações por palavra.
Uso: python3 motor/narrar.py JOB_DIR"""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from comum import RAIZ, dur, ler_json
from transcrever import transcrever

VOZ = RAIZ / "motor" / "modelos" / "en_US-ryan-high.onnx"


def falar(texto, saida):
    subprocess.run(["python3", "-m", "piper", "-m", str(VOZ), "--sentence-silence", "0.35", "--length-scale", "1.1",
                    "-f", str(saida)], input=texto.encode(), check=True, capture_output=True)


def alinhar(texto, palavras):
    """Troca as palavras reconhecidas pelo texto exato do roteiro (mantendo os tempos), para a legenda sair sem erros."""
    import difflib, re
    roteiro = texto.split()
    n = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    a, b = [n(w) for w in roteiro], [n(w["w"]) for w in palavras]
    out = [dict(w) for w in palavras]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace") and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                out[j1 + k]["w"] = roteiro[i1 + k]
    return out


def main(job):
    job = Path(job); r = ler_json(job / "roteiro.json")
    voz = job / "voz"; voz.mkdir(exist_ok=True)
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
    nomes = " ".join(r.get("nomes_proprios", []))
    secoes = (r.get("longo") or {}).get("secoes", [])   # Short urgente: "longo": null
    itens = [(s["id"], s["texto"]) for s in secoes] + [(s["id"], s["narracao"]) for s in r["shorts"]]
    tempos = {}
    for sid, texto in itens:
        wav = voz / f"{sid}.wav"
        falar(texto, wav)
        tr = transcrever(wav, "en", prompt=nomes, modelo=m)
        tempos[sid] = {"dur": dur(wav), "palavras": alinhar(texto, tr["palavras"])}
        print("voz", sid, round(tempos[sid]["dur"], 1), flush=True)
    json.dump(tempos, open(voz / "tempos.json", "w"))
    total = sum(tempos[s["id"]]["dur"] for s in secoes)
    print(f"narração do longo: {total/60:.1f} min")
    for s in r["shorts"]:
        print(f"short {s['id']}: {tempos[s['id']]['dur']:.1f}s de narração")


if __name__ == "__main__":
    main(sys.argv[1])
