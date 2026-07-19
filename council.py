import ollama
import re

# ==================================================
# MODEL SELECTION
# Set this to the model you have pulled in Model server.
# ==================================================
LOCAL_MODEL = "qwen3:4b" # Updated — qwen2.5-coder removed, use smart model


def _chat(prompt_system: str, prompt_user: str) -> str:
 """Single call to the local model. Strips <think> blocks from reasoning models."""
 try:
 response = ollama.chat(
  model=LOCAL_MODEL,
  messages=[
  {"role": "system", "content": prompt_system},
  {"role": "user", "content": prompt_user},
  ]
 )
 raw = response['message']['content']
 # Strip reasoning blocks emitted by deepseek/qwen thinking models
 return re.sub(r'<think>[\s\S]*?</think>', '', raw).strip()
 except Exception as e:
 return f"[Agent unavailable: {e}]"


def run_council_debate(user_idea: str) -> dict:
 """
 Runs a full 7-seat council debate on the user's idea.

 Returns a dict with keys:
 contrarian, first_principles, expansionist, outsider, executor, rainmaker, chairman

 BUG FIX (v2): previously returned a plain string, which caused KeyError
 crashes in gui_app.py and main.py whenever council was triggered.
 """
 print("\n==================================================")
 print(" COUNCIL CHAMBER ACTIVE: INITIATING DEBATE ")
 print("==================================================")

 import json
 import os
 config_path = os.path.join(os.path.dirname(__file__), "council_config.json")
 with open(config_path, "r", encoding="utf-8") as f:
 config = json.load(f)

 # --- Seat 1: The Contrarian ---
 print("\n[1/7] The Contrarian...")
 text1 = _chat(config["contrarian"]["system"], config["contrarian"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 2: First Principles Thinker ---
 print("[2/7] First Principles Thinker...")
 text2 = _chat(config["first_principles"]["system"], config["first_principles"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 3: The Expansionist ---
 print("[3/7] The Expansionist...")
 text3 = _chat(config["expansionist"]["system"], config["expansionist"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 4: The Outsider ---
 print("[4/7] The Outsider...")
 text4 = _chat(config["outsider"]["system"], config["outsider"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 5: The Executor ---
 print("[5/7] The Executor...")
 text5 = _chat(config["executor"]["system"], config["executor"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 6: The Rainmaker ---
 print("[6/7] The Rainmaker...")
 text6 = _chat(config["rainmaker"]["system"], config["rainmaker"]["prompt"].format(idea=user_idea))
 print(" done.")

 # --- Seat 7: The Chairman ---
 print("[7/7] The Chairman (synthesis)...")
 chairman_context = config["chairman"]["prompt"].format(
 idea=user_idea,
 contrarian=text1,
 first_principles=text2,
 expansionist=text3,
 outsider=text4,
 executor=text5,
 rainmaker=text6
 )
 text7 = _chat(config["chairman"]["system"], chairman_context)
 print(" done.")

 print("\n==================================================")
 print(" DEBATE COMPLETE. RETURNING VERDICT PACKET. ")
 print("==================================================\n")

 return {
 "contrarian": text1,
 "first_principles": text2,
 "expansionist": text3,
 "outsider": text4,
 "executor": text5,
 "rainmaker": text6,
 "chairman": text7,
 }