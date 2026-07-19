import sys
import os
import time
from audio_provider import speak_text, listen_to_user
from council import run_council_debate
import ollama

# THE HYBRID ENGINE DECK
FAST_MODEL = "llama3.2:1b"
SMART_MODEL = "llama3.2:1b" # Qwen removed for context reasons, relying on Antigravity for coding

def should_trigger_council(user_input):
 """Analyzes intent to prevent false-positives."""
 text = user_input.lower()
 triggers = ["council", "debate", "evaluate"]
 negations = ["don't", "dont", "do not", "never", "without", "skip", "stop"]
 
 if not any(kw in text for kw in triggers):
 return False
 
 for neg in negations:
 if neg in text:
  for kw in triggers:
  if kw in text and text.find(neg) < text.find(kw):
   print(f" [Negation Shield Tripped: Bypassing Council Feature]")
   return False
 return True

def handle_standard_chat(user_query):
 """Routes standard chat requests based on required depth."""
 text = user_query.lower()
 
 # SMART TRIGGER CHECK
 if "think deeply" in text or "smart mode" in text or "analyze" in text:
 active_model = SMART_MODEL
 print(f" [Scaling Up Engine: Routing transaction through {SMART_MODEL}...]")
 else:
 active_model = FAST_MODEL
 print(f" [Pacing Optimal: Routing transaction through {FAST_MODEL}...]")

 try:
 response = ollama.chat(
  model=active_model,
  messages=[
  {"role": "system", "content": "You are CHRONOS, an elite, highly intelligent desktop AI assistant customized for Aryan. Always address him as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses."},
  {"role": "user", "content": user_query}
  ]
 )
 reply = response['message']['content']
 print(f"\nChronos: {reply}")
 speak_text(reply)
 except Exception as e:
 print(f" Core processing link exception: {e}")

def main():
 print("\n========================================================")
 print(" CHRONOS PROTOCOL INITIALIZED: INTERACTIVE UI RESTORED ")
 print(" Fast Core: Llama 1B | Heavy Logic Core: Antigravity/Claude ")
 print("========================================================\n")
 
 speak_text("System active, Aryan. Standing by.")
 
 while True:
 user_choice = input("\n️ [Press ENTER to Talk / Or type your command]: ").strip()
 
 user_command = None
 
 # Scenario A: User hits Enter on an empty line -> Fire up microphone
 if user_choice == "":
  user_command = listen_to_user()
  if not user_command:
  print("️ [No speech captured. Returning to idle command line.]")
  continue
 
 # Scenario B: User typed out a text instruction manually -> Process string
 else:
  user_command = user_choice
  print(f" Captured typed input: \"{user_command}\"")
  
 # THE SYSTEM EXIT DOOR
 # Intercepts the command before it ever touches the ENGINE models
 if user_command.lower() in ["exit", "quit"]:
  print("\n [Exiting CHRONOS Protocol. Disconnecting local nodes...]")
  speak_text("Systems shutting down. Goodbye, Aryan.")
  sys.exit(0)
  
 # Unified processing stream for both input methods
 if should_trigger_council(user_command):
  # BUG FIX: run_council_debate now returns a 6-key dict, not a string
  debate_packet = run_council_debate(user_command)

  print(f"\n [CONTRARIAN]:\n{debate_packet.get('contrarian', '')}")
  speak_text("Contrarian analysis.")
  speak_text(debate_packet.get('contrarian', ''))
  time.sleep(0.3)

  print(f"\n [FIRST PRINCIPLES]:\n{debate_packet.get('first_principles', '')}")
  speak_text("First principles baseline.")
  speak_text(debate_packet.get('first_principles', ''))
  time.sleep(0.3)

  print(f"\n [EXPANSIONIST]:\n{debate_packet.get('expansionist', '')}")
  speak_text("Expansionist strategy.")
  speak_text(debate_packet.get('expansionist', ''))
  time.sleep(0.3)

  print(f"\n️ [OUTSIDER]:\n{debate_packet.get('outsider', '')}")
  speak_text("Outsider perspective.")
  speak_text(debate_packet.get('outsider', ''))
  time.sleep(0.3)

  print(f"\n [EXECUTOR]:\n{debate_packet.get('executor', '')}")
  speak_text("Executor directive.")
  speak_text(debate_packet.get('executor', ''))
  time.sleep(0.3)

  print(f"\n️ [CHAIRMAN]:\n{debate_packet.get('chairman', '')}")
  speak_text("Chairman's final verdict.")
  speak_text(debate_packet.get('chairman', ''))
 else:
  handle_standard_chat(user_command)
  
 time.sleep(0.1)

if __name__ == "__main__":
 try:
 main()
 except KeyboardInterrupt:
 print("\nGateway shutdown. Systems safely disconnected.")
 sys.exit(0)