"""Render two local Kokoro performances and retain their actual token durations."""
import json
import os
import sys
import wave
from pathlib import Path

# Use VoiceStudio's installed weights. This worker never sends script text to a service.
os.environ["HF_HUB_OFFLINE"] = "1"
MODEL = "mlx-community/Kokoro-82M-bf16"


def performance(pipeline, request, voice, dest):
    import numpy as np
    samples = []
    words = []
    frames = 0
    rate = 24000
    for phrase in request["phrases"]:
        labels = phrase["text"].split()
        aliases = phrase.get("pronounce", {})
        spoken = [aliases.get(label, label) for label in labels]
        spans = []
        text = ""
        for line in spoken:
            # Map Kokoro's punctuation and subword tokens back to caption words.
            start = len(text)
            text += "".join(line.split())
            spans.append((start, len(text)))
        tokens = []
        cursor = 0
        speed = phrase.get("speed", request["speed"])
        for chunk in pipeline(" ".join(spoken), voice=voice, speed=speed):
            pcm = np.asarray(chunk.audio).reshape(-1)
            start_time = frames / rate
            for token in chunk.tokens:
                letters = "".join(token.text.split())
                if not text.startswith(letters, cursor):
                    raise ValueError("Spoken tokens changed. Use a pronounce entry for the affected word.")
                end = cursor + len(letters)
                if token.start_ts is not None and token.end_ts is not None:
                    tokens.append((cursor, end, start_time + token.start_ts,
                                   start_time + min(token.end_ts, len(pcm) / rate)))
                cursor = end
            samples.append(pcm)
            frames += len(pcm)
        if cursor != len(text):
            raise ValueError("Kokoro did not speak the complete phrase.")
        for label, (start, end) in zip(labels, spans):
            matched = [t for t in tokens if t[0] < end and t[1] > start]
            if not matched:
                raise ValueError(f"No word timing for {label}. Adjust pronunciation and audition again.")
            words.append({"text": label, "start": matched[0][2], "end": matched[-1][3]})
        pause = round(phrase.get("pause_after", 0) * rate)
        if pause:
            samples.append(np.zeros(pause, dtype=np.float32))
            frames += pause
    pcm = np.concatenate(samples)
    if not np.isfinite(pcm).all() or not np.any(np.abs(pcm) > .001):
        raise ValueError("Kokoro returned an inaudible reading.")
    with wave.open(str(dest), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", ""))
        wav.writeframes((np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes())
    return {"words": words, "duration": frames / rate}


def main(directory):
    from huggingface_hub import snapshot_download
    from mlx_audio.tts.utils import load_model
    from mlx_audio.tts.models.kokoro.pipeline import KokoroPipeline
    cache = Path(snapshot_download(MODEL, local_files_only=True))
    pipeline = KokoroPipeline("a", load_model(cache), MODEL)
    requests = json.loads((directory / "delivery.json").read_text())
    results = {}
    for key, request in requests.items():
        voice = str(cache / "voices" / (request["voice"] + ".safetensors"))
        results[key] = performance(pipeline, request, voice, directory / f"{key}.wav")
    (directory / "timings.json").write_text(json.dumps(results))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
