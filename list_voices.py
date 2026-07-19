import asyncio
import edge_tts


async def main():
 """
 Fetches and prints all available English neural voice codes from
 the Microsoft edge-tts service. Use these codes in config.py under VOICE_TAG.
 """
 try:
 voices = await edge_tts.list_voices()

 print("\n==================================================")
 print(" Available English Neural Voices (edge-tts)")
 print("==================================================")

 for v in voices:
 if v['ShortName'].startswith("en-"):
 print(f" Code: {v['ShortName']:<35} Gender: {v['Gender']}")

 print("==================================================\n")
 print(" Copy your preferred code and set it as VOICE_TAG in config.py")

 except Exception as e:
 print(f"[Failed to fetch voice list: {e}]")


if __name__ == "__main__":
 asyncio.run(main())