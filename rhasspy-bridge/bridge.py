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
    candidates = [
        # Prefer raw ASR text first; Rhasspy "text" may be intent-normalized.
        data.get('raw_text'),
        data.get('raw_input'),
        data.get('rawInput'),
        data.get('text'),
        data.get('input'),
        data.get('utterance'),
    ]

    if isinstance(data.get('slots'), dict):
        candidates.append(data['slots'].get('text'))

    if isinstance(data.get('intent'), dict):
        candidates.extend([
            data['intent'].get('input'),
            data['intent'].get('raw_input'),
            data['intent'].get('rawInput'),
            data['intent'].get('name'),
        ])

    candidates = [c.strip() for c in candidates if isinstance(c, str) and c.strip()]
    text = candidates[0] if candidates else ''

    if not text:
        return jsonify({"ok": False, "error": "No text in payload", "payload": data}), 400

    global ARMED_UNTIL
    normalized = text.strip().lower()

    # Wake-word flow: tolerate ASR repeats like "hola hola" and check all candidate text forms.
    def is_wake_phrase(s: str) -> bool:
        s = s.strip().lower()
        tokens = [t for t in s.replace(',', ' ').replace('.', ' ').split() if t]
        return bool(tokens) and all(t == WAKE_WORD for t in tokens)

    only_wake_tokens = any(is_wake_phrase(c) for c in candidates)

    if only_wake_tokens:
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

    # If Rhasspy provides wakeword/session signal, allow command without manual arm state.
    wakeword_signal = data.get('wakeword_id')
    if (not wakeword_signal) and isinstance(data.get('intent'), dict):
        wakeword_signal = data['intent'].get('wakeword_id')

    is_armed = (ARMED_UNTIL is not None) and (datetime.utcnow() <= ARMED_UNTIL)
    if not is_armed and not wakeword_signal:
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
