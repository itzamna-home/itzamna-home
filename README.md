# itzamna-home

Infra y documentación operativa de Itzamna Home.

## Estado actual (2026-03-07)

- OpenClaw endurecido (hardening aplicado)
- Gateway por HTTPS con Tailscale Serve
- Healthchecks semanales configurados por cron
- Rhasspy instalado en Docker
- Bridge Rhasspy -> Ollama/OpenClaw funcional
- Ollama remoto disponible en `192.168.100.64:11434`

## Servicios

### En este host
- OpenClaw Gateway (systemd, fuera de Docker)
- Rhasspy (Docker)
- Rhasspy Bridge (Docker)

### En otro host
- Ollama (`192.168.100.64:11434`)

## Levantar stack por Docker

```bash
docker compose up -d rhasspy rhasspy-bridge
```

### Dejar Rhasspy + OpenClaw listo (voz)

1. Copia el perfil base:

```bash
mkdir -p rhasspy/profiles/es
cp rhasspy/profile.es.sample.json rhasspy/profiles/es/profile.json
```

2. Reinicia Rhasspy:

```bash
docker compose restart rhasspy
```

3. Abre Rhasspy en `http://<host>:12101` y en **Train** descarga/entrena el perfil.

4. Prueba TTS:

```bash
curl -X POST 'http://127.0.0.1:12101/api/text-to-speech?play=true' \
  -H 'Content-Type: text/plain' \
  --data 'hola desde rhasspy'
```

5. Prueba bridge:

```bash
curl -X POST http://127.0.0.1:8099/rhasspy \
  -H 'Content-Type: application/json' \
  -d '{"text":"dime buenos días"}'
```

Opcional (si quieres Ollama local en este mismo host):

```bash
docker compose --profile local-ollama up -d ollama
```

## Comando único de voz (copy/paste)

```bash
bash scripts/voicecmd.sh
```

Hace todo en una sola ejecución (sin pelea de micrófono):

1. activa wake (`hola`)
2. Rhasspy captura micrófono
3. toma texto reconocido (`raw_text`)
4. envía el texto a OpenClaw/Ollama bridge

Requisitos en host:

- `jq`
- Python 3 + `faster-whisper`

Instalación:

```bash
pip3 install --user --break-system-packages faster-whisper
```

### Rhasspy con STT Whisper remoto (recomendado)

1. Instala servicio systemd user (persistente):

```bash
mkdir -p ~/.config/systemd/user
cp systemd/whisper-stt.service ~/.config/systemd/user/whisper-stt.service
systemctl --user daemon-reload
systemctl --user enable --now whisper-stt.service
systemctl --user status whisper-stt.service --no-pager
```

2. Configura Rhasspy para usar STT remoto:

```json
"speech_to_text": {
  "system": "remote",
  "remote": { "url": "http://172.17.0.1:8100/api/speech-to-text" }
}
```

3. Desactiva wake interno de Rhasspy (el wake lo maneja el bridge con "hola") para evitar contención de micrófono:

```json
"wake": { "system": "dummy" }
```

4. Reinicia Rhasspy:

```bash
docker restart rhasspy
```

Notas:

- En la primera ejecución, Whisper descargará el modelo (puede tardar).
- Puedes ajustar variables:
  - `WHISPER_MODEL=small|medium`
  - `MIC_DEVICE=plughw:0,0`
  - `SECONDS_REC=6`
  - `LISTEN_TIMEOUT=10` (cuando usa fallback Rhasspy)

## Documentación

- Bitácora de cambios y decisiones: `docs/operations-log-2026-03-07.md`
