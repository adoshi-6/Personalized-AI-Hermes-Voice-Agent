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

def is_speaking():
    return _speak_lock.locked()


def speak_text(text, voice_mode="standard"):
    """
    Converts text to speech using the Ryan (UK) voice.
    Blocks until playback is fully complete (play wait).
    """
    if not text or not text.strip():
        return

    output_file = os.path.abspath("ace_speech.mp3")
    from config import VOICE_TAG
    selected_voice = VOICE_TAG

    async def generate_speech():
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_file)

    with _speak_lock:
        try:
            asyncio.run(generate_speech())
            ctypes.windll.winmm.mciSendStringW(
                f'open "{output_file}" type mpegvideo alias ace_audio', None, 0, 0)
            # "play wait" blocks until playback is done — no polling loop needed
            ctypes.windll.winmm.mciSendStringW('play ace_audio wait', None, 0, 0)
            ctypes.windll.winmm.mciSendStringW('close ace_audio', None, 0, 0)
        except Exception as e:
            print(f"[Audio pipeline error: {e}]")

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
