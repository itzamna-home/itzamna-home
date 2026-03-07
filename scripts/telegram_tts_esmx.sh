#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/telegram_tts_esmx.sh "Tu texto aquí"
# Requires:
#   - edge-tts installed in host Python
#   - openclaw message tool available via CLI

TEXT="${*:-}"
if [[ -z "$TEXT" ]]; then
  echo "Uso: bash scripts/telegram_tts_esmx.sh \"Tu texto aquí\"" >&2
  exit 1
fi

OUT="/home/user/.openclaw/workspace/itzamna-home/.tmp-tts-esmx.mp3"
python3 -m edge_tts --voice es-MX-DaliaNeural --text "$TEXT" --write-media "$OUT"

openclaw message send \
  --channel telegram \
  --target 776654658 \
  --path "$OUT" \
  --as-voice \
  --caption ""
