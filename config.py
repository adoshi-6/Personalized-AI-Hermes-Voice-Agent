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