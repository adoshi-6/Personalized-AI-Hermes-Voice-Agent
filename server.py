from flask import Flask, request, jsonify
import hashlib
import pyautogui   # keyboard and mouse control for desktop typing
import os
import sys
import io
# Safe UTF-8 console reconfiguration — lets emoji/unicode print without crashing
# on Windows consoles. Uses reconfigure() instead of manually rewrapping
# sys.stdout/sys.stderr: rewrapping is NOT idempotent — if this file's
# top-level code ever runs twice in the same process (e.g. an old launcher
# script that starts server.py twice), a second raw TextIOWrapper() wrap
# closes the underlying buffer and crashes with
# "ValueError: I/O operation on closed file" before Flask ever starts.
# reconfigure() is safe to call any number of times.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception as _e:
    print(f"[Console encoding setup skipped: {_e}]")
import threading
import time
import ollama
import re
import json
import subprocess
import glob
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout, as_completed
from playwright.sync_api import sync_playwright
from audio_provider import speak_text, is_speaking

# ── GPU Server Connection ─────────────────────────────────────────────────────
# Point this at your Ollama server's Tailscale IP.
# Change the IP below to match your server — find it with `tailscale ip` on the server.
# Leave as localhost if running Ollama on this same machine.
OLLAMA_SERVER_URL = "http://100.88.1.86:11434"
client = ollama.Client(host=OLLAMA_SERVER_URL)
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# ============================================================
# MODEL ANCHORS
# ============================================================
# GPU SERVER ACTIVE — models running on RTX 3060 via Tailscale
#   FAST_MODEL   = "qwen3:4b"          — fast conversational replies
#   SMART_MODEL  = "deepseek-r1:14b"   — council, research, deep reasoning
#   CODING_MODEL = None                — load on demand, say "load the coder"
#
# To point at a different server: change OLLAMA_SERVER_URL below.
# ============================================================

FAST_MODEL   = "qwen3:4b"
SMART_MODEL  = "deepseek-r1:14b"
CODING_MODEL = "qwen2.5-coder:14b"   # Re-enabled — runs on GPU server

# ============================================================
# DESKTOP CONFIG — Aryan's desktop path
# ============================================================
DESKTOP_PATH = r"C:\Users\Aryan\OneDrive\Desktop"

# ============================================================
# SECURITY CONFIG
# ============================================================
SECURITY_DIR      = "ACE_SECURITY"
PIN_FILE          = os.path.join(SECURITY_DIR, "pin.json")
os.makedirs(SECURITY_DIR, exist_ok=True)

# Actions that always require a PIN before running
PROTECTED_ACTIONS = [
    "send_message", "delete_data", "change_setting",
    "first_time_access", "write_file", "store_password",
    "code_black", "safe_mode", "focus_mode", "stealth_mode",
    "factory_reset", "briefing",
]

# Current active mode — changes via code words
# Modes: "normal", "safe", "focus", "stealth"
ACE_MODE = "normal"

def _hash_pin(pin: str) -> str:
    """SHA-256 hash of the PIN — never store raw digits."""
    return hashlib.sha256(pin.strip().encode()).hexdigest()

def pin_is_set() -> bool:
    try:
        data = json.loads(open(PIN_FILE).read())
        return bool(data.get("pin_hash"))
    except Exception:
        return False

def pin_matches(entered: str) -> bool:
    try:
        data = json.loads(open(PIN_FILE).read())
        return data.get("pin_hash") == _hash_pin(entered)
    except Exception:
        return False

def save_pin(pin: str) -> None:
    with open(PIN_FILE, "w") as f:
        json.dump({"pin_hash": _hash_pin(pin)}, f)

def extract_pin_from_text(text: str) -> str | None:
    """Pull a 6-digit sequence from the user's message."""
    import re as _re
    match = _re.search(r'\b(\d{6})\b', text)
    return match.group(1) if match else None


# ============================================================
# GLOBAL STATE
# ============================================================
chat_history              = []
interaction_session_counter = 0
pending_memory_clear      = False
pending_self_modification = None   # Holds a proposed self-change awaiting approval
pending_pin_action        = None   # Holds a protected action waiting for PIN entry
pending_pin_setup         = False  # True when we're in the middle of first-time PIN setup
pending_code_word         = None   # Holds a code word action waiting for PIN confirmation

# ============================================================
# SELF-LEARNING MEMORY FILES
# These files let ACE learn from mistakes and evolve over time.
# They are plain JSON — you can open and edit them any time.
# ============================================================
MEMORY_DIR       = "ACE_MEMORY"
MISTAKES_FILE    = os.path.join(MEMORY_DIR, "mistakes.json")
CORRECTIONS_FILE = os.path.join(MEMORY_DIR, "corrections.json")
SELF_EDITS_FILE  = os.path.join(MEMORY_DIR, "self_edits.json")
LESSONS_FILE     = os.path.join(MEMORY_DIR, "lessons.json")

