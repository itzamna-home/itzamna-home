#!/usr/bin/env python3
import argparse
import sys
from faster_whisper import WhisperModel


def main():
    p = argparse.ArgumentParser()
    p.add_argument("audio", help="Path to wav audio file")
    p.add_argument("--model", default="small", help="Whisper model size (tiny, base, small, medium, large-v3)")
    p.add_argument("--lang", default="es", help="Language code")
    p.add_argument("--compute", default="int8", help="Compute type (int8, float16, float32)")
    args = p.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type=args.compute)
    segments, _ = model.transcribe(args.audio, language=args.lang, vad_filter=True, beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
