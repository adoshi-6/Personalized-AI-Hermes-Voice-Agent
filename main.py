import sys
import os
import time
from audio_provider import speak_text, listen_to_user
from council import run_council_debate
import ollama

from config import ASSISTANT_NAME, USER_NAME, FAST_MODEL, SMART_MODEL, COUNCIL_TRIGGERS


def should_trigger_council(user_input: str) -> bool:
    """Detects council keywords while respecting negation modifiers."""
    text      = user_input.lower()
    negations = ["don't", "dont", "do not", "never", "without", "skip", "stop"]

    if not any(kw in text for kw in COUNCIL_TRIGGERS):
        return False

    for neg in negations:
        if neg in text:
            for kw in COUNCIL_TRIGGERS:
                if kw in text and text.find(neg) < text.find(kw):
                    return False
    return True


def handle_standard_chat(user_query: str):
    """Routes to fast or smart model based on complexity keywords."""
    text = user_query.lower()

    if "think deeply" in text or "smart mode" in text or "analyze" in text:
        active_model = SMART_MODEL
        print(f"[Smart model: {SMART_MODEL}]")
    else:
        active_model = FAST_MODEL
        print(f"[Fast model: {FAST_MODEL}]")

    try:
        response = ollama.chat(
            model=active_model,
            messages=[
                {"role": "system",
                 "content": f"You are {ASSISTANT_NAME}, a warm, direct, and brief personal assistant. Always address {USER_NAME} as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses.."},
                {"role": "user", "content": user_query},
            ]
        )
        reply = response['message']['content']
        print(f"\n{ASSISTANT_NAME}: {reply}")
        speak_text(reply)
    except Exception as e:
        print(f"[Chat error: {e}]")


def main():
    """
    Dual-input mode with exit command.
    Added 'exit' and 'quit' as graceful shutdown keywords,
    intercepted before reaching the AI models.
    """
    print("\n" + "=" * 56)
    print(f"  {ASSISTANT_NAME} — Voice + Keyboard Mode")
    print(f"  Press [ENTER] to talk, or type your command.")
    print(f"  Type 'exit' or 'quit' to shut down.")
    print("=" * 56 + "\n")

    speak_text(f"System active, {USER_NAME}. Standing by.")

    while True:
        user_choice = input("\n[Press ENTER to talk / or type your command]: ").strip()

        if user_choice == "":
            user_command = listen_to_user()
            if not user_command:
                print("[No speech captured. Try again.]")
                continue
        else:
            user_command = user_choice
            print(f'[Typed input: "{user_command}"]')

        # Clean exit gate — checked before routing to any model
        if user_command.lower() in ["exit", "quit"]:
            print("\n[Shutting down...]")
            speak_text(f"Goodbye, {USER_NAME}.")
            sys.exit(0)

        if should_trigger_council(user_command):
            debate_packet = run_council_debate(user_command)

            print(f"\n[CONTRARIAN]:\n{debate_packet['contrarian']}")
            speak_text("Contrarian analysis.")
            speak_text(debate_packet['contrarian'])
            time.sleep(0.5)

            print(f"\n[SYNERGIST]:\n{debate_packet['synergist']}")
            speak_text("Synergist strategy.")
            speak_text(debate_packet['synergist'])
            time.sleep(0.5)

            print(f"\n[CHAIRMAN]:\n{debate_packet['chairman']}")
            speak_text("Chairman verdict.")
            speak_text(debate_packet['chairman'])
        else:
            handle_standard_chat(user_command)

        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down.")
        sys.exit(0)
