import speech_recognition as sr
import asyncio
import edge_tts
import os
import pygame
import time

from config import VOICE_TAG

def speak_text(text):
    """
    Converts text to speech using Microsoft Edge TTS and plays it via pygame.
    This was the first working audio implementation.
    Voice is set in config.py under VOICE_TAG.
    """
    if not text or not text.strip():
        return

    output_file = "assistant_speech.mp3"

    async def generate_speech():
        communicate = edge_tts.Communicate(text, VOICE_TAG)
        await communicate.save(output_file)

    try:
        asyncio.run(generate_speech())

        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()
        pygame.mixer.quit()

    except Exception as e:
        print(f"[Audio error: {e}]")


def listen_to_user():
    """
    Captures microphone audio and returns it as text.
    Uses a 3.5-second pause threshold so the speaker is never cut off mid-sentence.
    """
    recognizer = sr.Recognizer()
    recognizer.pause_threshold       = 3.5
    recognizer.dynamic_energy_threshold = False

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        recognizer.energy_threshold = 300

        print("\n[Listening... Speak now]")
        try:
            audio_data = recognizer.listen(source, timeout=7, phrase_time_limit=None)
            print("Processing...")
            text = recognizer.recognize_google(audio_data)
            print(f'You said: "{text}"')
            return text
        except sr.UnknownValueError:
            print("[Could not understand audio]")
            return None
        except sr.RequestError as e:
            print(f"[Speech recognition error: {e}]")
            return None
        except Exception:
            print("[Listening timed out]")
            return None