import speech_recognition as sr
import asyncio
import edge_tts
import os
import ctypes
import time
import threading
import uuid
import glob

# Global speaking lock — prevents two TTS calls overlapping.
# speak_text blocks until audio finishes so /api/speak only returns
# when CHRONOS has truly finished speaking — which is what keeps the
# frontend mic muted for exactly the right duration.
_speak_lock = threading.Lock()
_active_speech_threads = 0
_counter_lock = threading.Lock()

# Dedicated cache folder for generated speech clips. Using a fresh filename
# per utterance (instead of one shared "CHRONOS_SPEECH.mp3") is what fixes
# the "audio randomly stops working" bug below.
_AUDIO_CACHE_DIR = os.path.abspath("CHRONOS_AUDIO_CACHE")
os.makedirs(_AUDIO_CACHE_DIR, exist_ok=True)


is_currently_speaking = False


def is_speaking():
 return is_currently_speaking or _speak_lock.locked()


def stop_all_audio():
 global is_currently_speaking
 is_currently_speaking = False
 _mci('close all')


def stop_all_audio():
 global is_currently_speaking
 is_currently_speaking = False
 _mci('close all')


def _mci(command: str) -> bool:
 """Runs a single MCI command. Never raises — returns True/False so
 cleanup steps can always be attempted regardless of earlier failures."""
 try:
 return ctypes.windll.winmm.mciSendStringW(command, None, 0, 0) == 0
 except Exception as e:
 print(f"[MCI error on '{command}': {e}]")
 return False


def _cleanup_old_clips(keep_last: int = 5):
 """Best-effort trim of old cached clips so the folder doesn't grow forever."""
 try:
 files = sorted(glob.glob(os.path.join(_AUDIO_CACHE_DIR, "*.mp3")), key=os.path.getmtime)
 for stale in files[:-keep_last] if len(files) > keep_last else []:
 try:
 os.remove(stale)
 except Exception:
 pass
 except Exception:
 pass


VOICE_MAP = {
 "standard": "en-GB-RyanNeural",
 "contrarian": "en-GB-SoniaNeural",
 "first_principles": "en-GB-ThomasNeural",
 "expansionist": "en-US-GuyNeural",
 "outsider": "en-US-AriaNeural",
 "executor": "en-US-ChristopherNeural",
 "rainmaker": "en-US-EricNeural",
 "chairman": "en-US-AndrewNeural",
 "conductor": "en-GB-RyanNeural",
}


def speak_text(text, voice_mode="standard"):
 """
 Converts text to speech using a mapped model voice (Edge-TTS).
 Blocks until playback is fully complete (play wait).
 """
 global is_currently_speaking, _active_speech_threads
 if not text or not text.strip():
 # Decrement counter if we return early
 with _counter_lock:
 if _active_speech_threads <= 0:
 is_currently_speaking = False
 return
 # Prepend a small pause to let the audio hardware wake up without truncating the first words
 text = "... " + text.lstrip(". ")

 with _counter_lock:
 _active_speech_threads += 1
 is_currently_speaking = True
 clip_id = uuid.uuid4().hex
 output_file = os.path.join(_AUDIO_CACHE_DIR, f"chronos_{clip_id}.mp3")
 alias = f"chronos_audio_{clip_id[:8]}"
 selected_voice = VOICE_MAP.get(voice_mode, "en-GB-RyanNeural")

 async def generate_speech():
 communicate = edge_tts.Communicate(text, selected_voice)
 await communicate.save(output_file)

 try:
 with _speak_lock:
 try:
 asyncio.run(generate_speech())
 except Exception as e:
 print(f"[TTS generation error: {e}]")
 return

 try:
 if not _mci(f'open "{output_file}" type mpegvideo alias {alias}'):
  print(f"[Audio pipeline error: could not open clip {clip_id}]")
  return
 # "play wait" blocks until playback is done — no polling loop needed
 _mci(f'play {alias} wait')
 finally:
 # Always release the device and delete the temp file, even if
 # playback threw — this is exactly what was jamming later replies.
 _mci(f'close {alias}')
 try:
  os.remove(output_file)
 except Exception:
  pass
 _cleanup_old_clips()
 finally:
 with _counter_lock:
 _active_speech_threads -= 1
 if _active_speech_threads <= 0:
 is_currently_speaking = False

def listen_to_user():
 """Captures microphone audio with an expanded window for long sentences."""
 recognizer = sr.Recognizer()
 recognizer.pause_threshold = 3.5
 recognizer.dynamic_energy_threshold = False
 
 with sr.Microphone() as source:
 recognizer.adjust_for_ambient_noise(source, duration=0.5)
 recognizer.energy_threshold = 300
 
 print("\n️ [Listening... Speak now]")
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