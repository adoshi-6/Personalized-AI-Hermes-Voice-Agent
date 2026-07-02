import os
import ctypes
import time
import requests
import wave
from piper.voice import PiperVoice

from config import USER_NAME, ASSISTANT_NAME

# Curated collection of local Piper voices across US and UK.
# Controls: [ENTER] download and play, [S] skip, [Q] quit.
# Set your chosen voice in config.py after auditioning.
PIPER_GLOBAL_VOICES = [
    # American voices
    {"name": "Ryan (US - Balanced Male)",          "voice": "ryan",                 "code": "en_US", "quality": "medium"},
    {"name": "Ryan (US - High Definition Male)",   "voice": "ryan",                 "code": "en_US", "quality": "high"},
    {"name": "Lessac (US - Articulate Male)",      "voice": "lessac",               "code": "en_US", "quality": "medium"},
    {"name": "Lessac (US - High Definition Male)", "voice": "lessac",               "code": "en_US", "quality": "high"},
    {"name": "Amy (US - Natural Female)",          "voice": "amy",                  "code": "en_US", "quality": "medium"},
    {"name": "Joe (US - Friendly Male)",           "voice": "joe",                  "code": "en_US", "quality": "medium"},
    {"name": "Kristin (US - Crisp Female)",        "voice": "kristin",              "code": "en_US", "quality": "medium"},
    {"name": "Linda (US - Narrative Female)",      "voice": "linda",                "code": "en_US", "quality": "medium"},
    # British voices
    {"name": "Alan (UK - Sophisticated Male)",     "voice": "alan",                 "code": "en_GB", "quality": "medium"},
    {"name": "Alba (UK - Modern Female)",          "voice": "alba",                 "code": "en_GB", "quality": "medium"},
    {"name": "Jenny (UK - Conversational Female)", "voice": "jenny",                "code": "en_GB", "quality": "medium"},
    {"name": "Northern English Male (UK)",         "voice": "northern_english_male","code": "en_GB", "quality": "medium"},
    {"name": "VCTK (UK - Corporate Male)",         "voice": "vctk",                 "code": "en_GB", "quality": "medium"},
]

MODEL_DIR = os.path.abspath("piper_voices")


def play_audio(file_path):
    """Plays a WAV file using the native Windows audio layer."""
    abs_path = os.path.abspath(file_path)
    alias    = "piper_mega_voice"
    ctypes.windll.winmm.mciSendStringW(
        f'open "{abs_path}" type waveaudio alias {alias}', None, 0, 0)
    ctypes.windll.winmm.mciSendStringW(f'play {alias}', None, 0, 0)
    status = ctypes.create_unicode_buffer(255)
    while True:
        ctypes.windll.winmm.mciSendStringW(f'status {alias} mode', status, 255, 0)
        if status.value != 'playing':
            break
        time.sleep(0.1)
    ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, 0)


def fetch_model(prefix, code, voice, quality):
    """Downloads ONNX model and config from HuggingFace if not already cached."""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    model_path  = os.path.join(MODEL_DIR, f"{prefix}.onnx")
    config_path = os.path.join(MODEL_DIR, f"{prefix}.onnx.json")
    base_url    = (
        f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/"
        f"en/{code}/{voice}/{quality}/"
    )

    if not os.path.exists(model_path):
        print(f"   [Downloading model: {prefix}.onnx (~15-60MB)...]")
        r = requests.get(base_url + f"{prefix}.onnx", stream=True)
        if r.status_code != 200:
            print("   [Error: This voice combination is not available]")
            return None, None
        with open(model_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    if not os.path.exists(config_path):
        print("   [Downloading voice config...]")
        r = requests.get(base_url + f"{prefix}.onnx.json", stream=True)
        with open(config_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return model_path, config_path


def main():
    print("==================================================")
    print("  Piper Offline Voice Audition Platform")
    print("  [ENTER] Download & Play | [S] Skip | [Q] Quit")
    print("==================================================")

    total       = len(PIPER_GLOBAL_VOICES)
    output_file = os.path.abspath("piper_test.wav")

    for idx, speaker in enumerate(PIPER_GLOBAL_VOICES, start=1):
        prefix = f"{speaker['code']}-{speaker['voice']}-{speaker['quality']}"
        print(f"\n[{idx}/{total}] {speaker['name']}")
        print(f"  Model: {prefix}")

        choice = input("Press Enter to test (or 's' to skip, 'q' to quit): ").strip().lower()

        if choice == 'q':
            print("\nExiting.")
            break
        elif choice == 's':
            print("Skipped.")
            continue

        m_path, _ = fetch_model(prefix, speaker['code'], speaker['voice'], speaker['quality'])
        if not m_path:
            continue

        try:
            print("   [Loading offline voice engine...]")
            engine      = PiperVoice.load(m_path)
            sample_text = (
                f"Hello {USER_NAME}. This is the {speaker['name'].split('(')[0].strip()} "
                f"offline voice running on Piper. How do I sound for {ASSISTANT_NAME}?"
            )
            with wave.open(output_file, 'wb') as wav_file:
                engine.synthesize(sample_text, wav_file)
            play_audio(output_file)
        except Exception as e:
            print(f"   [Synthesis error: {e}]")

    if os.path.exists(output_file):
        try:
            os.remove(output_file)
        except Exception:
            pass

    print("\n==================================================")
    print("  Done. Set your chosen voice in config.py")
    print("==================================================\n")


if __name__ == "__main__":
    main()