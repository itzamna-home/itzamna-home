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
- Home Assistant (Docker)

### En otro host
- Ollama (`192.168.100.64:11434`)

## Levantar stack por Docker

```bash
docker compose up -d rhasspy rhasspy-bridge homeassistant
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

### Home Assistant UI

- URL local: `http://127.0.0.1:8123`
- URL LAN: `http://<host>:8123`
- Config persistente: `homeassistant/config`
- Red recomendada para autodiscovery (Hue/mDNS): `network_mode: host`

Primera vez: completa el onboarding web y crea usuario admin.

### Conectar Home Assistant al bridge (voz)

1. Crea token de largo plazo en Home Assistant (`/profile`).
2. Guarda token en `.env` (no versionado):

```bash
echo "HA_TOKEN=tu_token" >> .env
```

3. Reinicia bridge:

```bash
docker compose up -d rhasspy-bridge
```

Con esto, el bridge intenta resolver consultas por la API de conversación de Home Assistant antes de fallback a Ollama.

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
2. captura audio por PipeWire (`pw-record`)
3. transcribe con faster-whisper
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

4. Configura ALSA compartido (`dsnoop`) para evitar pelea de micrófono:

`~/.asoundrc`

```ini
pcm.microfono_compartido {
  type dsnoop
  ipc_key 1024
  ipc_key_add_uid true
  slave {
    pcm "hw:0,0"
    channels 1
    rate 16000
    format S16_LE
  }
}
```

y en perfil Rhasspy usa:

```json
"microphone": {
  "system": "arecord",
  "arecord": { "device": "plug:microfono_compartido" }
}
```

5. Reinicia Rhasspy:

```bash
docker restart rhasspy
```

Notas:

- En la primera ejecución, Whisper descargará el modelo (puede tardar).
- Puedes ajustar variables:
  - `WHISPER_MODEL=small|medium`
  - `AUDIO_SOURCE=mic_bus.monitor`
  - `SECONDS_REC=6`

## TTS en español (Telegram)

Para evitar voz en inglés hablando español, usa voz `es-MX-DaliaNeural` con este script:

```bash
bash scripts/telegram_tts_esmx.sh "Hola, esta es una prueba en español de México"
```

## Documentación

- Bitácora de cambios y decisiones: `docs/operations-log-2026-03-07.md`