os.makedirs(MEMORY_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# SYSTEM PERFORMANCE MONITOR
# ─────────────────────────────────────────────────────────────

def get_full_system_report() -> dict:
    """
    Collects a comprehensive snapshot of system health.
    Returns a dict of raw metrics — the AI synthesizes advice from this.
    """
    import psutil, shutil

    report = {}

    # CPU
    report["cpu_percent"]   = psutil.cpu_percent(interval=0.5)
    report["cpu_cores"]     = psutil.cpu_count(logical=True)
    report["cpu_freq"]      = getattr(psutil.cpu_freq(), "current", "N/A")

    # RAM
    vm = psutil.virtual_memory()
    report["ram_total_gb"]  = round(vm.total / 1e9, 1)
    report["ram_used_gb"]   = round(vm.used  / 1e9, 1)
    report["ram_percent"]   = vm.percent

    # Disk
    disk = shutil.disk_usage("C:\\")
    report["disk_total_gb"] = round(disk.total / 1e9, 1)
    report["disk_used_gb"]  = round(disk.used  / 1e9, 1)
    report["disk_free_gb"]  = round(disk.free  / 1e9, 1)
    report["disk_percent"]  = round(disk.used / disk.total * 100, 1)

    # Battery
    batt = psutil.sensors_battery()
    if batt:
        report["battery_percent"] = batt.percent
        report["battery_plugged"]  = batt.power_plugged
    else:
        report["battery_percent"] = "N/A"
        report["battery_plugged"]  = "N/A"

    # Top CPU-hungry processes
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            if p.info["cpu_percent"] > 0.5:
                procs.append(p.info)
        except Exception:
            pass
    procs.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
    report["top_processes"] = procs[:8]

    # Startup programs (Windows only — reads registry)
    startup = []
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run")
        i = 0
        while True:
            try:
                name, _, _ = winreg.EnumValue(key, i)
                startup.append(name)
                i += 1
            except OSError:
                break
    except Exception:
        startup = ["Could not read startup registry"]
    report["startup_programs"] = startup

    return report


def build_system_advice(report: dict, user_query: str) -> str:
    """
    Feeds raw metrics to the model and asks for plain-English advice
    specific to Aryan's question.
    """
    metrics_text = (
        f"CPU: {report['cpu_percent']}% used ({report['cpu_cores']} cores at {report['cpu_freq']} MHz)\n"
        f"RAM: {report['ram_used_gb']}GB used of {report['ram_total_gb']}GB ({report['ram_percent']}%)\n"
        f"Disk C: {report['disk_used_gb']}GB used of {report['disk_total_gb']}GB "
        f"({report['disk_free_gb']}GB free, {report['disk_percent']}% full)\n"
        f"Battery: {report['battery_percent']}% "
        f"({'charging' if report['battery_plugged'] else 'on battery'})\n"
        f"Top CPU processes: {', '.join(p['name'] for p in report['top_processes'][:5])}\n"
        f"Startup programs: {', '.join(report['startup_programs'][:6])}"
    )

    system_prompt = (
        "You are ACE, a personal AI assistant. Always address Aryan as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses. No emojis. No filler. "
        "Address the user as 'sir' naturally. "
        "You have just run a live hardware scan. "
        "Give a direct assessment and specific actionable advice. "
        "If something looks bad, say so clearly. Under 5 sentences."
        "You have just run a live hardware scan of Aryan's PC. "
        "Give a direct assessment of system health and specific actionable advice. "
        "If something looks bad, say so clearly. "
        "If everything is fine, say that too. Keep it under 5 sentences."
    )

    return ollama_call(
        SMART_MODEL, system_prompt,
        f"Aryan asked: {user_query}\n\nLive system data:\n{metrics_text}"
    )

def _load_json(path: str, default) -> any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_mistakes() -> list:
    return _load_json(MISTAKES_FILE, [])

def save_mistake(command: str, bad_response: str, reason: str) -> None:
    mistakes = load_mistakes()
    mistakes.append({
        "timestamp":    time.strftime("%Y-%m-%d %H:%M:%S"),
        "command":      command,
        "bad_response": bad_response,
        "reason":       reason,
    })
    _save_json(MISTAKES_FILE, mistakes)
    print(f"[Self-Learn]: Mistake logged.")

def load_corrections() -> list:
    return _load_json(CORRECTIONS_FILE, [])

def save_correction(command: str, old_response: str, corrected_response: str) -> None:
    corrections = load_corrections()
    corrections.append({
        "timestamp":          time.strftime("%Y-%m-%d %H:%M:%S"),
        "command":            command,
        "old_response":       old_response,
        "corrected_response": corrected_response,
    })
    _save_json(CORRECTIONS_FILE, corrections)
    print(f"[Self-Learn]: Correction saved.")

def load_lessons() -> list:
    return _load_json(LESSONS_FILE, [])

def save_lesson(lesson: str) -> None:
    lessons = load_lessons()
    # Avoid exact duplicates
    if lesson not in lessons:
        lessons.append(lesson)
        _save_json(LESSONS_FILE, lessons)
        print(f"[Self-Learn]: Lesson stored: {lesson[:60]}...")

def load_self_edits() -> list:
    return _load_json(SELF_EDITS_FILE, [])

def save_self_edit(description: str, change_type: str, detail: str, approved: bool) -> None:
    edits = load_self_edits()
    edits.append({
        "timestamp":   time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "change_type": change_type,
        "detail":      detail,
        "approved":    approved,
    })
    _save_json(SELF_EDITS_FILE, edits)

def build_lessons_context() -> str:
    """
    Injects stored lessons and recent corrections into the system prompt
    so ACE walks into every conversation already knowing what not to repeat.
    """
    lessons     = load_lessons()
    corrections = load_corrections()
    parts = []
    if lessons:
        parts.append("Lessons learned from past mistakes:\n" +
                     "\n".join(f"  - {l}" for l in lessons[-10:]))
    if corrections:
        recent = corrections[-5:]
        lines  = []
        for c in recent:
            lines.append(f"  - When asked '{c['command']}', the wrong answer was "
                         f"'{c['old_response'][:80]}...'. Correct answer: '{c['corrected_response'][:80]}...'")
        parts.append("Recent corrections to remember:\n" + "\n".join(lines))
    if parts:
        return "\n\n[ACE SELF-LEARNING CONTEXT]\n" + "\n\n".join(parts) + "\n"
    return ""

# ============================================================
# SHARED THREAD POOL — all parallel council agents use this
# Limits total concurrent Ollama calls so the machine doesn't thrash
# ============================================================
COUNCIL_EXECUTOR = ThreadPoolExecutor(max_workers=6)

# ============================================================
# TIMEOUTS (seconds)
# ============================================================
AGENT_TIMEOUT    = 45   # Max wait per council agent before it's skipped
BROWSER_TIMEOUT  = 12   # Max wait for a page to load


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def strip_think(text: str) -> str:
    """Remove <think>...</think> blocks emitted by reasoning models."""
    return re.sub(r'<think>[\s\S]*?</think>', '', text).strip()


def stream_and_speak_sentences(messages: list, model: str, speak: bool = False) -> str:
    """
    Streams content from Ollama, extracts full sentences in real-time,
    and speaks them immediately on background threads.
    Accumulates and returns the full text response.
    """
    try:
        response_stream = client.chat(model=model, messages=messages, stream=True)
    except Exception as e:
        print(f"❌ [Streaming failure]: {e}")
        raise e

    full_response = []
    sentence_buffer = ""
    in_think_block = False

    for chunk in response_stream:
        content_chunk = chunk['message']['content']
        full_response.append(content_chunk)

        if speak:
            sentence_buffer += content_chunk

            # Simple state parser to skip over reasoning block <think>...</think>
            if "<think>" in sentence_buffer:
                in_think_block = True
                if "</think>" in sentence_buffer:
                    parts = sentence_buffer.split("</think>", 1)
                    sentence_buffer = parts[1]
                    in_think_block = False
                else:
                    continue

            if in_think_block:
                continue

            # Split on sentence boundaries: periods, question marks, exclamation marks, or double newlines
            sentences = re.split(r'(?<=[.!?])\s+|\n\n', sentence_buffer)
            if len(sentences) > 1:
                # Speak all completed sentences
                for sentence in sentences[:-1]:
                    clean_s = sentence.strip()
                    if clean_s:
                        execute_audio_playback(clean_s)
                # Keep the last incomplete fragment in the buffer
                sentence_buffer = sentences[-1]

    # Speak any remaining text left in the buffer at the end of the stream
    if speak:
        clean_remaining = sentence_buffer.strip()
        if clean_remaining:
            clean_remaining = strip_think(clean_remaining)
            if clean_remaining:
                execute_audio_playback(clean_remaining)

    return "".join(full_response)


def ollama_call_streaming(model: str, system: str, user: str, speak: bool = False) -> str:
    """
    Wrapper for streaming system prompts and user inputs dynamically.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    return stream_and_speak_sentences(messages, model, speak)


def ollama_call(model: str, system: str, user: str) -> str:
    """
    Single Ollama call with consistent error handling.
    Returns a plain string — never raises.
    """
    try:
        res = client.chat(model=model, messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ])
        return strip_think(res['message']['content'])
    except Exception as e:
        return f"[Agent error: {e}]"


def ollama_call_coding(system: str, user: str) -> str:
    """
    Coding-specific call with automatic load and unload.
    keep_alive=0 tells Ollama to evict the model from RAM/VRAM the
    moment generation finishes — it only lives in memory while actively
    generating code, never sitting idle between coding sessions.
    """
    try:
        print(f"[Coding Model]: Loading {CODING_MODEL} into memory...")
        res = client.chat(
            model=CODING_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            keep_alive=0,
        )
        reply = strip_think(res['message']['content'])
        print(f"[Coding Model]: Done. Model unloaded from memory.")
        return reply
    except Exception as e:
        print(f"[Coding Model]: Error: {e}")
        return f"[Coding agent error: {e}]"


def _run_audio(text: str, voice: str = "standard"):
    """Speak text in a background thread — never blocks Flask."""
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass
        speak_text(text, voice)
    except Exception as e:
        print(f"❌ [Audio Engine]: {e}")


def execute_audio_playback(text: str, voice: str = "standard"):
    """Fire-and-forget TTS — returns immediately."""
    import audio_provider
    audio_provider.is_currently_speaking = True
    threading.Thread(target=_run_audio, args=(text, voice), daemon=True).start()


# ─────────────────────────────────────────────────────────────
# ROUTING DETECTORS
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# SECURITY — CODE WORD DETECTION
# ─────────────────────────────────────────────────────────────

CODE_WORDS = {
    # phrase to detect          : (internal action key, description shown to user)
    "code black":    ("code_black",    "shut down everything immediately — server, audio, browser tab"),
    "safe mode":     ("safe_mode",     "switch to Safe Mode — chat only, no internet or desktop access"),
    "focus mode":    ("focus_mode",    "switch to Focus Mode — all proactive interruptions blocked"),
    "stealth mode":  ("stealth_mode",  "switch to Stealth Mode — no audio output, text only"),
    "briefing":      ("briefing",      "run a full briefing of everything since your last session"),
    "factory reset": ("factory_reset", "wipe ALL memory — lessons, mistakes, corrections, session history"),
    "stand down":    ("stand_down",    "pause all background activity but stay online"),
    "ghost mode":    ("ghost_mode",    "stop logging anything this session — no memory written"),
    "purge":         ("purge",         "wipe this session only, keep long-term memory"),
    "lockdown":      ("lockdown",      "stop accepting input from anyone until you say the unlock phrase"),
    "red alert":     ("red_alert",     "every action requires confirmation regardless of type"),
    "handoff":       ("handoff",       "save a full session summary to your desktop then shut down"),
    "debrief":       ("debrief",       "tell you everything ACE did since you last checked in"),
}

def detect_code_word(text: str) -> tuple[str, str] | None:
    """Returns (action_key, description) if a code word is found, else None."""
    lower = text.lower().strip()
    for phrase, (action, desc) in CODE_WORDS.items():
        if phrase in lower:
            return action, desc
    return None


def requires_pin(action_key: str) -> bool:
    """Returns True if this action needs a PIN before running."""
    return action_key in PROTECTED_ACTIONS


def execute_code_word(action_key: str) -> str:
    """
    Execute a confirmed (PIN-verified) code word action.
    Returns a plain string reply to send back to the user.
    """
    global ACE_MODE, chat_history

    if action_key == "code_black":
        # Schedule server shutdown after response is sent
        def _shutdown():
            time.sleep(1.5)
            os.kill(os.getpid(), 9)
        threading.Thread(target=_shutdown, daemon=True).start()
        return "Code Black confirmed. Shutting down now."

    elif action_key == "safe_mode":
        ACE_MODE = "safe"
        return "Safe Mode active. Internet and desktop access disabled. Chat only."

    elif action_key == "focus_mode":
        ACE_MODE = "focus"
        return "Focus Mode active. All proactive interruptions blocked."

    elif action_key == "stealth_mode":
        ACE_MODE = "stealth"
        return "Stealth Mode active. No audio output. Text only."

    elif action_key == "briefing":
        lessons   = load_lessons()
        mistakes  = load_mistakes()
        edits     = load_self_edits()
        session_count = len(chat_history) // 2

        # Build a rich context block for the model to summarize
        recent_topics = []
        for msg in chat_history[-12:]:
            if msg["role"] == "user":
                recent_topics.append(msg["content"][:80])

        recent_lessons = lessons[-4:] if lessons else []
        recent_edits   = [e["description"] for e in edits[-3:]] if edits else []

        briefing_context = (
            f"Session exchanges: {session_count}.\n"
            f"Recent topics: {chr(59).join(recent_topics) if recent_topics else 'None yet'}.\n"
            f"Long-term lessons stored: {len(lessons)}. "
            f"Most recent: {chr(59).join(recent_lessons) if recent_lessons else 'None'}.\n"
            f"Mistakes logged: {len(mistakes)}.\n"
            f"Self-modifications approved: {len(edits)}. "
            f"Most recent: {chr(59).join(recent_edits) if recent_edits else 'None'}.\n"
            f"Current mode: {ACE_MODE.upper()}."
        )

        summary = ollama_call(
            FAST_MODEL,
            "You are ACE giving Aryan a concise briefing. No emojis. No filler. "
            "Summarize what has happened this session, what you have learned, "
            "and what your current status is. Be direct and brief — 3 to 5 sentences max.",
            briefing_context
        )
        return summary

    elif action_key == "factory_reset":
        chat_history.clear()
        for f in [LESSONS_FILE, MISTAKES_FILE, CORRECTIONS_FILE, SELF_EDITS_FILE]:
            _save_json(f, [])
        return "Factory reset complete. All memory wiped. Starting clean."

    elif action_key == "stand_down":
        ACE_MODE = "standdown"
        return "Standing down. Background activity paused. Still here if you need me."

    elif action_key == "ghost_mode":
        ACE_MODE = "ghost"
        return "Ghost Mode active. Nothing will be logged or remembered this session."

    elif action_key == "purge":
        count = len(chat_history) // 2
        chat_history.clear()
        return f"Session purged. {count} exchanges cleared. Long-term memory intact."

    elif action_key == "lockdown":
        ACE_MODE = "lockdown"
        return "Lockdown active. I will only respond to you saying your name or unlock phrase."

    elif action_key == "red_alert":
        ACE_MODE = "red_alert"
        return "Red Alert active. Every action will require your confirmation."

    elif action_key == "handoff":
        summary = f"Session summary — {len(chat_history)//2} exchanges. Mode: {ACE_MODE}. Lessons: {len(load_lessons())}."
        path = os.path.join(DESKTOP_PATH, "ACE_HANDOFF.txt")
        try:
            with open(path, "w") as hf:
                hf.write(summary)
            def _shutdown():
                time.sleep(1.5)
                os.kill(os.getpid(), 9)
            threading.Thread(target=_shutdown, daemon=True).start()
            return f"Handoff saved to ACE_HANDOFF.txt on your desktop. Shutting down."
        except Exception as e:
            return f"Handoff file write failed: {e}"

    elif action_key == "debrief":
        edits = load_self_edits()
        recent = [e["description"] for e in edits[-3:]] if edits else []
        parts = [f"Since last session: {len(load_mistakes())} mistakes logged."]
        if recent:
            parts.append("Recent self-changes: " + "; ".join(recent))
        parts.append(f"Current mode: {ACE_MODE}.")
        return " ".join(parts)

    return f"Code word '{action_key}' recognised but not yet implemented."


def should_trigger_council(text: str) -> bool:
    text_lower = text.lower()
    triggers   = ["council", "debate", "boardroom", "assemble the council",
                  "get the council", "consult the council", "run a council",
                  "council mode", "evaluate this with the council"]
    negations  = ["don't", "dont", "do not", "never", "without", "skip",
                  "stop", "no council", "not the council"]

    if not any(kw in text_lower for kw in triggers):
        return False
    # Check if a negation appears before the trigger word
    for neg in negations:
        if neg in text_lower:
            for kw in triggers:
                if kw in text_lower and text_lower.find(neg) < text_lower.find(kw):
                    return False
    return True


def should_trigger_coding_agent(text: str) -> bool:
    keywords = ["code", "script", "program", "python", "javascript", "html",
                "css", "function", "class", "compile", "debug", "refactor",
                "write me a", "build me a", "fix this code"]
    return any(kw in text.lower() for kw in keywords)


def should_trigger_browser(text: str) -> bool:
    keywords = ["search", "browse", "look up", "google", "website", "live info",
                "current price", "news about", "what is happening", "latest",
                "find online", "check online"]
    return any(kw in text.lower() for kw in keywords)


def should_trigger_correction(text: str) -> bool:
    """Detects when Aryan is telling ACE it made a mistake."""
    keywords = [
        "that was wrong", "you were wrong", "that's incorrect", "you made a mistake",
        "that's not right", "you got that wrong", "incorrect", "bad answer",
        "wrong answer", "fix that", "that's wrong", "no that's wrong",
        "you messed up", "that was a mistake"
    ]
    return any(kw in text.lower() for kw in keywords)


def should_trigger_self_modification(text: str) -> bool:
    """Detects when Aryan wants ACE to change how it behaves or learn something."""
    keywords = [
        "change yourself", "modify yourself", "update yourself", "alter yourself",
        "learn to", "remember to always", "remember to never", "from now on",
        "going forward", "change the way you", "stop doing", "start doing",
        "always respond", "never respond", "change your personality",
        "change your tone", "teach yourself", "evolve", "adapt yourself",
        "update your behavior", "update your behaviour", "change how you"
    ]
    return any(kw in text.lower() for kw in keywords)


def build_self_modification_proposal(command: str) -> dict:
    """
    Uses the model to interpret what Aryan wants changed and
    builds a structured proposal to present for approval.
    """
    extraction = ollama_call(
        FAST_MODEL,
        "You are ACE. Aryan wants you to change something about how you behave. "
        "Extract and describe the proposed change. "
        "Respond ONLY as JSON: "
        '{"change_type": "behavior|tone|lesson|rule", '
        '"description": "plain English description of the change", '
        '"lesson": "one sentence lesson to store starting with Remember:"}',
        command
    )
    try:
        clean = re.sub(r'```[a-z]*\n?([\s\S]*?)```', r'\1', extraction).strip()
        parsed = json.loads(clean)
        return parsed
    except Exception:
        # Fallback if model doesn't return clean JSON
        return {
            "change_type": "lesson",
            "description": command,
            "lesson": f"Remember: {command}",
        }


def apply_self_modification(proposal: dict) -> None:
    """
    Applies an approved self-modification:
    - Saves it to the self_edits log (permanent audit trail)
    - Saves the lesson so it's injected into future prompts immediately
    """
    save_self_edit(
        description=proposal.get("description", ""),
        change_type=proposal.get("change_type", "lesson"),
        detail=json.dumps(proposal),
        approved=True,
    )
    lesson = proposal.get("lesson", "")
    if lesson:
        save_lesson(lesson)
    print(f"[Self-Modify]: Applied — {proposal.get('description', '')[:80]}")


def should_trigger_session_end(text: str) -> bool:
    """Detects natural end-of-session phrases — triggers Handoff automatically."""
    phrases = [
        "wrap it up", "end session", "that's all for today", "thats all for today",
        "i'm done for today", "im done for today", "shut it down for today",
        "call it a day", "we're done", "were done", "end of day",
        "close out", "wrap up for today", "finish up", "good night ACE",
        "good night", "terminate session", "end the day",
    ]
    return any(p in text.lower() for p in phrases)


def should_trigger_news_briefing(text: str) -> bool:
    """Detects requests for a current events or news briefing."""
    phrases = [
        "news briefing", "current events", "what's happening", "whats happening",
        "what happened today", "morning briefing", "daily briefing",
        "catch me up", "what's in the news", "whats in the news",
        "news update", "latest news", "headlines", "world news",
        "brief me on the news", "what did i miss",
    ]
    return any(p in text.lower() for p in phrases)


def should_trigger_system_monitor(text: str) -> bool:
    """Detects requests about system performance, speed, or hardware health."""
    keywords = [
        "system performance", "how is my computer", "how is my pc", "check my system",
        "cpu usage", "ram usage", "memory usage", "disk space", "battery",
        "system health", "what's running", "whats running", "slow down", "lagging",
        "my computer is slow", "optimize", "speed up my computer", "speed up my pc",
        "what should i close", "what's eating", "whats eating", "system stats",
        "how much ram", "how much cpu", "check performance", "system check",
        "is my computer ok", "hardware", "free up", "free up space",
        "what processes", "kill process", "startup programs"
    ]
    return any(kw in text.lower() for kw in keywords)


def should_trigger_desktop(text: str) -> bool:
    keywords = ["open", "launch", "start", "run", "file", "folder", "desktop",
                "notepad", "calculator", "chrome", "explorer", "list files",
                "show files", "read file", "save file", "write to file",
                "create file", "delete file"]
    return any(kw in text.lower() for kw in keywords)


def classify_command_route(command: str) -> str:
    """
    Classifies the user command using a hybrid model:
    1. Check for strong local keyword rules first (0ms, 100% correct).
    2. Fall back to a simplified LLM orchestrator prompt for complex phrasing.
    """
    lower = command.lower().strip()

    # --- Hybrid Rule Check ---
    browser_rules = ["search the web", "search online", "google search", "look up online", "search for", "browse the web"]
    if any(r in lower for r in browser_rules):
        return "browser"

    desktop_rules = ["open notepad", "launch notepad", "open calculator", "launch calculator", 
                     "open chrome", "launch chrome", "open explorer", "open file explorer", 
                     "list files", "show files", "desktop files"]
    if any(r in lower for r in desktop_rules):
        return "desktop"

    system_rules = ["system performance", "cpu usage", "ram usage", "disk usage", 
                    "battery percentage", "system report", "pc health", "system monitor"]
    if any(r in lower for r in system_rules):
        return "system_monitor"

    council_rules = ["ask the council", "boardroom debate", "assemble the council", "council debate"]
    if any(r in lower for r in council_rules):
        return "council"

    # Pre-classify conversational queries to bypass LLM routing overhead
    action_keywords = [
        "open", "launch", "start", "run", "close", "kill",
        "search", "google", "look up", "lookup", "browse", "find",
        "monitor", "system", "performance", "cpu", "ram", "disk", "battery", "pc", "health", "report",
        "council", "debate", "boardroom",
        "news", "headlines", "briefing",
        "modify", "teach", "learn", "rule",
        "wrong", "mistake", "correction", "incorrect",
        "wrap", "bye", "exit", "shutdown", "pin", "security",
        "code", "coding", "program", "script", "develop", "bug"
    ]
    if not any(k in lower for k in action_keywords):
        return 'conversational'

    # --- Simplified LLM orchestrator classifier ---
    system_prompt = (
        "Classify the user command into exactly one category:\n"
        "council: boardroom/council debate\n"
        "browser: search the web, check online info/news\n"
        "system_monitor: CPU, RAM, disk, PC health, performance\n"
        "desktop: open/launch/close apps, files, folders, or local controls\n"
        "coding: writing code, programming, scripts, debugging\n"
        "session_end: wrap up, end session, done, bye\n"
        "news_briefing: daily news/headlines report\n"
        "self_modification: change rules/behavior, teach new lessons\n"
        "correction: feedback that previous response was wrong/incorrect\n"
        "conversational: standard chat, math, questions, general talk\n"
        "\n"
        "Answer with ONLY the category name. Example: conversational"
    )
    try:
        # Determine assistant name dynamically in github version, or use ACE directly
        try:
            name_label = ASSISTANT_NAME
        except NameError:
            name_label = "ACE"
            
        reply = ollama_call(FAST_MODEL, system_prompt, f"User command: {command}")
        route = reply.strip().lower().replace("'", "").replace('"', "")
        
        # Keyword-to-route synonym mapping to make classification robust
        route_mapping = {
            'browser': ['browser', 'web', 'internet', 'search', 'google', 'duckduckgo', 'lookup', 'online'],
            'desktop': ['desktop', 'application', 'app', 'launch', 'open', 'close', 'run', 'local', 'file', 'folder', 'cmd', 'command'],
            'system_monitor': ['system_monitor', 'system', 'monitor', 'cpu', 'ram', 'performance', 'health', 'battery', 'metrics'],
            'coding': ['coding', 'code', 'script', 'compile', 'debug', 'programming', 'develop'],
            'council': ['council', 'debate', 'boardroom', 'consult'],
            'session_end': ['session_end', 'end', 'wrap', 'close', 'exit', 'bye', 'goodnight'],
            'news_briefing': ['news_briefing', 'briefing', 'headlines'],
            'self_modification': ['self_modification', 'modify', 'behavior', 'learn', 'rule'],
            'correction': ['correction', 'correct', 'wrong', 'mistake', 'incorrect']
        }
        for r, keywords in route_mapping.items():
            if any(k in route for k in keywords):
                return r
        return 'conversational'
    except Exception as e:
        print(f"?? [Routing classification error]: {e}")
        return 'conversational'
# ─────────────────────────────────────────────────────────────
# PARALLEL COUNCIL — all 6 agents fire simultaneously
# Chairman runs after they all finish (needs their output)
# ─────────────────────────────────────────────────────────────

import json
import os

_council_config_path = os.path.join(os.path.dirname(__file__), "council_config.json")
with open(_council_config_path, "r", encoding="utf-8") as f:
    _council_data = json.load(f)

# The first 6 are workers, the last is the chairman
DEBATE_SEATS = ["contrarian", "first_principles", "expansionist", "outsider", "executor", "rainmaker"]
COUNCIL_AGENTS = {k: v for k, v in _council_data.items() if k in DEBATE_SEATS}
CHAIRMAN_SYSTEM = _council_data.get("chairman", {}).get("system", "")


def _run_agent(seat_name: str, idea: str) -> tuple[str, str]:
    """Run one council agent. Returns (seat_name, verdict)."""
    cfg    = COUNCIL_AGENTS[seat_name]
    system = cfg["system"]
    prompt = cfg["prompt"].format(idea=idea)
    result = ollama_call(SMART_MODEL, system, prompt)
    return seat_name, result


def run_parallel_council(idea: str) -> dict:
    """
    Fire all 6 agents simultaneously using the shared thread pool.
    Each agent has AGENT_TIMEOUT seconds; slow ones get a fallback message.
    Chairman runs after all 6 complete (needs their output to synthesize).
    Total wall time ≈ slowest single agent + chairman, not sum of all 7.
    """
    print(f"\n👥 [Hermes Council]: Firing 6 agents in parallel via {SMART_MODEL}...")
    results = {}

    # Submit all 6 agents at once
    futures = {
        COUNCIL_EXECUTOR.submit(_run_agent, seat, idea): seat
        for seat in COUNCIL_AGENTS
    }

    for future in as_completed(futures, timeout=AGENT_TIMEOUT + 5):
        seat = futures[future]
        try:
            _, verdict = future.result(timeout=AGENT_TIMEOUT)
            results[seat] = verdict
            print(f"  ✅ {seat} complete.")
        except FuturesTimeout:
            results[seat] = "Agent timed out — skipped."
            print(f"  ⏱️  {seat} timed out.")
        except Exception as e:
            results[seat] = f"Agent error: {e}"
            print(f"  ❌ {seat} failed: {e}")

    # Chairman runs last — needs all 5 briefs
    print("  -> Chairman synthesizing...")
    chairman_input = (
        f"Objective: {idea}\n\n"
        f"Contrarian: {results.get('contrarian', 'N/A')}\n\n"
        f"First Principles: {results.get('first_principles', 'N/A')}\n\n"
        f"Expansionist: {results.get('expansionist', 'N/A')}\n\n"
        f"Outsider: {results.get('outsider', 'N/A')}\n\n"
        f"Executor: {results.get('executor', 'N/A')}\n\n"
        f"Rainmaker: {results.get('rainmaker', 'N/A')}"
    )
    results["chairman"] = ollama_call(SMART_MODEL, CHAIRMAN_SYSTEM, chairman_input)
    print("  ✅ Chairman complete.\n")

    return results


def run_execution_loop(task: str) -> dict:
    """
    Step 2: Core Execution Loop (Conductor/Worker/Verifier)
    Executes a task through planning, execution, and verification phases.
    Iterates up to 3 times to get a verified result.
    """
    print(f"\n⚡ [Execution Loop]: Starting loop for task: '{task}'")
    
    cond_cfg = _council_data.get("conductor", {})
    ver_cfg = _council_data.get("verifier", {})
    
    # 1. CONDUCTOR Plan
    cond_sys = cond_cfg.get("system", "")
    cond_prompt = cond_cfg.get("prompt", "").format(task=task)
    
    plan_json = {}
    try:
        raw_plan = ollama_call(SMART_MODEL, cond_sys, cond_prompt)
        # Parse JSON from model output
        clean_plan = re.sub(r'```[a-z]*\n?([\s\S]*?)```', r'\1', raw_plan).strip()
        # Find outer JSON block if there is extra conversational text
        json_match = re.search(r'\{[\s\S]*\}', clean_plan)
        if json_match:
            clean_plan = json_match.group(0)
        plan_json = json.loads(clean_plan)
    except Exception as e:
        print(f"❌ [Conductor Planning Error]: {e}. Raw response: {raw_plan if 'raw_plan' in locals() else 'N/A'}")
        return {"status": "error", "error": f"Conductor planning failed: {e}", "logs": []}

    worker = plan_json.get("worker", "conversational")
    spec = plan_json.get("spec", "")
    done_when = plan_json.get("done_when", [])
    
    print(f"📋 [Conductor Plan]: Specialist: {worker} | Spec: '{spec}' | Done When: {done_when}")
    
    loop_logs = []
    current_feedback = ""
    success = False
    final_output = ""
    
    # Iterate up to 3 times
    for attempt in range(1, 4):
        print(f"🔄 [Execution Attempt {attempt}/3]: Running Specialist Worker '{worker}'")
        
        # 2. WORKER executes
        worker_output = ""
        try:
            if worker == "browser":
                # Prepend previous feedback if we are retrying
                full_spec = spec
                if current_feedback:
                    full_spec += f" (Note: previous search failed verification: {current_feedback})"
                worker_output = execute_browser_harness(full_spec)
            elif worker == "desktop":
                full_spec = spec
                if current_feedback:
                    full_spec += f"\nNote: Previous attempt failed verification. Feedback: {current_feedback}"
                worker_output = handle_desktop_command(full_spec)
            elif worker == "coding":
                coding_system = (
                    "You are ACE's software engineering agent. No emojis. No filler. "
                    "Address the user as 'sir' naturally. "
                    "Provide clean, working code. "
                )
                if current_feedback:
                    coding_system += f"\nPrevious attempt failed verification. Feedback: {current_feedback}"
                worker_output = ollama_call_coding(coding_system, spec)
            else:
                # General text specialist worker (mathematician, sales, support)
                worker_prompt = f"Perform this task: {spec}"
                if current_feedback:
                    worker_prompt += f"\nNote: Previous attempt failed. Verifier feedback: {current_feedback}. Adjust your answer accordingly."
                
                worker_sys = "You are a specialist worker on ACE's council. Be precise and direct."
                # Check if there is a custom agent prompt matching the worker name
                if worker in _council_data:
                    worker_sys = _council_data[worker].get("system", worker_sys)
                    
                worker_output = ollama_call(SMART_MODEL, worker_sys, worker_prompt)
        except Exception as e:
            worker_output = f"Worker execution error: {e}"
            print(f"❌ [Worker Error]: {e}")
            
        print(f"📥 [Worker Output]: {worker_output[:120]}...")
        
        # 3. VERIFIER checks output
        ver_sys = ver_cfg.get("system", "")
        ver_prompt = ver_cfg.get("prompt", "").format(
            spec=spec,
            done_when=json.dumps(done_when),
            output=worker_output
        )
        
        verdict = ""
        try:
            verdict = ollama_call(SMART_MODEL, ver_sys, ver_prompt).strip()
        except Exception as e:
            verdict = f"FAIL: Verifier error: {e}"
            
        print(f"🧐 [Verifier Verdict]: {verdict}")
        
        loop_logs.append({
            "attempt": attempt,
            "worker": worker,
            "spec": spec,
            "output": worker_output,
            "verdict": verdict
        })
        
        if verdict.startswith("PASS"):
            success = True
            final_output = worker_output
            break
        else:
            current_feedback = verdict.replace("FAIL:", "").strip()
            final_output = worker_output
            
    return {
        "status": "success" if success else "failed",
        "worker": worker,
        "spec": spec,
        "done_when": done_when,
        "output": final_output,
        "logs": loop_logs
    }


# ─────────────────────────────────────────────────────────────
# BROWSER HARNESS — internet access
# ─────────────────────────────────────────────────────────────

def execute_browser_harness(user_query: str) -> str:
    """
    Uses Crawl4AI to scrape a Bing search for live web context in clean Markdown.
    """
    print(f"🌐 [Crawl4AI Browser]: Query: '{user_query}'")

    # Ask the fast model to extract clean search terms
    try:
        raw_terms = ollama_call(
            FAST_MODEL,
            "Extract only the ideal web search keywords from the user request. "
            "Output nothing but the raw keyword string — no quotes, no explanation.",
            user_query
        )
        target_search = raw_terms.strip().replace('"', '').replace("'", "")
    except Exception:
        target_search = user_query

    target_url = (
        target_search if target_search.startswith("http")
        else f"https://www.bing.com/search?q={target_search.replace(' ', '+')}"
    )

    print(f"🛰️  Crawling -> {target_url}")
    
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler
        
        async def _crawl(url):
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return result.markdown

        # Safely run the async crawl in Flask's sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        markdown_data = loop.run_until_complete(_crawl(target_url))
        
        # Take the first 3000 chars to avoid model context overflow
        scraped = markdown_data[:3000]
        print("✅ [Crawl4AI]: Markdown context extracted successfully.")
        return scraped
        
    except Exception as e:
        print(f"❌ [Crawl4AI Failure]: {e}")
        return f"Browser crawl unavailable: {e}"


# ─────────────────────────────────────────────────────────────
# DESKTOP ACCESS — files and apps on Aryan's machine
# ─────────────────────────────────────────────────────────────

def focus_window(title_substring: str) -> bool:
    import ctypes
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_pointer)
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
    ShowWindow = ctypes.windll.user32.ShowWindow

    found_hwnd = []

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value.lower()
                if title_substring.lower() in title:
                    found_hwnd.append(hwnd)
                    return False # stop enumeration
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)
    if found_hwnd:
        hwnd = found_hwnd[0]
        ShowWindow(hwnd, 9) # Restore window if minimized
        SetForegroundWindow(hwnd)
        return True
    return False


def handle_desktop_command(command: str) -> str:
    """
    Gives access to Aryan's desktop:
    - Open applications (notepad, calculator, chrome, explorer)
    - List files on the desktop
    - Read a named file from the desktop
    - Write / append text to a named file on the desktop
    - Open a specific file with its default app
    """
    lower = command.lower()

    # --- Advanced window management ---
    if any(k in lower for k in ["focus", "bring to front", "maximize", "show window", "bring"]):
        words = lower.split()
        ignore = ["bring", "to", "the", "front", "of", "screen", "my", "focus", "show", "window", "app", "application", "please", "now"]
        name_words = [w for w in words if w not in ignore]
        if name_words:
            app_name = name_words[0]
            if focus_window(app_name):
                return f"Brought {app_name} to the front."
            else:
                return f"Could not find any running window matching '{app_name}'."


    # --- App launching ---
    app_map = {
        "notepad":     "notepad",
        "calculator":  "calc",
        "chrome":      "chrome",
        "explorer":    "explorer",
        "file explorer": "explorer",
    }
    for keyword, exe in app_map.items():
        if keyword in lower:
            try:
                os.startfile(exe) if exe not in ("calc", "notepad") else subprocess.Popen(exe)
                return f"Launched {keyword}."
            except Exception as e:
                return f"Couldn't launch {keyword}: {e}"

    # General app launching fallback using Windows Shell start command!
    if any(k in lower for k in ["open", "launch", "start"]):
        words = lower.split()
        ignore = ["open", "launch", "start", "the", "app", "application", "please", "app:"]
        name_words = [w for w in words if w not in ignore]
        if name_words:
            app_name = name_words[0]
            try:
                subprocess.Popen(f"start {app_name}", shell=True)
                return f"Launched {app_name}."
            except Exception as e:
                return f"Could not launch {app_name}: {e}"

    # --- List desktop files ---
    if any(kw in lower for kw in ["list files", "show files", "what's on my desktop", "files on desktop"]):
        try:
            files = os.listdir(DESKTOP_PATH)
            if not files:
                return "Your desktop is empty."
            return "Desktop contents:\n" + "\n".join(f"  • {f}" for f in sorted(files))
        except Exception as e:
            return f"Couldn't read desktop: {e}"

    # --- Read a file ---
    if "read" in lower or "open file" in lower:
        # Ask the model to extract the filename from the command
        filename = ollama_call(
            FAST_MODEL,
            "Extract only the filename (including extension) from the user request. "
            "Output nothing but the filename. If you can't find one, output: NONE",
            command
        ).strip()
        if filename and filename != "NONE":
            target = os.path.join(DESKTOP_PATH, filename)
            if os.path.exists(target):
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        content = f.read()
                    return f"Contents of {filename}:\n\n{content}"
                except Exception as e:
                    return f"Couldn't read {filename}: {e}"
            else:
                return f"File '{filename}' not found on your desktop."
        return "Please specify which file to read."

    # --- Write / append to a file --- (PIN required)
    if any(kw in lower for kw in ["write", "save", "append", "create file", "add to"]):
        if not pending_pin_action:
            pending_pin_action = {"command": command, "action": "write_file"}
            return "Writing to a file requires your PIN. Enter your 6-digit PIN to continue."
        # Let the model extract filename and content
        extraction = ollama_call(
            FAST_MODEL,
            'Extract the filename and the content to write from the user request. '
            'Respond ONLY as JSON like: {"filename": "notes.txt", "content": "text here", "mode": "write"} '
            'Mode should be "append" if user says append/add, otherwise "write". '
            'If you cannot find them, respond: {"filename": "NONE", "content": "", "mode": "write"}',
            command
        )
        try:
            clean = re.sub(r'```[a-z]*\n?([\s\S]*?)```', r'\1', extraction).strip()
            parsed = json.loads(clean)
            filename = parsed.get("filename", "NONE")
            content  = parsed.get("content", "")
            mode     = parsed.get("mode", "write")
            if filename and filename != "NONE":
                target = os.path.join(DESKTOP_PATH, filename)
                write_mode = "a" if mode == "append" else "w"
                with open(target, write_mode, encoding="utf-8") as f:
                    if mode == "append":
                        f.write("\n" + content)
                    else:
                        f.write(content)
                action = "appended to" if mode == "append" else "written to"
                return f"Done — {action} {filename} on your desktop."
        except Exception as e:
            return f"File write failed: {e}"
        return "Please specify the filename and what to write."

    # --- Type text into whichever app is in focus ---
    if any(kw in lower for kw in ["type", "write in", "type in", "enter text", "input"]):
        text_to_type = ollama_call(
            FAST_MODEL,
            "Extract only the text that should be typed. Output nothing but the raw text to type. "
            "If you cannot find text to type, output: NONE",
            command
        ).strip()
        if text_to_type and text_to_type != "NONE":
            try:
                import time as _time
                _time.sleep(0.5)   # brief pause so the target app can get focus
                pyautogui.typewrite(text_to_type, interval=0.04)
                return f"Typed into the active window: {text_to_type}"
            except Exception as e:
                return f"Typing failed: {e}"
        return "Could not extract what to type. Please be more specific."

    return "Desktop command not recognised. Try: 'open notepad', 'list files', 'read notes.txt', 'write to todo.txt: buy milk', or 'type hello world'."


# ─────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────


@app.route('/api/pin_status', methods=['GET'])
def pin_status():
    """Frontend polls this on load to know if PIN setup is needed."""
    return jsonify({
        "pin_set": pin_is_set(),
        "ACE_MODE": ACE_MODE,
    })


@app.route('/api/stop_audio', methods=['POST'])
def stop_audio():
    """Kill audio immediately — called when browser tab loses focus."""
    try:
        import ctypes as _ct
        _ct.windll.winmm.mciSendStringW('stop ACE_audio', None, 0, 0)
        _ct.windll.winmm.mciSendStringW('close ACE_audio', None, 0, 0)
    except Exception:
        pass
    return jsonify({"status": "stopped"})


@app.route('/api/is_speaking', methods=['GET'])
def check_is_speaking():
    """
    Frontend polls this after every response to know when ACE has
    finished talking so it can safely re-arm the microphone. Without this
    route the frontend's restart-listening loop has nothing valid to poll
    and the mic never comes back on after the first reply.
    """
    return jsonify({"speaking": is_speaking()})


@app.route('/api/stop_audio', methods=['POST'])
def stop_audio_endpoint():
    """Immediately stops all TTS audio output."""
    import audio_provider
    audio_provider.stop_all_audio()
    return jsonify({"status": "stopped"})


@app.route('/api/health', methods=['GET'])
def health_check():
    """Live health data for the System Health panel in the frontend."""
    return jsonify({
        "server":       "Running on localhost:5000",
        "ollama":       "Port 11434",
        "fast_model":   FAST_MODEL,
        "smart_model":  SMART_MODEL,
        "coding_model": CODING_MODEL or "Offline — GPU server pending",
    })


@app.route('/')
def serve_dashboard_console():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Dashboard load failure: {e}"


@app.route('/three.min.js')
def serve_local_three_js():
    try:
        with open('three.min.js', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript'}
    except Exception as e:
        return f"Graphics asset failure: {e}", 404


@app.route('/api/speak', methods=['POST'])
def handle_isolated_playback():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    voice = data.get('voice', 'standard').strip()
    if text:
        execute_audio_playback(text, voice)
    return jsonify({"status": "vocalization_complete"})


@app.route('/api/command', methods=['POST'])
def orchestrate_command_routing():
    global chat_history, pending_memory_clear, interaction_session_counter, pending_self_modification
    global pending_pin_action, pending_pin_setup, pending_code_word, ACE_MODE
    start_time = time.time()

    data    = request.get_json() or {}
    command = data.get('command', '').strip()
    source  = data.get('source', 'text')

    if not command:
        return jsonify({"response": "Empty command.", "execution_time": 0.0})

    interaction_session_counter += 1
    print(f"\n📥 [{source.upper()}] #{interaction_session_counter}: \"{command}\"")
    lower_cmd      = command.lower()
    context_string = f"{len(chat_history)}/20 SLOTS"

    def respond(reply, rtype="standard", model=FAST_MODEL, speak=False):
        """Helper to build a consistent response dict and optionally speak."""
        if speak and source == 'voice' and ACE_MODE != "stealth":
            execute_audio_playback(reply if isinstance(reply, str) else "Response ready.")
        return jsonify({
            "response":          reply,
            "type":              rtype,
            "model":             model,
            "ACE_MODE":          ACE_MODE,
            "interaction_count": interaction_session_counter,
            "context_loaded":    context_string,
            "execution_time":    round(time.time() - start_time, 2),
        })

    # ══════════════════════════════════════════════════════════════════════
    # SECURITY GATES — checked before anything else
    # ══════════════════════════════════════════════════════════════════════

    # ── First-run PIN setup ──────────────────────────────────────────────
    if not pin_is_set() and not pending_pin_setup:
        pending_pin_setup = True
        reply = (
            "Before we go any further, I need you to set a 6-digit security PIN. "
            "This PIN will be required before any sensitive action. "
            "Type your 6-digit PIN now — I will hash and store it, never the raw digits."
        )
        return respond(reply, speak=True)

    if pending_pin_setup:
        entered = extract_pin_from_text(command)
        if entered and len(entered) == 6 and entered.isdigit():
            save_pin(entered)
            pending_pin_setup = False
            reply = "PIN set. I have hashed and stored it — the raw digits are gone. You are ready."
        else:
            reply = "That does not look like a 6-digit number. Please enter your 6-digit PIN."
        return respond(reply, speak=True)

    # ── Stealth mode — no audio output ──────────────────────────────────
    if ACE_MODE == "stealth":
        source = "text"   # Force text-only — no TTS fired regardless of source

    # ── Lockdown mode — ignore everyone ─────────────────────────────────
    if ACE_MODE == "lockdown":
        unlock_phrases = ["aryan", "unlock", "i am aryan", "this is aryan"]
        if not any(p in lower_cmd for p in unlock_phrases):
            return respond("Lockdown active. Not responding.", speak=False)
        else:
            ACE_MODE = "normal"
            return respond("Lockdown lifted. Welcome back, Aryan.", speak=True)

    # ── Code word detection ──────────────────────────────────────────────
    code_match = detect_code_word(command)
    if code_match and not pending_code_word:
        action_key, description = code_match
        pending_code_word = action_key
        reply = (
            f"Code word detected: {action_key.replace('_', ' ').upper()}. "
            f"This will: {description}. "
            f"Enter your 6-digit PIN to confirm."
        )
        return respond(reply, speak=True)

    # ── Code word PIN confirmation ───────────────────────────────────────
    if pending_code_word:
        entered = extract_pin_from_text(command)
        if entered and pin_matches(entered):
            action = pending_code_word
            pending_code_word = None
            result = execute_code_word(action)
            return respond(result, speak=(ACE_MODE != "stealth"))
        else:
            pending_code_word = None
            reply = "Incorrect PIN. Code word action cancelled."
            return respond(reply, speak=True)

    # ── Pending PIN gate — waiting for PIN before a protected action ─────
    if pending_pin_action:
        entered = extract_pin_from_text(command)
        if entered and pin_matches(entered):
            action_data = pending_pin_action
            pending_pin_action = None
            # Re-route to the correct handler with the original command
            command  = action_data["command"]
            lower_cmd = command.lower()
            # Fall through to normal routing below with PIN cleared
        else:
            pending_pin_action = None
            reply = "Incorrect PIN. Action cancelled."
            return respond(reply, speak=True)

    # ── Memory purge confirmation gate ──────────────────────────────────────
    if pending_memory_clear:
        if any(w in lower_cmd for w in ["yes", "confirm", "do it", "sure", "go ahead"]):
            purge_type = pending_memory_clear  # "session", "lessons", or "all"
            deleted = []

            if purge_type in ("session", "all"):
                count = len(chat_history) // 2
                chat_history.clear()
                deleted.append(f"{count} conversation messages this session")

            if purge_type in ("lessons", "all"):
                lessons   = load_lessons()
                mistakes  = load_mistakes()
                corr      = load_corrections()
                edits     = load_self_edits()
                _save_json(LESSONS_FILE,     [])
                _save_json(MISTAKES_FILE,    [])
                _save_json(CORRECTIONS_FILE, [])
                _save_json(SELF_EDITS_FILE,  [])
                deleted.append(
                    f"{len(lessons)} lessons, {len(mistakes)} mistakes, "
                    f"{len(corr)} corrections, {len(edits)} self-edits"
                )

            pending_memory_clear = False
            summary = " and ".join(deleted) if deleted else "nothing"
            reply = f"Done. Erased: {summary}."

        elif any(w in lower_cmd for w in ["no", "cancel", "abort", "stop", "keep"]):
            pending_memory_clear = False
            reply = "Cancelled. Nothing was erased."
        else:
            pending_memory_clear = False
            reply = "Unclear — erased nothing to be safe."
        return respond(reply, speak=True)

    # ── Memory purge request ────────────────────────────────────────────────
    purge_actions  = ["clear", "wipe", "reset", "delete", "purge", "forget", "erase"]
    memory_targets = ["memory", "history", "logs", "context", "cache",
                      "lessons", "mistakes", "corrections", "everything"]

    if any(a in lower_cmd for a in purge_actions) and any(t in lower_cmd for t in memory_targets):
        # Work out scope
        wants_lessons = any(w in lower_cmd for w in
                            ["lessons", "mistakes", "corrections", "long term",
                             "long-term", "everything", "all memory", "all of it"])
        wants_session = any(w in lower_cmd for w in
                            ["history", "context", "session", "conversation",
                             "chat", "cache", "this session"])

        if wants_lessons and wants_session:
            scope = "all"
        elif wants_lessons:
            scope = "lessons"
        else:
            scope = "session"   # default — safer

        # Build a plain summary of what will be deleted
        session_count = len(chat_history) // 2
        lesson_count  = len(load_lessons())
        mistake_count = len(load_mistakes())

        if scope == "all":
            preview = (
                f"This will erase: {session_count} messages from this session, "
                f"plus {lesson_count} lessons and {mistake_count} logged mistakes "
                f"from long-term memory. This cannot be undone. Confirm?"
            )
        elif scope == "lessons":
            preview = (
                f"This will erase {lesson_count} lessons and {mistake_count} logged mistakes "
                f"from long-term memory. Your conversation history stays. Confirm?"
            )
        else:
            preview = (
                f"This will erase {session_count} messages from this session only. "
                f"Long-term lessons and memory stay intact. Confirm?"
            )

        pending_memory_clear = scope
        return respond(preview, speak=True)

    # ── Mode deactivation — turn off any active mode ────────────────────────
    mode_off_phrases = [
        "disable safe mode", "turn off safe mode", "exit safe mode", "leave safe mode",
        "disable focus mode", "turn off focus mode", "exit focus mode",
        "disable stealth mode", "turn off stealth mode", "exit stealth mode",
        "disable ghost mode", "turn off ghost mode", "exit ghost mode",
        "disable red alert", "turn off red alert", "exit red alert",
        "disable stand down", "resume normal", "normal mode", "back to normal",
        "disable lockdown", "exit lockdown",
        "cancel mode", "deactivate mode", "clear mode", "reset mode",
    ]
    if any(phrase in lower_cmd for phrase in mode_off_phrases) and ACE_MODE != "normal":
        old_mode = ACE_MODE
        ACE_MODE = "normal"
        reply = f"{old_mode.replace('_', ' ').title()} deactivated. Back to normal."
        return respond(reply, speak=True)

    # ── Voice control ───────────────────────────────────────────────────────
    if any(x in lower_cmd for x in ["turn microphone off", "microphone off", "voice mode off", "deactivate voice", "turn off voice mode", "turn off the microphone"]):
        reply = "Entering standby. Say 'Hey ACE' or 'activate voice mode' when you need me."
        return respond(reply, rtype="shutdown", speak=True)

    if any(x in lower_cmd for x in ["activate voice mode", "turn on microphone", "voice mode on"]):
        reply = "Voice channels open, Aryan. Listening."
        execute_audio_playback(reply)
        return respond(reply, rtype="wakeup")

    # ── Intent Classification Route ───────────────────────────────────────
    route = classify_command_route(command)
    print(f"🎯 [Hermes Orchestrator] Dynamic LLM Route: {route}")

    # ── Safe mode guard — block internet and desktop ─────────────────────
    if ACE_MODE == "safe":
        if route in ("browser", "desktop"):
            return respond(
                "Safe Mode is active — internet and desktop access are disabled. "
                "Say 'disable safe mode' and enter your PIN to restore full access.",
                speak=True
            )

    # ── Red alert guard — every action needs confirmation ─────────────────
    if ACE_MODE == "red_alert" and not pending_pin_action:
        pending_pin_action = {"command": command, "action": "red_alert_confirm"}
        return respond(
            "Red Alert is active. Enter your PIN to confirm this action.",
            speak=True
        )

    # ══════════════════════════════════════════════════════════════════════
    # CASE A — PARALLEL COUNCIL
    # All 6 agents fire at the same time. Total wait ≈ slowest single agent.
    # ══════════════════════════════════════════════════════════════════════
    if route == "council":
        print(f"👥 [Hermes]: Parallel council assembling...")
        try:
            debate_packet = run_parallel_council(command)
            return jsonify({
                "response":          debate_packet,
                "type":              "council",
                "model":             "hermes-parallel-7",
                "interaction_count": interaction_session_counter,
                "context_loaded":    context_string,
                "execution_time":    round(time.time() - start_time, 2),
            })
        except Exception as e:
            print(f"❌ [Council crash]: {e}")
            return respond(f"Council assembly failed: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CASE B — INTERNET / BROWSER HARNESS
    # ══════════════════════════════════════════════════════════════════════
    elif route == "browser":
        print(f"🌐 [Hermes]: Browser harness active...")
        # Run through execution loop to verify web search
        loop_res = run_execution_loop(command)
        web_context = loop_res.get("output", "")
        synthesis_system = (
            "You are ACE, a personal AI assistant. Always address Aryan as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses. with live web access. "
            "Never use emojis. Never start with filler phrases like Certainly or Great question. "
            "Summarize the most relevant facts from the web data to answer Aryan's question directly. "
            "2 to 4 sentences max. Skip navigation text and ads. "
            "If the data does not contain an answer, say so plainly."
        )
        try:
            reply = ollama_call_streaming(
                SMART_MODEL, synthesis_system,
                f"Aryan asked: {command}\n\nLive web data:\n{web_context}",
                speak=(source == 'voice' and ACE_MODE != "stealth")
            )
            return jsonify({
                "response":          reply,
                "type":              "browser",
                "model":             "hermes-browser",
                "ACE_MODE":      ACE_MODE,
                "interaction_count": interaction_session_counter,
                "context_loaded":    context_string,
                "execution_time":    round(time.time() - start_time, 2),
                "logs":              loop_res.get("logs", [])
            })
        except Exception as e:
            return respond(f"Browser synthesis failed: {e}", rtype="browser")

    # ══════════════════════════════════════════════════════════════════════
    # CASE C — SYSTEM PERFORMANCE MONITOR
    # ══════════════════════════════════════════════════════════════════════
    elif route == "system_monitor":
        print(f"[Hermes]: System monitor active...")
        try:
            report = get_full_system_report()
            advice = build_system_advice(report, command)
            # Also return raw metrics so the frontend can display them cleanly
            return jsonify({
                "response":          advice,
                "type":              "system_monitor",
                "model":             "system-agent",
                "metrics":           {
                    "cpu":     f"{report['cpu_percent']}%",
                    "ram":     f"{report['ram_used_gb']}GB / {report['ram_total_gb']}GB ({report['ram_percent']}%)",
                    "disk":    f"{report['disk_free_gb']}GB free of {report['disk_total_gb']}GB",
                    "battery": f"{report['battery_percent']}% ({'charging' if report['battery_plugged'] else 'on battery'})",
                    "top_procs": [p['name'] for p in report['top_processes'][:5]],
                    "startup": report['startup_programs'][:6],
                },
                "interaction_count": interaction_session_counter,
                "context_loaded":    context_string,
                "execution_time":    round(time.time() - start_time, 2),
            })
        except Exception as e:
            return respond(f"System scan failed: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # CASE D — DESKTOP ACCESS
    # ══════════════════════════════════════════════════════════════════════
    elif route == "desktop":
        print(f"🖥️  [Hermes]: Desktop agent active...")
        loop_res = run_execution_loop(command)
        result = loop_res.get("output", "")
        if source == 'voice' and ACE_MODE != "stealth":
            execute_audio_playback(result)
        return jsonify({
            "response":          result,
            "type":              "desktop",
            "model":             "desktop-agent",
            "ACE_MODE":      ACE_MODE,
            "interaction_count": interaction_session_counter,
            "context_loaded":    context_string,
            "execution_time":    round(time.time() - start_time, 2),
            "logs":              loop_res.get("logs", [])
        })

    # ══════════════════════════════════════════════════════════════════════
    # CASE D2 — CODING AGENT (disabled — no model loaded)
    # Re-enable when GPU server arrives by setting CODING_MODEL above.
    # ══════════════════════════════════════════════════════════════════════
    elif route == "coding":
        print(f"[Hermes]: Coding agent requested -> {CODING_MODEL}")
        loop_res = run_execution_loop(command)
        result = loop_res.get("output", "")
        if source == 'voice' and ACE_MODE != "stealth":
            execute_audio_playback("Code compiled. Dropping it into your viewport now.")
        return jsonify({
            "response":          result,
            "type":              "coding",
            "model":             CODING_MODEL,
            "ACE_MODE":      ACE_MODE,
            "interaction_count": interaction_session_counter,
            "context_loaded":    context_string,
            "execution_time":    round(time.time() - start_time, 2),
            "logs":              loop_res.get("logs", [])
        })

    # ══════════════════════════════════════════════════════════════════════
    # CASE E — SESSION END ("wrap it up", "end session", etc.)
    # Triggers Handoff automatically — saves summary and shuts down.
    # ══════════════════════════════════════════════════════════════════════
    elif route == "session_end":
        result = execute_code_word("handoff")
        return respond(result, speak=True)

    # ══════════════════════════════════════════════════════════════════════
    # CASE F — CURRENT EVENTS / NEWS BRIEFING
    # Searches the web for top headlines and summarises them.
    # ══════════════════════════════════════════════════════════════════════
    elif route == "news_briefing":
        print(f"[Hermes]: News briefing requested...")
        queries = [
            "top world news headlines today",
            "top US news headlines today",
            "technology news today",
        ]
        all_context = []
        for q in queries:
            ctx = execute_browser_harness(q)
            if ctx and "unavailable" not in ctx.lower():
                all_context.append(ctx[:600])

        combined = "\n\n".join(all_context) if all_context else "No news data retrieved."

        news_system = (
            "You are ACE, a personal AI assistant. Always address Aryan as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses. delivering a morning news briefing. "
            "No emojis. No filler. Address the user as 'sir'. "
            "Summarise the most important headlines from the data provided. "
            "Group by category if possible: world, US, tech. "
            "Be concise — this is a spoken briefing, not an article. "
            "Under 8 sentences total."
        )
        reply = ollama_call_streaming(
            SMART_MODEL, news_system,
            f"Today's news data:\n{combined}",
            speak=(source == 'voice' and ACE_MODE != "stealth")
        )
        return respond(reply, rtype="browser", model="news-briefing", speak=False)

    # ══════════════════════════════════════════════════════════════════════
    # CASE G — SELF-MODIFICATION REQUEST
    # Aryan asks ACE to change how it behaves, learn something, or fix itself.
    # ACE proposes the change, then waits for explicit approval before applying.
    # ══════════════════════════════════════════════════════════════════════
    elif route == "self_modification":
        print(f"[Self-Modify]: Self-modification request detected.")
        proposal = build_self_modification_proposal(command)
        global pending_self_modification
        pending_self_modification = proposal
        reply = (
            "Understood. Here's what I'm proposing to change:\n\n"
            f"Type: {proposal['change_type']}\n"
            f"What: {proposal['description']}\n\n"
            "Do you approve this change? Say 'yes apply it' to confirm, or 'no cancel' to reject."
        )
        return respond(reply, speak=True)

    # ══════════════════════════════════════════════════════════════════════
    # CASE H — SELF-MODIFICATION APPROVAL GATE
    # ══════════════════════════════════════════════════════════════════════
    elif pending_self_modification and any(w in lower_cmd for w in ["yes apply", "approve", "confirm it", "go ahead", "apply it"]):
        proposal = pending_self_modification
        pending_self_modification = None
        apply_self_modification(proposal)
        reply = f"Done. I've applied the change: {proposal['description']}. I'll remember this going forward."
        return respond(reply, speak=True)

    elif pending_self_modification and any(w in lower_cmd for w in ["no cancel", "reject", "don't", "abort", "stop"]):
        pending_self_modification = None
        return respond("Change rejected and discarded. No modifications made.", speak=True)

    # ══════════════════════════════════════════════════════════════════════
    # CASE I — EXPLICIT CORRECTION ("that was wrong", "you made a mistake")
    # ACE logs the mistake and asks Aryan for the correct answer.
    # ══════════════════════════════════════════════════════════════════════
    elif route == "correction":
        print(f"[Self-Learn]: Correction signal detected.")
        # Find the last assistant reply to log as the bad response
        last_reply   = next((m["content"] for m in reversed(chat_history) if m["role"] == "assistant"), "unknown")
        last_command = next((m["content"] for m in reversed(chat_history) if m["role"] == "user"), "unknown")
        save_mistake(last_command, last_reply, command)
        # Derive a lesson automatically
        lesson_text = ollama_call(
            FAST_MODEL,
            "You are ACE. Based on the mistake described, write one short lesson (1 sentence) "
            "that you should remember to avoid repeating this error. Start with 'Remember:'.",
            f"Mistake: {command}\nBad response was: {last_reply}"
        )
        save_lesson(lesson_text)
        reply = (
            f"Got it — I've logged that as a mistake and noted: {lesson_text}\n\n"
            "What should the correct answer have been? I'll store it so I don't repeat this."
        )
        chat_history.append({"role": "user",      "content": command})
        chat_history.append({"role": "assistant",  "content": reply})
        return respond(reply, speak=True)

    # ══════════════════════════════════════════════════════════════════════
    # CASE J — FAST CONVERSATIONAL CHAT (default)
    # Lessons from past mistakes are injected into the system prompt.
    # ══════════════════════════════════════════════════════════════════════
    else:
        print(f"⚡ [Hermes]: Conversational route -> {FAST_MODEL}")
        lessons_ctx = build_lessons_context()
        chat_system = (
            "You are ACE, a personal AI assistant. Always address Aryan as 'sir'. Use impeccable grammar, spelling, capitalization, and punctuation in your responses. No emojis. No filler phrases. "
            "You have full capabilities to search the internet/web (via the browser harness) and execute commands/open applications on the user's desktop. Never claim that you cannot access the internet, browse the web, or control the desktop. "
            "Speak like a sharp, trusted friend — warm, direct, and brief. "
            "Address the user as 'sir' naturally in conversation. "
            "Keep responses to 1 or 2 sentences unless more detail is asked for. "
            "If you do not know something, say so plainly. "
            "Never agree with bad ideas just to be agreeable — push back honestly when needed."
            + lessons_ctx
        )
        messages = [{"role": "system", "content": chat_system}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": command})

        try:
            reply = stream_and_speak_sentences(
                messages, FAST_MODEL,
                speak=(source == 'voice' and ACE_MODE != "stealth")
            )

            chat_history.append({"role": "user",      "content": command})
            chat_history.append({"role": "assistant",  "content": reply})
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
            context_string = f"{len(chat_history)}/20 SLOTS"

            return respond(reply, speak=False)
        except Exception as e:
            return respond(f"Conversation pipeline dropped: {e}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ACE SERVER — Hermes Parallel Architecture")
    print(f"  Fast:   {FAST_MODEL}")
    print(f"  Smart:  {SMART_MODEL}")
    print(f"  Coding: {CODING_MODEL}")
    print(f"  Desktop: {DESKTOP_PATH}")
    print("  Council: 6 parallel agents + Chairman")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
