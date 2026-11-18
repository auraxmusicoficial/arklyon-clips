"""Salva no GitHub as mudanças de estado feitas pelo robô, mesmo se outro robô (produção/faxina) mexeu no repositório
nesse meio-tempo — mescla os arquivos JSON item a item em vez de sobrescrever.
Uso: python3 motor/sincronizar.py "mensagem do commit\""""
import json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def sh(*a, ok=False):
    r = subprocess.run(a, cwd=RAIZ, capture_output=True, text=True)
    if r.returncode and not ok:
        raise RuntimeError(f"{' '.join(a)}: {r.stderr.strip()[:400]}")
    return r.stdout


def chave(e):
    if isinstance(e, dict):
        if "quando" in e:
            return (e["quando"], e.get("yt_title") or e.get("titulo", ""))
        return e.get("id") or e.get("video_id") or e.get("url") or json.dumps(e, sort_keys=True)
    return e


def mesclar(base, nosso, remoto):
    """3 vias: aplica sobre o remoto só o que NÓS mudamos em relação à base."""
    if isinstance(nosso, dict) and isinstance(remoto, dict):
        b = base if isinstance(base, dict) else {}
        out = dict(remoto)
        for k, v in nosso.items():
            if b.get(k) != v:
                out[k] = mesclar(b.get(k), v, remoto.get(k)) if k in remoto else v
        return out
    if isinstance(nosso, list) and isinstance(remoto, list):
        b = {json.dumps(chave(e), default=str): e for e in (base or [])} if isinstance(base, list) else {}
        out = list(remoto); idx = {json.dumps(chave(e), default=str): i for i, e in enumerate(out)}
        for e in nosso:
            k = json.dumps(chave(e), default=str)
            if k in idx:
                if b.get(k) != e:
                    out[idx[k]] = mesclar(b.get(k), e, out[idx[k]])
            elif k not in b:      # item novo nosso
                out.append(e); idx[k] = len(out) - 1
        return out
    return nosso


def main(msg):
    sh("git", "add", "-A")
    if not sh("git", "status", "--porcelain").strip():
        print("nada para salvar"); return
    base_sha = sh("git", "rev-parse", "HEAD").strip()
    mudados = [l[3:].strip() for l in sh("git", "status", "--porcelain").splitlines()]
    nossos = {f: (RAIZ / f).read_bytes() if (RAIZ / f).exists() else None for f in mudados}
    bases = {f: sh("git", "show", f"{base_sha}:{f}", ok=True) for f in mudados}
    cfg = ["-c", "user.name=Vault Robot (GitHub)", "-c", "user.email=actions@github.com"]
    for tentativa in range(4):
        sh("git", "fetch", "-q", "--depth=1", "origin", "main")
        sh("git", "reset", "-q", "--hard", "origin/main")
        for f, dados in nossos.items():
            p = RAIZ / f
            if dados is None:
                p.unlink(missing_ok=True); continue
            p.parent.mkdir(parents=True, exist_ok=True)
            if f.endswith(".json") and p.exists():
                try:
                    novo = mesclar(json.loads(bases[f]) if bases[f] else None, json.loads(dados), json.loads(p.read_text()))
                    p.write_text(json.dumps(novo, ensure_ascii=False, indent=1)); continue
                except ValueError:
                    pass
            p.write_bytes(dados)
        sh("git", "add", "-A")
        if not sh("git", "status", "--porcelain").strip():
            print("já estava igual no remoto"); return
        sh("git", *cfg, "commit", "-q", "-m", msg)
        if subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=RAIZ).returncode == 0:
            print("salvo:", ", ".join(mudados)); return
    raise RuntimeError("não consegui salvar depois de 4 tentativas")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "robô do GitHub: atualiza estado")
