# =============================================================
# config.py — User Configuration
# =============================================================
# This is the only file you need to edit before running the
# assistant. Change the values below to match your setup.
# Every other file in the project reads from here.
# =============================================================


# ── Identity ──────────────────────────────────────────────────
# The name the assistant calls itself and responds to.
ASSISTANT_NAME = "Jarvis"

# The name the assistant uses to address you.
USER_NAME = "User"

# The default background color of the UI dashboard
BACKGROUND_COLOR = "#0E0F13"


# ── AI Models ─────────────────────────────────────────────────
# These must be pulled in Ollama before running.
# Example: run  ollama pull qwen3:1.7b  in your terminal.
FAST_MODEL  = "qwen3:1.7b"     # Used for quick conversational replies
SMART_MODEL = "qwen3:4b"       # Used for council debates and research


# ── Voice ─────────────────────────────────────────────────────
# Edge-TTS voice tag. Run list_voices.py to see all options.
# Examples: "en-GB-RyanNeural", "en-US-AndrewNeural"
VOICE_TAG = "en-GB-RyanNeural"


# ── Wake Word ─────────────────────────────────────────────────
# What you say to activate the assistant when in open-mic mode.
WAKE_WORD = "hey jarvis"


# ── File Paths ────────────────────────────────────────────────
# Where conversation history is saved between sessions.
HISTORY_FILE = "conversation_history.json"

# Path to your desktop for file read/write operations.
# Windows example: r"C:\Users\YourName\Desktop"
DESKTOP_PATH = r"C:\Users\YourName\Desktop"


# ── Council ───────────────────────────────────────────────────
# Keywords that trigger the multi-agent council debate.
COUNCIL_TRIGGERS = ["council", "debate", "evaluate", "boardroom"]

# ── Security ──────────────────────────────────────────────────────────────────
# PIN length — must be exactly this many digits to be accepted.
PIN_LENGTH = 6

# Actions that always require a PIN before running.
# Add or remove entries to control what needs confirmation.
PROTECTED_ACTIONS = [
    "send_message",
    "delete_data",
    "change_setting",
    "first_time_access",
    "write_file",
    "store_password",
    "code_word",
    "factory_reset",
]

# Code words and what they do.
# Format: "phrase you say" : ("internal_action_key", "description shown to you before PIN")
# Change the phrases to anything you want — these are the words the assistant listens for.
# The action keys must stay exactly as they are (they map to internal logic).
CODE_WORDS = {
    "shutdown now":   ("code_black",    "shut down everything immediately"),
    "safe mode":      ("safe_mode",     "disable internet and desktop access — chat only"),
    "focus mode":     ("focus_mode",    "block all proactive interruptions"),
    "stealth mode":   ("stealth_mode",  "disable all audio output — text only"),
    "briefing":       ("briefing",      "summarise everything since your last session"),
    "factory reset":  ("factory_reset", "wipe ALL memory — cannot be undone"),
    "stand down":     ("stand_down",    "pause all background activity"),
    "ghost mode":     ("ghost_mode",    "stop logging anything this session"),
    "purge session":  ("purge",         "clear this session only, keep long-term memory"),
    "lockdown":       ("lockdown",      "stop responding to anyone until unlocked"),
    "high alert":     ("red_alert",     "require confirmation before every action"),
    "save and quit":  ("handoff",       "save a session summary to desktop then shut down"),
    "status report":  ("debrief",       "report everything done since last check-in"),
}

# Unlock phrases accepted during lockdown mode.
# The assistant only responds to these when lockdown is active.
UNLOCK_PHRASES = ["unlock", "i am the owner", "disengage lockdown"]
