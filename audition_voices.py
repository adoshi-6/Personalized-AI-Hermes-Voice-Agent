import asyncio
import edge_tts
import os
import ctypes
import time

from config import USER_NAME, ASSISTANT_NAME

# A curated shortlist of 7 voices to audition before committing to one.
# After running this script, set your preferred voice in config.py under VOICE_TAG.
TEST_VOICES = {
    "Brian (US - Corporate & Crisp)":        "en-US-BrianNeural",
    "Andrew (US - Deep & Casual)":           "en-US-AndrewNeural",
    "Christopher (US - Young & Articulate)": "en-US-ChristopherNeural",
    "Ava (US - Modern Female)":              "en-US-AvaNeural",
    "Emma (US - Soft & Calm Female)":        "en-US-EmmaNeural",
    "Ryan (UK - Cinematic British)":         "en-GB-RyanNeural",
    "Sonia (UK - Polished British Female)":  "en-GB-SoniaNeural",
}


def play_audio(file_path):
    """Plays an MP3 file using the native Windows audio layer."""
    abs_path = os.path.abspath(file_path)
    alias    = os.path.basename(file_path).split('.')[0]

    ctypes.windll.winmm.mciSendStringW(
        f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, 0)
    ctypes.windll.winmm.mciSendStringW(f'play {alias}', None, 0, 0)

    status = ctypes.create_unicode_buffer(255)
    while True:
        ctypes.windll.winmm.mciSendStringW(f'status {alias} mode', status, 255, 0)
        if status.value != 'playing':
            break
        time.sleep(0.1)

    ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, 0)


async def run_audition():
    print("\n==================================================")
    print("  Voice Auditions: Initial Shortlist")
    print("==================================================\n")

    generated_files = []

    for nickname, voice_tag in TEST_VOICES.items():
        name_key    = nickname.split('(')[0].strip().lower().replace(' ', '_')
        unique_file = f"voice_sample_{name_key}.mp3"
        generated_files.append(unique_file)

        print(f"Playing: {nickname}...")
        sample_text = (
            f"Hello {USER_NAME}. This is the {nickname.split('(')[0].strip()} "
            f"voice profile. How do I sound as the voice of {ASSISTANT_NAME}?"
        )

        try:
            communicate = edge_tts.Communicate(sample_text, voice_tag)
            await communicate.save(unique_file)
            play_audio(unique_file)
            time.sleep(0.8)
        except Exception as e:
            print(f"[Failed to process {nickname}: {e}]")

    print("\nCleaning up audio files...")
    for f in generated_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    print("\n==================================================")
    print("  Auditions complete. Set your choice in config.py")
    print("==================================================\n")


if __name__ == "__main__":
    asyncio.run(run_audition())