import speech_recognition as sr
import asyncio
import edge_tts
import os
import ctypes
import time
import threading

# Global speaking lock — prevents two TTS calls overlapping.
# speak_text blocks until audio finishes so /api/speak only returns
# when Ace has truly finished speaking — which is what keeps the
# frontend mic muted for exactly the right duration.
_speak_lock = threading.Lock()

is_currently_speaking = False


def is_speaking():
    return is_currently_speaking or _speak_lock.locked()


def _mci(command: str) -> bool:
    try:
        return ctypes.windll.winmm.mciSendStringW(command, None, 0, 0) == 0
    except Exception:
        return False


def stop_all_audio():
    global is_currently_speaking
    is_currently_speaking = False
    _mci('close all')


def speak_text(text, voice_mode="standard"):
    """
    Converts text to speech using the Ryan (UK) voice.
    Blocks until playback is fully complete (play wait).
    """
    global is_currently_speaking
    if not text or not text.strip():
        is_currently_speaking = False
        return

    # Prepend a small pause to let the audio hardware wake up without truncating the first words
    text = "... " + text.lstrip('. ')

    is_currently_speaking = True
    output_file = os.path.abspath("ace_speech.mp3")
    from config import VOICE_TAG
    selected_voice = VOICE_TAG

    async def generate_speech():
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_file)

    try:
        with _speak_lock:
            try:
                asyncio.run(generate_speech())
                _mci(f'open "{output_file}" type mpegvideo alias ace_audio')
                # "play wait" blocks until playback is done — no polling loop needed
                _mci('play ace_audio wait')
                _mci('close ace_audio')
            except Exception as e:
                print(f"[Audio pipeline error: {e}]")
    finally:
        is_currently_speaking = False

def listen_to_user():
    """Captures microphone audio with an expanded window for long sentences."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 3.5
    recognizer.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.energy_threshold = 300
        
        print("\n [Listening... Speak now]")
        try:
            audio_data = recognizer.listen(source, timeout=7, phrase_time_limit=None)
            print("Processing text...")
            text = recognizer.recognize_google(audio_data)
            print(f"You said: \"{text}\"")
            return text
        except sr.UnknownValueError:
            print("[System could not understand the audio waveform]")
            return None
        except sr.RequestError as e:
            print(f"[Speech recognition service error: {e}]")
            return None
        except Exception:
            print("[Listening timed out]")
            return None
