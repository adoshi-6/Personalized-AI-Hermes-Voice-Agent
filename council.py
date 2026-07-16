import ollama
import re

# ==================================================
# MODEL SELECTION
# Set this to the model you have pulled in Ollama.
# ==================================================
from config import SMART_MODEL
LOCAL_MODEL = SMART_MODEL


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
    print(" COUNCIL CHAMBER ACTIVE: INITIATING DEBATE        ")
    print("==================================================")

    # --- Seat 1: The Contrarian ---
    print("\n[1/7] The Contrarian...")
    text1 = _chat(
        "You are The Contrarian. Highlight every critical risk, flaw, and reason "
        "this plan will fail. Be direct and ruthless. Maximum 2 sentences.",
        f"Identify vulnerabilities: {user_idea}"
    )
    print("  done.")

    # --- Seat 2: First Principles Thinker ---
    print("[2/7] First Principles Thinker...")
    text2 = _chat(
        "You are the First Principles Thinker. Strip all assumptions and analogies. "
        "Rebuild the core logic from raw axioms. Maximum 2 sentences.",
        f"Deconstruct and rebuild from first principles: {user_idea}"
    )
    print("  done.")

    # --- Seat 3: The Expansionist ---
    print("[3/7] The Expansionist...")
    text3 = _chat(
        "You are The Expansionist. Uncover the biggest hidden upside, scalability plays, "
        "and opportunities being missed. Maximum 2 sentences.",
        f"Maximize scale and upside: {user_idea}"
    )
    print("  done.")

    # --- Seat 4: The Outsider ---
    print("[4/7] The Outsider...")
    text4 = _chat(
        "You are The Outsider. Evaluate this with complete objectivity, "
        "zero jargon, and no emotional attachment. Maximum 2 sentences.",
        f"Evaluate neutrally: {user_idea}"
    )
    print("  done.")

    # --- Seat 5: The Executor ---
    print("[5/7] The Executor...")
    text5 = _chat(
        "You are The Executor. Focus purely on what to do next. "
        "Give the single most concrete, actionable next step. Maximum 2 sentences.",
        f"What is the immediate next action? {user_idea}"
    )
    print("  done.")

    # --- Seat 6: The Rainmaker ---
    print("[6/7] The Rainmaker...")
    text6 = _chat(
        "You are The Rainmaker. Think like an investor, entrepreneur, and dealmaker. "
        "Evaluate through the lens of revenue, ROI, market positioning, and monetization. Maximum 2 sentences.",
        f"Evaluate financial upside and investment-worthiness: {user_idea}"
    )
    print("  done.")

    # --- Seat 7: The Chairman ---
    print("[7/7] The Chairman (synthesis)...")
    chairman_context = (
        f"Objective: {user_idea}\n\n"
        f"Contrarian: {text1}\n\n"
        f"First Principles: {text2}\n\n"
        f"Expansionist: {text3}\n\n"
        f"Outsider: {text4}\n\n"
        f"Executor: {text5}\n\n"
        f"Rainmaker: {text6}"
    )
    text7 = _chat(
        "You are The Chairman. Read all six agent briefs and deliver one clear, "
        "unified recommendation — the single best path forward. Maximum 3 sentences.",
        chairman_context
    )
    print("  done.")

    print("\n==================================================")
    print(" DEBATE COMPLETE. RETURNING VERDICT PACKET.        ")
    print("==================================================\n")

    return {
        "contrarian":      text1,
        "first_principles": text2,
        "expansionist":    text3,
        "outsider":        text4,
        "executor":        text5,
        "rainmaker":       text6,
        "chairman":        text7,
    }
