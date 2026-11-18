#!/bin/bash
# Prepara o ambiente da sessão (rodar uma vez por sessão).
set -e
cd "$(dirname "$0")"
pip install -q --break-system-packages faster-whisper piper-tts gdown numpy 2>&1 | grep -v -i warn || true
mkdir -p modelos fontes
[ -f modelos/en_US-ryan-high.onnx ] || curl -sSL -o modelos/en_US-ryan-high.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx
[ -f modelos/en_US-ryan-high.onnx.json ] || curl -sSL -o modelos/en_US-ryan-high.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json
[ -f fontes/Anton-Regular.ttf ] || curl -sSL -o fontes/Anton-Regular.ttf \
  https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf
# Pricedown (fonte gratuita da Typodermic, estilo dos títulos de GTA) — baixada na hora, não vai pro repositório
[ -f fontes/Pricedown.otf ] || { rm -rf /tmp/pd && git clone -q --depth 1 https://github.com/C0D3XT/Pricedown-Font /tmp/pd \
  && cp "/tmp/pd/Pricedown Bl.otf" fontes/Pricedown.otf; } || true
mkdir -p ~/.fonts && cp fontes/*.ttf ~/.fonts/ && fc-cache -f >/dev/null 2>&1 || true
which ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)
python3 -c "import faster_whisper, piper; print('setup ok')"
