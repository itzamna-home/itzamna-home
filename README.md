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

Hace todo en una sola ejecución:

1. activa wake (`hola`)
2. escucha por micrófono con Rhasspy
3. envía el texto a OpenClaw/Ollama bridge

Requisito: `jq` instalado en host.

## Documentación

- Bitácora de cambios y decisiones: `docs/operations-log-2026-03-07.md`
