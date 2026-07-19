import asyncio
import edge_tts
import os
import ctypes
import time

from config import USER_NAME, ASSISTANT_NAME

# The 6 finalist voices after narrowing down from the full global library.
# Controls: press Enter to replay, 'n' for next, 'q' to quit.
# Set your final choice in config.py under VOICE_TAG.
SHORTLIST_VOICES = [
 {"name": "Liam (Canada - Smooth & Grounded)", "tag": "en-CA-LiamNeural"},
 {"name": "Ryan (UK - Deep Cinematic)", "tag": "en-GB-RyanNeural"},
 {"name": "James (Philippines - Clear & Articulate)", "tag": "en-PH-JamesNeural"},
 {"name": "Wayne (Singapore - Dynamic)", "tag": "en-SG-WayneNeural"},
 {"name": "Andrew (US - Deep Casual)", "tag": "en-US-AndrewNeural"},
 {"name": "Eric (US - Sharp & Clear)", "tag": "en-US-EricNeural"},
]


def play_audio(file_path):
 """Plays an MP3 file using the native Windows audio layer."""
 abs_path = os.path.abspath(file_path)
 alias = "shortlist_voice"

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
 print("==================================================")
 print(" Voice Finals: Shortlist")
 print(" [ENTER] Replay | [N] Next | [Q] Quit")
 print("==================================================")

 idx = 0
 while idx < len(SHORTLIST_VOICES):
 speaker = SHORTLIST_VOICES[idx]
 print(f"\nFinalist [{idx + 1}/{len(SHORTLIST_VOICES)}]: {speaker['name']}")
 print(f" Tag: {speaker['tag']}")

 sample_text = (
 f"Hello {USER_NAME}. Testing the {speaker['name'].split('(')[0].strip()} "
 f"voice for {ASSISTANT_NAME}. How do I sound?"
 )
 safe_filename = f"shortlist_sample_{idx}.mp3"

 if not os.path.exists(safe_filename):
 communicate = edge_tts.Communicate(sample_text, speaker['tag'])
 await communicate.save(safe_filename)

 play_audio(safe_filename)

 action = input("[ENTER] replay | 'n' next | 'q' quit: ").strip().lower()

 if action == 'q':
 break
 elif action == 'n':
 idx += 1

 print("\nCleaning up...")
 for i in range(len(SHORTLIST_VOICES)):
 f = f"shortlist_sample_{i}.mp3"
 if os.path.exists(f):
 try:
 os.remove(f)
 except Exception:
 pass

 print("\n==================================================")
 print(" Review complete. Set your choice in config.py")
 print("==================================================\n")


if __name__ == "__main__":
 asyncio.run(main())