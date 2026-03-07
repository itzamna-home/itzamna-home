# Operations Log - 2026-03-07

## 1) Healthcheck + seguridad OpenClaw

Se ejecutaron verificaciones read-only:

- `openclaw security audit --deep`
- `openclaw update status`

Hallazgos iniciales:

- `gateway.controlUi.dangerouslyDisableDeviceAuth=true` (critical)
- `gateway.controlUi.allowInsecureAuth=true`
- Sin `gateway.auth.rateLimit`
- Update disponible (se actualizó a 2026.3.2)

Acciones aplicadas:

- Se desactivaron flags inseguros de Control UI
- Se configuró rate limit:
  - `maxAttempts: 10`
  - `windowMs: 60000`
  - `lockoutMs: 300000`
- Re-validación: `0 critical`, `0 warn`

## 2) Scheduling semanal

Se configuraron jobs cron:

- `healthcheck:security-audit` -> sábados 00:00 CST
- `healthcheck:update-status` -> sábados 00:10 CST

Con indicación de salida para corrección: "call healthcheck to fix issues".

## 3) Acceso remoto seguro a Control UI

Se habilitó Tailscale y exposición por HTTPS (Serve):

- URL: `https://thinkpad.tail5456b7.ts.net`
- Gateway quedó en `bind=loopback` (modelo más seguro)
- Se agregó origin permitido en `gateway.controlUi.allowedOrigins` para el dominio HTTPS
- Se aprobó pairing de nuevo dispositivo en Control UI

## 4) Ollama remoto

Host: `192.168.100.64:11434`

- Inicialmente no accesible por LAN
- Se indicó bind a `0.0.0.0:11434`
- Verificación remota OK
- Modelos detectados:
  - `llama3.1:8b`
  - `tinyllama:latest`
- Prueba de inferencia OK

## 5) Model routing en OpenClaw

Configuración resultante:

- Primary: `openai-codex/gpt-5.3-codex`
- Fallback: `ollama/llama3.1:8b`
- Proveedor Ollama explícito a host remoto

Nota: forzado directo por runtime quedó restringido por allowlist del entorno, pero fallback y API funcionan.

## 6) Rhasspy + bridge

- Rhasspy instalado en Docker en puerto `12101`
- Se habilitó passthrough de audio ALSA al contenedor (`/dev/snd` + grupo `audio`)
- Bridge HTTP en `:8099` para recibir texto de Rhasspy
- Bridge genera respuesta con Ollama y reenvía traza a Telegram
- Endpoint de salud: `GET /health`
- Endpoint principal: `POST /rhasspy`

Payload esperado:

```json
{"text":"tu frase"}
```

Respuesta incluye:

- `reply`
- `speech.text`

Útil para TTS en Rhasspy.
