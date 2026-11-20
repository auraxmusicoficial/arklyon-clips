"""Transmissor de lives do HQ Vault Clips (roda no SnapDeploy).
Variáveis (postas pelo robô do GitHub pela API):
  STREAM_KEY   chave da live no YouTube
  VIDEO_URL    link direto do vídeo (mp4 H.264/AAC)
  DURACAO_MIN  duração da live em minutos
  SELF_URL     endereço público deste container (para se manter acordado durante a live)
  LIVE_ID      identificador da live (só para registro)
Sem STREAM_KEY: apenas testa a rede e fica parado."""
import os, socket, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

E = {"fase": "iniciando", "live": os.environ.get("LIVE_ID", "-"), "inicio": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}

def rede():
    try:
        socket.create_connection(("a.rtmp.youtube.com", 1935), timeout=10).close()
        return "ok: porta 1935 do YouTube acessível"
    except Exception as e:
        return f"FALHOU: {e}"

def manter_acordado(parar):
    url = os.environ.get("SELF_URL")
    while url and not parar.is_set():
        try: urllib.request.urlopen(url.rstrip("/") + "/ping", timeout=20).read()
        except Exception: pass
        parar.wait(240)

def transmitir():
    E["rede"] = rede()
    chave, video = os.environ.get("STREAM_KEY"), os.environ.get("VIDEO_URL")
    if not (chave and video):
        E["fase"] = "parado (sem live marcada)"; return
    dur = int(float(os.environ.get("DURACAO_MIN", "10")) * 60)
    parar = threading.Event(); threading.Thread(target=manter_acordado, args=(parar,), daemon=True).start()
    try:
        E["fase"] = "baixando vídeo"
        subprocess.run(["curl", "-sSfL", "--retry", "3", "-o", "/tmp/live.mp4", video], check=True)
        fim = time.time() + dur; tentativas = 0
        while time.time() < fim - 30 and tentativas < 20:
            E["fase"] = "AO VIVO"; tentativas += 1
            p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-re", "-stream_loop", "-1",
                                "-i", "/tmp/live.mp4", "-t", str(int(fim - time.time())), "-c", "copy",
                                "-f", "flv", f"rtmp://a.rtmp.youtube.com/live2/{chave}"], capture_output=True, text=True)
            E["ultimo_erro"] = (p.stderr or "")[-400:]
            if time.time() < fim - 30: time.sleep(5)   # caiu antes da hora: reconecta
        E["fase"] = "live encerrada"
    except Exception as e:
        E["fase"] = f"erro: {e}"
    finally:
        parar.set()

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
        self.wfile.write("\n".join(f"{k}: {v}" for k, v in E.items()).encode())
    def log_message(self, *a): pass

threading.Thread(target=transmitir, daemon=True).start()
HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
