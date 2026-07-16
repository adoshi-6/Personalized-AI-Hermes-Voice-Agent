import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
import os
import time
import ollama

# Import your locked, functional modules
from audio_provider import speak_text, listen_to_user
from council import run_council_debate

# 🤖 THE HYBRID ENGINE DECK
FAST_MODEL = "llama3.2:1b"
SMART_MODEL = "llama3.2:1b" # Qwen removed for context reasons, relying on Antigravity for coding

class ChronosGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CHRONOS: Cognitive Hermes Routing Orchestration and Neural Operations System")
        self.root.geometry("700x550")
        self.root.configure(bg="#121212") # Futuristic Dark Theme Base

        # 🧠 ACTIVE SHORT-TERM MEMORY BUFFER
        self.chat_history = []

        # --------------------------------------------------
        # 🎨 Sophisticated HUD INTERFACE LAYOUT
        # --------------------------------------------------
        # Top Status Indicator Bar
        self.status_label = tk.Label(root, text="⚡ SYSTEM STATUS: ONLINE [ARYAN.H.O.HYBRID.DECK]", 
                                     font=("Consolas", 10, "bold"), bg="#1a1a1a", fg="#00ffcc", anchor="w", pady=5)
        self.status_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Core Console Readout Display Log
        self.log_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 11), 
                                                     bg="#1e1e1e", fg="#ffffff", insertbackground="#00ffcc")
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure unique colored tagging text streams
        self.log_display.tag_config("sys", foreground="#00ffcc")   # Neon Teal System Alert
        self.log_display.tag_config("aryan", foreground="#ffcc00") # Amber Aryan Output
        self.log_display.tag_config("CHRONOS", foreground="#ffffff")   # Clean White Response
        self.log_display.tag_config("err", foreground="#ff3333")   # Crimson Pipeline Failure

        # Bottom Input Dock Framework
        self.input_frame = tk.Frame(root, bg="#121212")
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Manual Entry Field
        self.entry_field = tk.Entry(self.input_frame, font=("Consolas", 12), bg="#1e1e1e", fg="#ffffff", 
                                    insertbackground="#00ffcc", borderwidth=1, relief=tk.SOLID)
        self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry_field.bind("<Return>", lambda event: self.process_text_input())

        # Operation Action Buttons
        self.send_btn = tk.Button(self.input_frame, text="SEND", font=("Consolas", 10, "bold"), 
                                  bg="#00ffcc", fg="#121212", activebackground="#00cc99", 
                                  command=self.process_text_input, width=8, relief=tk.FLAT)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.mic_btn = tk.Button(self.input_frame, text="🎙️ MIC", font=("Consolas", 10, "bold"), 
                                 bg="#ffcc00", fg="#121212", activebackground="#cc9900", 
                                 command=self.trigger_voice_thread, width=8, relief=tk.FLAT)
        self.mic_btn.pack(side=tk.LEFT)

        # Print initial boot diagnostics to the log display window
        self.append_log("🚀 CHRONOS Protocol Initialized. Standby for input connection...\n", "sys")
        
        # Run standard startup greeting voice inside a safe non-blocking background thread
        threading.Thread(target=lambda: speak_text("System active, Aryan. Standing by."), daemon=True).start()

    # --------------------------------------------------
    # 🧠 CORE ENGINE INTELLIGENCE MATRIX
    # --------------------------------------------------
    def append_log(self, text, tag):
        """Appends formatted messages to the GUI display log safely."""
        self.log_display.insert(tk.END, text, tag)
        self.log_display.see(tk.END)

    def set_status(self, text, color="#00ffcc"):
        """Dynamically switches the text color and readout message of the top HUD bar."""
        self.status_label.config(text=text, fg=color)

    def should_trigger_council(self, text):
        """Checks for council trigger keywords while respecting intent negation modifiers."""
        text_lower = text.lower()
        triggers = ["council", "debate", "evaluate"]
        negations = ["don't", "dont", "do not", "never", "without", "skip", "stop"]
        
        if not any(kw in text_lower for kw in triggers):
            return False
            
        for neg in negations:
            if neg in text_lower:
                for kw in triggers:
                    if kw in text_lower and text_lower.find(neg) < text_lower.find(kw):
                        return False
        return True

    def process_text_input(self):
        """Extracts the manual string from the entry box and boots the computing pipeline."""
        query = self.entry_field.get().strip()
        if not query:
            return
            
        self.entry_field.delete(0, tk.END)
        
        if query.lower() in ["exit", "quit"]:
            self.set_status("🚪 DETACHING CLIENT NODE... GOODBYE", "#ff3333")
            self.append_log(f"\n📝 Command captured: \"{query}\"\n", "sys")
            threading.Thread(target=lambda: [speak_text("Systems shutting down. Goodbye, Aryan."), self.root.quit()], daemon=True).start()
            return

        threading.Thread(target=self.execute_pipeline, args=(query, "Typed Input"), daemon=True).start()

    def trigger_voice_thread(self):
        """Fires off an independent worker thread to poll mic data without freezing the window UI."""
        threading.Thread(target=self.execute_voice_capture, daemon=True).start()

    def execute_voice_capture(self):
        """Controls audio capturing state mechanics cleanly."""
        self.set_status("🎙️ LISTENING TO AMBIENT MIC WAVEFORM...", "#ffcc00")
        self.append_log("\n🎙️ [Microphone Channel Open: Speak now]\n", "sys")
        
        spoken_text = listen_to_user()
        if not spoken_text:
            self.set_status("⚡ SYSTEM STATUS: READY", "#00ffcc")
            self.append_log("⚠️ [No vocal input data recognized. Loop aborted.]\n", "err")
            return
            
        self.execute_pipeline(spoken_text, "Vocal Stream")

    def execute_pipeline(self, command, source_type):
        """Main computational pipeline. Routes data streams and manages model generation."""
        self.append_log(f"\n👤 ARYAN ({source_type}): \"{command}\"\n", "aryan")
        
        if self.should_trigger_council(command):
            self.set_status("👥 COUNCIL ASSEMBLED: AGENTS GENERATING DATA...", "#ffcc00")
            self.append_log("⏳ Calling Council Boardroom (6 Agents)...\n", "sys")

            # BUG FIX: council.py previously returned a plain string; it now returns a dict
            # with keys: contrarian, first_principles, expansionist, outsider, executor, chairman
            debate_packet = run_council_debate(command)

            self.append_log(f"\n🎭 [CONTRARIAN]:\n{debate_packet.get('contrarian', '')}\n", "CHRONOS")
            speak_text("Contrarian analysis.")
            speak_text(debate_packet.get('contrarian', ''))

            self.append_log(f"\n🔬 [FIRST PRINCIPLES]:\n{debate_packet.get('first_principles', '')}\n", "CHRONOS")
            speak_text("First principles baseline.")
            speak_text(debate_packet.get('first_principles', ''))

            self.append_log(f"\n🚀 [EXPANSIONIST]:\n{debate_packet.get('expansionist', '')}\n", "CHRONOS")
            speak_text("Expansionist strategy.")
            speak_text(debate_packet.get('expansionist', ''))

            self.append_log(f"\n👁️ [OUTSIDER]:\n{debate_packet.get('outsider', '')}\n", "CHRONOS")
            speak_text("Outsider perspective.")
            speak_text(debate_packet.get('outsider', ''))

            self.append_log(f"\n⚡ [EXECUTOR]:\n{debate_packet.get('executor', '')}\n", "CHRONOS")
            speak_text("Executor directive.")
            speak_text(debate_packet.get('executor', ''))

            self.append_log(f"\n🏛️ [CHAIRMAN]:\n{debate_packet.get('chairman', '')}\n", "sys")
            speak_text("Chairman's final verdict.")
            speak_text(debate_packet.get('chairman', ''))

        else:
            text_lower = command.lower()
            if "think deeply" in text_lower or "smart mode" in text_lower or "analyze" in text_lower:
                active_model = SMART_MODEL
                self.set_status(f"🧠 RUNNING HEAVY LOGIC LAYER ({active_model})...", "#ffcc00")
                self.append_log(f"🧠 Routing to High-Capacity Logic Engine ({active_model})...\n", "sys")
            else:
                active_model = FAST_MODEL
                self.set_status(f"⚡ RUNNING OPTIMAL SPEED LAYER ({active_model})...", "#00ffcc")
                self.append_log(f"⚡ Routing to Low-Latency Speed Engine ({active_model})...\n", "sys")

            messages_payload =[
                {"role": "system", "content": "You are CHRONOS, an elite, highly intelligent desktop GUI AI assistant customized for Aryan. Always address him as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses."}
            ]
            messages_payload.extend(self.chat_history)
            messages_payload.append({"role": "user", "content": command})

            try:
                response = ollama.chat(model=active_model, messages=messages_payload)
                reply = response['message']['content']
                self.append_log(f"🤖 CHRONOS: {reply}\n", "CHRONOS")
                
                self.chat_history.append({"role": "user", "content": command})
                self.chat_history.append({"role": "assistant", "content": reply})
                
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]

                speak_text(reply)
            except Exception as e:
                self.append_log(f"❌ Core link drop exception: {e}\n", "err")

        self.set_status("⚡ SYSTEM STATUS: READY", "#00ffcc")

# --------------------------------------------------
# 🚀 THE ENGINE STARTER (CRITICAL: Make sure this is saved!)
# --------------------------------------------------
if __name__ == "__main__":
    app_root = tk.Tk()
    app_instance = ChronosGUIApp(app_root)
    app_root.mainloop()