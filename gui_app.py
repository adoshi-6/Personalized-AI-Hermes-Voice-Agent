import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
import os
import time
import ollama

from audio_provider import speak_text, listen_to_user
from council import run_council_debate
from config import ASSISTANT_NAME, USER_NAME, FAST_MODEL, SMART_MODEL, COUNCIL_TRIGGERS


class VoiceAssistantGUI:
 """
 Final Tkinter GUI version — combines all previous fixes with
 short-term chat history memory. This is the last iteration of the
 desktop GUI before the project moved to a Flask web server and
 browser-based frontend.
 """
 def __init__(self, root):
 self.root = root
 self.root.title(f"{ASSISTANT_NAME}: Voice Assistant")
 self.root.geometry("700x550")
 self.root.configure(bg="#121212")

 # Short-term memory — cleared on restart
 self.chat_history = []

 self.status_label = tk.Label(
 root, text="SYSTEM STATUS: ONLINE",
 font=("Consolas", 10, "bold"),
 bg="#1a1a1a", fg="#00ffcc", anchor="w", pady=5
 )
 self.status_label.pack(fill=tk.X, padx=10, pady=(10, 5))

 self.log_display = scrolledtext.ScrolledText(
 root, wrap=tk.WORD, font=("Consolas", 11),
 bg="#1e1e1e", fg="#ffffff", insertbackground="#00ffcc"
 )
 self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

 self.log_display.tag_config("sys", foreground="#00ffcc")
 self.log_display.tag_config("user", foreground="#ffcc00")
 self.log_display.tag_config("CHRONOS", foreground="#ffffff")
 self.log_display.tag_config("err", foreground="#ff3333")

 self.input_frame = tk.Frame(root, bg="#121212")
 self.input_frame.pack(fill=tk.X, padx=10, pady=10)

 self.entry_field = tk.Entry(
 self.input_frame, font=("Consolas", 12),
 bg="#1e1e1e", fg="#ffffff",
 insertbackground="#00ffcc", borderwidth=1, relief=tk.SOLID
 )
 self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
 self.entry_field.bind("<Return>", lambda event: self.process_text_input())

 self.send_btn = tk.Button(
 self.input_frame, text="SEND", font=("Consolas", 10, "bold"),
 bg="#00ffcc", fg="#121212", activebackground="#00cc99",
 command=self.process_text_input, width=8, relief=tk.FLAT
 )
 self.send_btn.pack(side=tk.LEFT, padx=5)

 self.mic_btn = tk.Button(
 self.input_frame, text="MIC", font=("Consolas", 10, "bold"),
 bg="#ffcc00", fg="#121212", activebackground="#cc9900",
 command=self.trigger_voice_thread, width=8, relief=tk.FLAT
 )
 self.mic_btn.pack(side=tk.LEFT)

 self.append_log(f"{ASSISTANT_NAME} initialized. Standby...\n", "sys")
 threading.Thread(
 target=lambda: speak_text(f"System active, {USER_NAME}. Standing by."),
 daemon=True
 ).start()

 def append_log(self, text, tag):
 self.log_display.insert(tk.END, text, tag)
 self.log_display.see(tk.END)

 def set_status(self, text, color="#00ffcc"):
 self.status_label.config(text=text, fg=color)

 def should_trigger_council(self, text):
 text_lower = text.lower()
 negations = ["don't", "dont", "do not", "never", "without", "skip", "stop"]
 if not any(kw in text_lower for kw in COUNCIL_TRIGGERS):
 return False
 for neg in negations:
 if neg in text_lower:
 for kw in COUNCIL_TRIGGERS:
 if kw in text_lower and text_lower.find(neg) < text_lower.find(kw):
 return False
 return True

 def process_text_input(self):
 query = self.entry_field.get().strip()
 if not query:
 return
 self.entry_field.delete(0, tk.END)
 if query.lower() in ["exit", "quit"]:
 self.set_status("Shutting down...", "#ff3333")
 threading.Thread(
 target=lambda: [speak_text(f"Goodbye, {USER_NAME}."), self.root.quit()],
 daemon=True
 ).start()
 return
 threading.Thread(
 target=self.execute_pipeline, args=(query, "Typed"), daemon=True
 ).start()

 def trigger_voice_thread(self):
 threading.Thread(target=self.execute_voice_capture, daemon=True).start()

 def execute_voice_capture(self):
 self.set_status("Listening...", "#ffcc00")
 self.append_log("\n[Microphone open]\n", "sys")
 spoken_text = listen_to_user()
 if not spoken_text:
 self.set_status("SYSTEM STATUS: READY", "#00ffcc")
 self.append_log("[No speech recognized.]\n", "err")
 return
 self.execute_pipeline(spoken_text, "Voice")

 def execute_pipeline(self, command, source_type):
 self.append_log(f"\n{USER_NAME} ({source_type}): \"{command}\"\n", "user")

 if self.should_trigger_council(command):
 self.set_status("Council assembling...", "#ffcc00")
 self.append_log("Running council debate...\n", "sys")
 debate_packet = run_council_debate(command)

 self.append_log(f"\n[CONTRARIAN]:\n{debate_packet['contrarian']}\n", "CHRONOS")
 speak_text("Contrarian analysis.")
 speak_text(debate_packet['contrarian'])

 self.append_log(f"\n[SYNERGIST]:\n{debate_packet['synergist']}\n", "CHRONOS")
 speak_text("Synergist strategy.")
 speak_text(debate_packet['synergist'])

 self.append_log(f"\n[CHAIRMAN]:\n{debate_packet['chairman']}\n", "sys")
 speak_text("Chairman verdict.")
 speak_text(debate_packet['chairman'])

 else:
 text_lower = command.lower()
 if "think deeply" in text_lower or "smart mode" in text_lower or "analyze" in text_lower:
 active_model = SMART_MODEL
 self.set_status(f"Smart model: {SMART_MODEL}", "#ffcc00")
 else:
 active_model = FAST_MODEL
 self.set_status(f"Fast model: {FAST_MODEL}", "#00ffcc")

 messages = [
 {"role": "system",
 "content": f"You are {ASSISTANT_NAME}, a warm, direct, brief personal assistant. Always address {USER_NAME} as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses.."}
 ]
 messages.extend(self.chat_history)
 messages.append({"role": "user", "content": command})

 try:
 response = ollama.chat(model=active_model, messages=messages)
 reply = response['message']['content']
 self.append_log(f"{ASSISTANT_NAME}: {reply}\n", "CHRONOS")

 self.chat_history.append({"role": "user", "content": command})
 self.chat_history.append({"role": "assistant", "content": reply})
 if len(self.chat_history) > 20:
 self.chat_history = self.chat_history[-20:]

 speak_text(reply)
 except Exception as e:
 self.append_log(f"[Error: {e}]\n", "err")

 self.set_status("SYSTEM STATUS: READY", "#00ffcc")


if __name__ == "__main__":
 app_root = tk.Tk()
 app_instance = VoiceAssistantGUI(app_root)
 app_root.mainloop()
