"""Acha o momento de MAIOR IMPACTO dentro dos intervalos de b-roll (explosão, tiro, batida, corte rápido):
mede o volume do áudio original e o quanto a imagem muda, a cada 0,25 s. Usado para abrir os Shorts com a cena
mais forte nos primeiros segundos (ideia tirada do "Cortador Automático").
Uso: from impacto import momento_forte; t = momento_forte(src, [[a, b], ...], dur_take)"""
import subprocess
import numpy as np

PASSO = 0.25   # segundos


def _audio(src, a, b, sr=8000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", str(src),
                          "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    n = int(sr * PASSO)
    if len(x) < n:
        return np.zeros(0)
    x = x[: len(x) // n * n].reshape(-1, n)
    return np.sqrt((x ** 2).mean(axis=1))


def _movimento(src, a, b, w=64, h=36):
    fps = 1 / PASSO
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", str(src),
                          "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    q = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
    if len(q) < 2 * w * h:
        return np.zeros(0)
    q = q[: len(q) // (w * h) * (w * h)].reshape(-1, w * h)
    d = np.abs(np.diff(q, axis=0)).mean(axis=1)
    return np.concatenate([[0.0], d])


def _norm(v):
    if v.size == 0 or v.max() <= v.min():
        return np.zeros_like(v)
    return (v - v.min()) / (v.max() - v.min())


def momento_forte(src, ranges, take=3.6, janela=2.0):
    """Devolve o início (s) do take de maior impacto, ou None se não conseguir medir."""
    melhor, nota_max = None, -1.0
    k = max(1, int(janela / PASSO))
    for a, b in ranges:
        if b - a < take:
            continue
        au, mv = _audio(src, a, b), _movimento(src, a, b)
        n = min(len(au), len(mv))
        if n < k:
            continue
        nota = 0.6 * _norm(au[:n]) + 0.4 * _norm(mv[:n])
        janela_nota = np.convolve(nota, np.ones(k) / k, mode="valid")   # força média dos 2 primeiros segundos do take
        lim = max(1, int((b - a - take) / PASSO) + 1)
        janela_nota = janela_nota[:lim]
        if janela_nota.size == 0:
            continue
        i = int(janela_nota.argmax())
        if janela_nota[i] > nota_max:
            nota_max, melhor = float(janela_nota[i]), a + i * PASSO
    return melhor
