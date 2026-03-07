#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# ---- Config ----
TELEGRAM_CHAT_ID = "776654658"
OLLAMA_URL = "http://192.168.100.64:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
WAKE_WORD = "hola"
ARM_SECONDS = 20
ARMED_UNTIL = None


def run_cmd(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _call_ollama(model: str, prompt: str) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()


def ask_llm(user_text: str) -> str:
    prompt = (
        "You are a home assistant voice bot. "
        "Reply in Mexican Spanish, concise (max 1 short sentence).\n"
        f"User: {user_text}\nAssistant:"
    )
    try:
        reply = _call_ollama(OLLAMA_MODEL, prompt)
        if reply:
            return reply
    except Exception:
        pass

    # fallback local model
    reply = _call_ollama("tinyllama:latest", prompt)
    return reply or "Listo."


@app.get('/health')
def health():
    return {
        "ok": True,
        "service": "rhasspy-openclaw-bridge",
        "time": datetime.utcnow().isoformat() + "Z",
        "ollama_model": OLLAMA_MODEL,
    }


@app.post('/rhasspy')
def rhasspy_in():
    data = request.get_json(silent=True) or {}

    # Accept multiple Rhasspy payload styles
    text = (
        data.get('text')
        or data.get('input')
        or data.get('utterance')
        or data.get('raw_text')
        or ((data.get('slots') or {}).get('text') if isinstance(data.get('slots'), dict) else None)
        or ''
    ).strip()

    # Some intent payloads carry text in nested/alternate fields
    if not text and isinstance(data.get('intent'), dict):
        text = (data['intent'].get('name') or '').strip()

    if not text:
        return jsonify({"ok": False, "error": "No text in payload", "payload": data}), 400

    global ARMED_UNTIL
    normalized = text.strip().lower()

    # Wake-word flow: say "hola" first, then next utterance is treated as command.
    if normalized == WAKE_WORD:
        ARMED_UNTIL = datetime.utcnow() + timedelta(seconds=ARM_SECONDS)
        answer = "Te escucho. ¿Cuál es tu comando?"
        return jsonify({
            "ok": True,
            "heard": text,
            "armed": True,
            "reply": answer,
            "speech": {"text": answer},
            "telegramForwarded": False,
            "stdout": "",
            "stderr": "",
        })

    if (ARMED_UNTIL is None) or (datetime.utcnow() > ARMED_UNTIL):
        answer = "Di hola para activarme."
        return jsonify({
            "ok": True,
            "heard": text,
            "armed": False,
            "reply": answer,
            "speech": {"text": answer},
            "telegramForwarded": False,
            "stdout": "",
            "stderr": "",
        })

    # Consume armed state and execute command
    ARMED_UNTIL = None

    try:
        answer = ask_llm(text)
    except Exception as e:
        answer = f"No pude procesarlo ahorita: {e}"

    # Optional trace to Telegram
    msg = f"🎙️ Rhasspy: {text}\n🤖 {answer}"
    cmd = [
        "openclaw", "message", "send",
        "--channel", "telegram",
        "--target", TELEGRAM_CHAT_ID,
        "--message", msg,
        "--json",
    ]
    code, out, err = run_cmd(cmd)

    # Return text for Rhasspy TTS/webhook consumers
    return jsonify({
        "ok": True,
        "heard": text,
        "armed": False,
        "reply": answer,
        "speech": {"text": answer},
        "telegramForwarded": code == 0,
        "stdout": out,
        "stderr": err,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8099)
