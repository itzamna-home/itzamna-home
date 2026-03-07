#!/usr/bin/env python3
from flask import Flask, request, Response
from faster_whisper import WhisperModel
import tempfile
import os

app = Flask(__name__)

MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
LANG = os.environ.get("WHISPER_LANG", "es")
COMPUTE = os.environ.get("WHISPER_COMPUTE", "int8")

model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE)


@app.get('/health')
def health():
    return {"ok": True, "model": MODEL_SIZE, "lang": LANG, "compute": COMPUTE}


@app.post('/api/speech-to-text')
def stt():
    audio = request.get_data()
    if not audio:
        return Response("", mimetype="text/plain")

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(audio)
        wav_path = f.name

    try:
        segments, _ = model.transcribe(wav_path, language=LANG, vad_filter=True, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return Response(text, mimetype="text/plain")
    finally:
        try:
            os.remove(wav_path)
        except Exception:
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8100)
