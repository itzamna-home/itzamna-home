#!/usr/bin/env bash
set -euo pipefail

# One-shot voice command flow (single mic owner = Rhasspy):
# 1) wake bridge with "hola"
# 2) Rhasspy captures audio from mic
# 3) send recognized text to bridge/OpenClaw

BRIDGE_URL="http://127.0.0.1:8099/rhasspy"
LISTEN_TIMEOUT="${LISTEN_TIMEOUT:-12}"
LISTEN_URL="http://127.0.0.1:12101/api/listen-for-command?timeout=${LISTEN_TIMEOUT}"

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"hola"}' >/dev/null

echo "🎤 Habla ahora (timeout ${LISTEN_TIMEOUT}s)..."
RESP=$(curl -sS -X POST "$LISTEN_URL" || true)
echo "📦 Rhasspy: $RESP"

if [[ "$RESP" == \{*\} ]]; then
  CMD=$(echo "$RESP" | jq -r '.raw_text // .text // empty')
  echo "📝 Detectado: $CMD"
else
  echo "❌ Rhasspy no devolvió JSON (probable timeout). Habla justo después del prompt o sube LISTEN_TIMEOUT." >&2
  exit 1
fi

if [[ -z "$CMD" ]]; then
  echo "❌ No se detectó texto." >&2
  exit 1
fi

PAYLOAD=$(jq -n --arg t "$CMD" --arg w "default" '{raw_text:$t,wakeword_id:$w}')

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

echo
