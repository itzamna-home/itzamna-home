#!/usr/bin/env bash
set -euo pipefail

# One-shot voice command flow:
# 1) wake bridge with "hola"
# 2) capture command through Rhasspy
# 3) send recognized text to bridge/OpenClaw

BRIDGE_URL="http://127.0.0.1:8099/rhasspy"
LISTEN_URL="http://127.0.0.1:12101/api/listen-for-command?timeout=8"

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"hola"}' >/dev/null

echo "🎤 Habla ahora (timeout 8s)..."
RESP=$(curl -sS -X POST "$LISTEN_URL")

echo "📦 Rhasspy: $RESP"
CMD=$(echo "$RESP" | jq -r '.raw_text // .text // empty')

if [[ -z "$CMD" ]]; then
  echo "❌ No se detectó texto." >&2
  exit 1
fi

echo "📝 Detectado: $CMD"

PAYLOAD=$(jq -n --arg t "$CMD" --arg w "default" '{raw_text:$t,wakeword_id:$w}')

curl -sS -X POST "$BRIDGE_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

echo
