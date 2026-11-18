"""Trilha sonora 100% original (composta por código) no clima synthwave anos 80 / Vice City + efeitos sonoros.
Como é gerada aqui, não tem direitos de terceiros — nunca gera reivindicação de Content ID.
Uso:
  python3 motor/trilha.py musica SAIDA.wav SEGUNDOS [semente] [estilo]   # estilo: noite (padrão) | acao | sol
  python3 motor/trilha.py efeitos PASTA                                  # whoosh, impacto, riser, ding
  python3 motor/trilha.py mixar VOZ_OU_VIDEO MUSICA SAIDA [volume_db]    # música por baixo, abaixando quando a voz fala"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
ESTILOS = {   # bpm, progressão (tônica, menor?), brilho do filtro
    "noite": (98, [("A", 1), ("F", 0), ("C", 0), ("G", 0)], 1800),
    "acao": (118, [("E", 1), ("C", 0), ("D", 0), ("B", 1)], 2600),
    "sol": (104, [("F", 0), ("A", 1), ("D", 1), ("C", 0)], 2300),
}


def hz(nome, oit):
    return 440.0 * 2 ** ((NOTAS[nome] + 12 * (oit - 4) - 9) / 12)


def lp(x, fc, ordem=2):
    b, a = butter(ordem, min(fc, SR / 2 - 100) / (SR / 2), "low"); return lfilter(b, a, x)


def hp(x, fc, ordem=2):
    b, a = butter(ordem, fc / (SR / 2), "high"); return lfilter(b, a, x)


def saw(f, n, fase=0.0):
    t = (np.arange(n) * f / SR + fase) % 1.0; return 2 * t - 1


def env(n, a=0.005, d=0.1, s=0.6, r=0.05):
    e = np.ones(n) * s; ia, idd, ir = int(a * SR), int(d * SR), int(r * SR)
    ia = min(ia, n); e[:ia] = np.linspace(0, 1, ia)
    fim = min(n, ia + idd); e[ia:fim] = np.linspace(1, s, fim - ia)
    if ir and n > ir:
        e[-ir:] *= np.linspace(1, 0, ir)
    return e


def kick(n):
    t = np.arange(n) / SR; f = 50 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)


def snare(rng, n):
    t = np.arange(n) / SR
    corpo = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    ruido = hp(rng.standard_normal(n), 1200) * np.exp(-t * 9)
    return 0.5 * corpo + 0.6 * ruido


def hat(rng, n):
    t = np.arange(n) / SR; return hp(rng.standard_normal(n), 7000) * np.exp(-t * 60)


def acorde(raiz, menor):
    r = NOTAS[raiz]; return [r, r + (3 if menor else 4), r + 7]


def nota_hz(semi, oit):
    return 440.0 * 2 ** ((semi + 12 * (oit - 4) - 9) / 12)


def eco(x, atraso, fb=0.35, mix=0.35):
    d = int(atraso * SR); y = x.copy()
    for k in range(1, 4):
        if d * k < len(x):
            y[d * k:] += x[:-d * k] * (fb ** k) * mix
    return y


def musica(segundos, semente=7, estilo="noite"):
    rng = np.random.default_rng(semente)
    bpm, prog, brilho = ESTILOS.get(estilo, ESTILOS["noite"])
    if semente % 2:
        prog = prog[1:] + prog[:1]
    beat = 60 / bpm; barra = 4 * beat; nb = int(np.ceil(segundos / barra)) + 1
    N = int(nb * barra * SR) + SR
    L = np.zeros(N); R = np.zeros(N); bat = np.zeros(N); pump = np.ones(N)
    sb = int(beat * SR)
    for b in range(nb):
        raiz, menor = prog[b % 4]; ac = acorde(raiz, menor); i0 = int(b * barra * SR)
        secao = 0 if b < 2 else [1, 2, 2, 3][(b // 4) % 4]   # 0 intro leve, 1 cheio, 2 cheio + arp, 3 arp sem caixa
        # bateria
        for q in range(4):
            p = i0 + q * sb
            if secao != 0 or q % 2 == 0:
                k = kick(int(0.4 * SR)); bat[p:p + len(k)] += 0.9 * k
                pump[p:p + int(0.3 * SR)] = np.minimum(pump[p:p + int(0.3 * SR)], np.linspace(0.35, 1, int(0.3 * SR)))
            if q in (1, 3) and secao in (1, 2):  # caixa
                s_ = snare(rng, int(0.35 * SR)); bat[p:p + len(s_)] += 0.4 * s_
            for h in range(2):
                ph = p + h * sb // 2; hh = lp(hat(rng, int(0.05 * SR)), 11000); bat[ph:ph + len(hh)] += (0.08 if h else 0.045) * hh
        # baixo em colcheias (oitavas)
        for e in range(8):
            p = i0 + e * sb // 2; n = sb // 2
            f = nota_hz(ac[0], 2 if e % 2 == 0 else 3)
            x = lp(saw(f, n) + 0.5 * saw(f * 1.005, n), 700) * env(n, 0.003, 0.08, 0.5, 0.02)
            L[p:p + n] += 0.32 * x; R[p:p + n] += 0.32 * x
        # pad (acorde com serras desafinadas)
        n = int(barra * SR); pad = np.zeros(n)
        for s_ in ac:
            f = nota_hz(s_, 4)
            pad += saw(f * 0.997, n, rng.random()) + saw(f * 1.003, n, rng.random())
        pad = lp(pad, brilho * (0.6 if secao == 0 else 1.0)) * env(n, 0.35, 0.3, 0.8, 0.4)
        L[i0:i0 + n] += 0.07 * pad; R[i0:i0 + n] += 0.07 * np.roll(pad, 300)
        # arpejo em semicolcheias (seções 2 e 3)
        if secao >= 2:
            seq = [ac[0], ac[1], ac[2], ac[1] + 12, ac[2], ac[1], ac[0] + 12, ac[2]]
            for e in range(16):
                p = i0 + e * sb // 4; n2 = sb // 4
                f = nota_hz(seq[e % 8], 5)
                sq = np.sign(np.sin(2 * np.pi * f * np.arange(n2) / SR)) * env(n2, 0.002, 0.05, 0.3, 0.02)
                sq = lp(sq, 3200)
                (L if e % 2 else R)[p:p + n2] += 0.06 * sq
    L = eco(L * pump, beat * 0.75); R = eco(R * pump, beat * 0.5)
    mix = np.stack([L + bat, R + bat], 1)[: int(segundos * SR)]
    f = min(len(mix), 2 * SR)
    mix[:f] *= np.linspace(0, 1, f)[:, None]; mix[-f:] *= np.linspace(1, 0, f)[:, None]
    return (mix / (np.abs(mix).max() + 1e-9) * 0.89).astype(np.float32)


def efeitos():
    rng = np.random.default_rng(1); t = lambda s: np.arange(int(s * SR)) / SR
    out = {}
    n = int(0.7 * SR); x = rng.standard_normal(n); y = np.zeros(n)   # whoosh (varredura de filtro)
    for i in range(0, n, 512):
        fc = 300 + 6000 * np.sin(np.pi * i / n); y[i:i + 512] = lp(x[i:i + 512], fc)
    out["whoosh"] = y * np.sin(np.pi * np.arange(n) / n) ** 2
    tt = t(1.2); out["impacto"] = (np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 3)
                                   + 0.4 * lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 6))
    tt = t(1.5); out["riser"] = lp(rng.standard_normal(len(tt)), 8000) * (tt / tt[-1]) ** 2 * 0.6 + \
        0.3 * saw(1, len(tt)) * 0 + 0.25 * np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / tt[-1]) ** 2) / SR) * (tt / tt[-1])
    tt = t(1.0); out["ding"] = np.sin(2 * np.pi * 1318.5 * tt + 2.5 * np.sin(2 * np.pi * 2637 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 5)
    return {k: (v / np.abs(v).max() * 0.8).astype(np.float32) for k, v in out.items()}


def salvar(caminho, x):
    x = np.asarray(x); x = x[:, None] if x.ndim == 1 else x
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(pcm.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def mixar(voz, mus, saida, volume_db=-17):
    """Música por baixo da voz com 'ducking' (abaixa quando a narração fala). Se 'voz' for vídeo, mantém a imagem."""
    filtro = (f"[1:a]volume={volume_db}dB,aloop=loop=-1:size=2e9[m];"
              "[0:a]asplit=2[v][sc];"
              "[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[md];"
              "[v][md]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[a]")
    video = Path(voz).suffix.lower() in (".mp4", ".mov", ".mkv")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(voz), "-i", str(mus), "-filter_complex", filtro, "-map", "[a]"]
    cmd += (["-map", "0:v", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k"] if video else [])
    subprocess.run(cmd + [str(saida)], check=True)


def sonorizar(video, saida, marcas=(), estilo="noite", semente=7, volume_db=-16, ding=()):
    """Coloca a trilha original por baixo do vídeo (abaixa quando a voz fala) + whoosh/impacto nas `marcas`
    (segundos: trocas de capítulo/gancho) e 'ding' nos tempos de `ding`. Mantém a imagem (copy)."""
    import tempfile, json as _j
    tmp = Path(tempfile.mkdtemp())
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                             capture_output=True, text=True).stdout.strip())
    salvar(tmp / "m.wav", musica(d + 1, semente, estilo))
    fx = efeitos()
    for k, v in fx.items():
        salvar(tmp / f"{k}.wav", v)
    ent = ["-i", str(video), "-i", str(tmp / "m.wav")]
    fc = (f"[1:a]volume={volume_db}dB[m];[0:a]asplit=2[v][sc];"
          "[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[md];")
    mixs = ["[v]", "[md]"]; i = 2
    for tm in [m for m in marcas if 0.3 < m < d - 1][:30]:
        for nome, vol, desloc in (("whoosh", 0.45, -0.45), ("impacto", 0.35, 0.05)):
            ent += ["-i", str(tmp / f"{nome}.wav")]; ms = max(0, int((tm + desloc) * 1000))
            fc += f"[{i}:a]adelay={ms}|{ms},volume={vol}[f{i}];"; mixs.append(f"[f{i}]"); i += 1
    for tm in [x for x in ding if 0 < x < d - 0.5][:10]:
        ent += ["-i", str(tmp / "ding.wav")]; ms = int(tm * 1000)
        fc += f"[{i}:a]adelay={ms}|{ms},volume=0.22[f{i}];"; mixs.append(f"[f{i}]"); i += 1
    fc += "".join(mixs) + f"amix=inputs={len(mixs)}:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(saida)], check=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "musica":
        salvar(a[1], musica(float(a[2]), int(a[3]) if len(a) > 3 else 7, a[4] if len(a) > 4 else "noite"))
    elif a[0] == "efeitos":
        Path(a[1]).mkdir(parents=True, exist_ok=True)
        for k, v in efeitos().items():
            salvar(Path(a[1]) / f"{k}.wav", v)
    elif a[0] == "mixar":
        mixar(a[1], a[2], a[3], float(a[4]) if len(a) > 4 else -17)
