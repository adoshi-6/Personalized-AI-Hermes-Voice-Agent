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
    """
    Routes queries to either the fast or smart model depending on complexity.
    Fast model: quick conversational replies.
    Smart model: triggered by 'think deeply', 'smart mode', or 'analyze'.
    """
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
                 "content": f"You are {ASSISTANT_NAME}, a warm, direct, and brief personal assistant."},
                {"role": "user", "content": user_query},
            ]
        )
        reply = response['message']['content']
        print(f"\n{ASSISTANT_NAME}: {reply}")
        speak_text(reply)
    except Exception as e:
        print(f"[Chat error: {e}]")


def main():
    print("\n" + "=" * 56)
    print(f"  {ASSISTANT_NAME} — Hybrid Model Mode")
    print(f"  Fast: {FAST_MODEL}  |  Smart: {SMART_MODEL}")
    print("=" * 56 + "\n")

    speak_text(f"System active, {USER_NAME}. Standing by.")

    while True:
        print("[Listening for wake word...]")
        wake_check = listen_to_user()

        if wake_check and ASSISTANT_NAME.lower() in wake_check.lower():
            print("[Wake phrase detected]")
            speak_text(f"Yes, {USER_NAME}?")

            user_command = listen_to_user()
            if not user_command:
                continue

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
