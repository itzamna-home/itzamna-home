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

Opcional (si quieres Ollama local en este mismo host):

```bash
docker compose --profile local-ollama up -d ollama
```

## Documentación

- Bitácora de cambios y decisiones: `docs/operations-log-2026-03-07.md`
