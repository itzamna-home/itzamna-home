#!/usr/bin/env bash
set -euo pipefail

# One-shot voice command flow (shared PipeWire, no ALSA contention):
# 1) wake bridge with "hola"
# 2) capture audio with pw-record from PipeWire source
# 3) transcribe with faster-whisper
# 4) send recognized text to bridge/OpenClaw

BRIDGE_URL="http://127.0.0.1:8099/rhasspy"
SECONDS_REC="${SECONDS_REC:-6}"
AUDIO_SOURCE="${AUDIO_SOURCE:-mic_bus.monitor}"
WHISPER_MODEL="${WHISPER_MODEL:-medium}"
TMP_WAV="/tmp/voicecmd-pw.wav"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"hola"}' >/dev/null

echo "🎤 Habla ahora (${SECONDS_REC}s, source=${AUDIO_SOURCE})..."

# Capture from PipeWire source (shared, no mic lock fight)
timeout "${SECONDS_REC}" pw-record --target "$AUDIO_SOURCE" --rate 16000 --channels 1 --format s16 "$TMP_WAV" >/dev/null 2>&1 || true

if [[ ! -s "$TMP_WAV" ]]; then
  echo "❌ No se pudo capturar audio desde PipeWire (${AUDIO_SOURCE})." >&2
  echo "Tip: revisa fuentes con: pactl list short sources" >&2
  exit 1
fi

CMD=$(python3 "$SCRIPT_DIR/whisper_stt.py" "$TMP_WAV" --model "$WHISPER_MODEL" --lang es)
echo "📝 Detectado: $CMD"

if [[ -z "$CMD" ]]; then
  echo "❌ No se detectó texto." >&2
  exit 1
fi

PAYLOAD=$(jq -n --arg t "$CMD" --arg w "default" '{raw_text:$t,wakeword_id:$w}')

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

echo
