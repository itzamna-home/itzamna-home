from flask import Flask, request, jsonify
import os
import subprocess
import requests
from datetime import datetime

app = Flask(__name__)

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "776654658")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.100.64:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL", "tinyllama:latest")


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

    reply = _call_ollama(FALLBACK_MODEL, prompt)
    return reply or "Listo."


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "rhasspy-openclaw-bridge",
        "time": datetime.utcnow().isoformat() + "Z",
        "ollama_model": OLLAMA_MODEL,
    }


@app.post("/rhasspy")
def rhasspy_in():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or data.get("input") or data.get("utterance") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "No text in payload"}), 400

    try:
        answer = ask_llm(text)
    except Exception as e:
        answer = f"No pude procesarlo ahorita: {e}"

    msg = f"🎙️ Rhasspy: {text}\n🤖 {answer}"
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        TELEGRAM_CHAT_ID,
        "--message",
        msg,
        "--json",
    ]
    code, out, err = run_cmd(cmd)

    return jsonify(
        {
            "ok": True,
            "heard": text,
            "reply": answer,
            "speech": {"text": answer},
            "telegramForwarded": code == 0,
            "stdout": out,
            "stderr": err,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099)
