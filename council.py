import ollama

from config import SMART_MODEL

# Bug fix: v1 returned a plain string (the Chairman's verdict only).
# This caused KeyError crashes whenever callers did debate_packet['contrarian'].
# v2 returns a full dict so all three agent verdicts are accessible.
LOCAL_MODEL = SMART_MODEL


def run_council_debate(user_idea: str) -> dict:
    """
    Runs a 3-agent strategic debate on the user's idea.

    Returns a dict with keys:
        contrarian  — risks and flaws identified
        synergist   — re-engineered strategy
        chairman    — final synthesized verdict

    Bug fix from v1: now returns a dict instead of a plain string.
    """
    print("\n==================================================")
    print("  Council Chamber Active")
    print("==================================================")

    # Phase 1: The Contrarian
    print("\n[1/3] The Contrarian...")
    prompt_contrarian = (
        f"You are 'The Contrarian', a ruthless risk analyst. "
        f"Point out the fatal flaws, vulnerabilities, and hidden dangers "
        f"in this idea. Be brief, direct, and devastating.\n\nIdea: {user_idea}"
    )
    try:
        response           = ollama.chat(model=LOCAL_MODEL,
                                         messages=[{"role": "user", "content": prompt_contrarian}])
        contrarian_verdict = response['message']['content']
        print("  done.")
    except Exception as e:
        contrarian_verdict = f"[Contrarian failed: {e}]"

    # Phase 2: The Synergist
    print("[2/3] The Synergist...")
    prompt_synergist = (
        f"You are 'The Synergist', a venture strategist. "
        f"Review this proposal: '{user_idea}' and the flaws exposed: "
        f"'{contrarian_verdict}'. Re-engineer the strategy to eliminate those flaws "
        f"and scale up the blueprint value. Keep it concise."
    )
    try:
        response          = ollama.chat(model=LOCAL_MODEL,
                                        messages=[{"role": "user", "content": prompt_synergist}])
        synergist_verdict = response['message']['content']
        print("  done.")
    except Exception as e:
        synergist_verdict = f"[Synergist failed: {e}]"

    # Phase 3: The Chairman
    print("[3/3] The Chairman...")
    prompt_chairman = (
        f"You are 'The Chairman'. Deliver the final master summary and explicit "
        f"takeaways based on the debate.\n"
        f"Original proposal: '{user_idea}'\n"
        f"Contrarian risks: '{contrarian_verdict}'\n"
        f"Synergist optimizations: '{synergist_verdict}'\n\n"
        f"Synthesize into an authoritative final review in 3 to 4 sentences."
    )
    try:
        response         = ollama.chat(model=LOCAL_MODEL,
                                       messages=[{"role": "user", "content": prompt_chairman}])
        chairman_verdict = response['message']['content']
        print("  done.")
    except Exception as e:
        chairman_verdict = f"[Chairman failed: {e}]"

    print("\n==================================================")
    print("  Debate complete.")
    print("==================================================\n")

    return {
        "contrarian": contrarian_verdict,
        "synergist":  synergist_verdict,
        "chairman":   chairman_verdict,
    }
