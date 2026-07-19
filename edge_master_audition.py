import asyncio
import edge_tts
import os
import ctypes
import time

from config import USER_NAME, ASSISTANT_NAME

# Full 47-voice interactive audition tool.
# Controls: [ENTER] replay, [N] next, [Q] quit.
# Set your final choice in config.py under VOICE_TAG.
ALL_VOICES = [
 {"name": "William (Australia - Multilingual)", "tag": "en-AU-WilliamMultilingualNeural"},
 {"name": "Natasha (Australia)", "tag": "en-AU-NatashaNeural"},
 {"name": "Clara (Canada)",  "tag": "en-CA-ClaraNeural"},
 {"name": "Liam (Canada)",  "tag": "en-CA-LiamNeural"},
 {"name": "Yan (Hong Kong)",  "tag": "en-HK-YanNeural"},
 {"name": "Sam (Hong Kong)",  "tag": "en-HK-SamNeural"},
 {"name": "Neerja (India - Expressive)", "tag": "en-IN-NeerjaExpressiveNeural"},
 {"name": "Neerja (India)",  "tag": "en-IN-NeerjaNeural"},
 {"name": "Prabhat (India)",  "tag": "en-IN-PrabhatNeural"},
 {"name": "Connor (Ireland)",  "tag": "en-IE-ConnorNeural"},
 {"name": "Emily (Ireland)",  "tag": "en-IE-EmilyNeural"},
 {"name": "Asilia (Kenya)",  "tag": "en-KE-AsiliaNeural"},
 {"name": "Chilemba (Kenya)",  "tag": "en-KE-ChilembaNeural"},
 {"name": "Mitchell (New Zealand)", "tag": "en-NZ-MitchellNeural"},
 {"name": "Molly (New Zealand)", "tag": "en-NZ-MollyNeural"},
 {"name": "Abeo (Nigeria)",  "tag": "en-NG-AbeoNeural"},
 {"name": "Ezinne (Nigeria)",  "tag": "en-NG-EzinneNeural"},
 {"name": "James (Philippines)", "tag": "en-PH-JamesNeural"},
 {"name": "Rosa (Philippines)",  "tag": "en-PH-RosaNeural"},
 {"name": "Luna (Singapore)",  "tag": "en-SG-LunaNeural"},
 {"name": "Wayne (Singapore)",  "tag": "en-SG-WayneNeural"},
 {"name": "Elimu (Tanzania)",  "tag": "en-TZ-ElimuNeural"},
 {"name": "Imani (Tanzania)",  "tag": "en-TZ-ImaniNeural"},
 {"name": "Libby (UK)",  "tag": "en-GB-LibbyNeural"},
 {"name": "Maisie (UK)",  "tag": "en-GB-MaisieNeural"},
 {"name": "Ryan (UK - Cinematic)", "tag": "en-GB-RyanNeural"},
 {"name": "Sonia (UK - Elegant)", "tag": "en-GB-SoniaNeural"},
 {"name": "Thomas (UK)",  "tag": "en-GB-ThomasNeural"},
 {"name": "Leah (South Africa)", "tag": "en-ZA-LeahNeural"},
 {"name": "Luke (South Africa)", "tag": "en-ZA-LukeNeural"},
 {"name": "Ava (US)",  "tag": "en-US-AvaNeural"},
 {"name": "Andrew (US - Deep Casual)", "tag": "en-US-AndrewNeural"},
 {"name": "Emma (US)",  "tag": "en-US-EmmaNeural"},
 {"name": "Brian (US - Corporate)", "tag": "en-US-BrianNeural"},
 {"name": "Ana (US)",  "tag": "en-US-AnaNeural"},
 {"name": "Andrew (US - Multilingual)", "tag": "en-US-AndrewMultilingualNeural"},
 {"name": "Aria (US)",  "tag": "en-US-AriaNeural"},
 {"name": "Ava (US - Multilingual)", "tag": "en-US-AvaMultilingualNeural"},
 {"name": "Brian (US - Multilingual)", "tag": "en-US-BrianMultilingualNeural"},
 {"name": "Christopher (US - Energetic)", "tag": "en-US-ChristopherNeural"},
 {"name": "Emma (US - Multilingual)", "tag": "en-US-EmmaMultilingualNeural"},
 {"name": "Eric (US)",  "tag": "en-US-EricNeural"},
 {"name": "Guy (US)",  "tag": "en-US-GuyNeural"},
 {"name": "Jenny (US)",  "tag": "en-US-JennyNeural"},
 {"name": "Michelle (US)",  "tag": "en-US-MichelleNeural"},
 {"name": "Roger (US)",  "tag": "en-US-RogerNeural"},
 {"name": "Steffan (US)",  "tag": "en-US-SteffanNeural"},
]


def play_audio(file_path):
 """Plays an MP3 file using the native Windows audio layer."""
 abs_path = os.path.abspath(file_path)
 alias = "master_audition"
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


async def main():
 print("==========================================================")
 print(" Master Voice Audition — 47 Global Voices")
 print(" [ENTER] Replay | [N] Next | [Q] Quit")
 print("==========================================================")

 total = len(ALL_VOICES)
 idx = 0

 while idx < total:
 speaker = ALL_VOICES[idx]
 print(f"\n[{idx + 1}/{total}] {speaker['name']}")
 print(f" Tag: {speaker['tag']}")

 safe_filename = f"audition_clip_{idx}.mp3"

 if not os.path.exists(safe_filename):
 try:
 sample_text = (
  f"Hello {USER_NAME}. This is the "
  f"{speaker['name'].split('(')[0].strip()} voice. "
  f"How do I sound for {ASSISTANT_NAME}?"
 )
 communicate = edge_tts.Communicate(sample_text, speaker['tag'])
 await communicate.save(safe_filename)
 except Exception as e:
 print(f" [Generation failed: {e}]")
 idx += 1
 continue

 play_audio(safe_filename)

 action = input("[ENTER] replay | 'n' next | 'q' quit: ").strip().lower()
 if action == 'q':
 break
 elif action == 'n':
 idx += 1

 print("\nCleaning up...")
 for i in range(total):
 f = f"audition_clip_{i}.mp3"
 if os.path.exists(f):
 try:
 os.remove(f)
 except Exception:
 pass

 print("\n==========================================================")
 print(" Done. Set your chosen voice in config.py under VOICE_TAG")
 print("==========================================================\n")


if __name__ == "__main__":
 asyncio.run(main())