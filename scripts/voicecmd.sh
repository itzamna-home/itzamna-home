#!/usr/bin/env bash
set -euo pipefail

# One-shot voice command flow (higher accuracy):
# 1) wake bridge with "hola"
# 2) record audio from mic
# 3) transcribe with faster-whisper (Spanish)
# 4) send recognized text to bridge/OpenClaw

BRIDGE_URL="http://127.0.0.1:8099/rhasspy"
MIC_DEVICE="${MIC_DEVICE:-plughw:0,0}"
SECONDS_REC="${SECONDS_REC:-6}"
WHISPER_MODEL="${WHISPER_MODEL:-small}"
TMP_WAV="/tmp/voicecmd.wav"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"hola"}' >/dev/null

echo "🎤 Habla ahora (${SECONDS_REC}s, mic=${MIC_DEVICE})..."
arecord -D "$MIC_DEVICE" -f S16_LE -c 1 -r 16000 -d "$SECONDS_REC" "$TMP_WAV" >/dev/null 2>&1

CMD=$(python3 "$SCRIPT_DIR/whisper_stt.py" "$TMP_WAV" --model "$WHISPER_MODEL" --lang es)

if [[ -z "$CMD" ]]; then
  echo "❌ No se detectó texto." >&2
  exit 1
fi

echo "📝 Detectado (Whisper): $CMD"

PAYLOAD=$(jq -n --arg t "$CMD" --arg w "default" '{raw_text:$t,wakeword_id:$w}')

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

echo
