import json
import os
import requests
import psutil
from datetime import datetime
from duckduckgo_search import DDGS

from config import DESKTOP_PATH, USER_NAME

# ── Tool Definitions ──────────────────────────────────────────────────────────
# These are passed to the model so it knows what tools are available.
# The model uses these descriptions to decide which tool to call.
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Returns a list of scheduled calendar events for today.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_live_weather",
            "description": "Fetches real-time weather for a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. London or Paris"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_local_application",
            "description": "Opens a local desktop application on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "App to open: notepad, calculator, or chrome"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_metrics",
            "description": "Returns live CPU usage, RAM usage, and battery level.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the internet for real-time information, news, or facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current local date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_desktop_file",
            "description": "Reads, writes, or appends text files on the user's desktop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["write", "append", "read"],
                        "description": "File operation to perform"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file, e.g. notes.txt"
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to write or append (leave empty for read)"
                    }
                },
                "required": ["action", "filename"]
            }
        }
    }
]


# ── Tool Implementations ───────────────────────────────────────────────────────

def get_calendar_events() -> str:
    """Returns a placeholder calendar. Replace with a real Google Calendar
    integration when ready."""
    return json.dumps({"events": [
        {"id": 1, "title": "Team meeting",   "time": "2:00 PM"},
        {"id": 2, "title": "Project review", "time": "4:30 PM"},
    ]})


def get_live_weather(location: str) -> str:
    try:
        clean = location.strip().replace(" ", "+")
        response = requests.get(f"https://wttr.in/{clean}?format=3", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return f"Could not fetch weather for '{location}'."
    except Exception as e:
        return f"Weather error: {e}"


def open_local_application(app_name: str) -> str:
    app = app_name.lower().strip()
    if "notepad" in app:
        os.system("start notepad")
        return "Opened Notepad."
    elif "calculator" in app or "calc" in app:
        os.system("start calc")
        return "Opened Calculator."
    elif "chrome" in app or "browser" in app:
        os.system("start chrome")
        return "Opened Chrome."
    else:
        return f"'{app_name}' is not on the allowed app list."


def get_system_metrics() -> str:
    try:
        cpu     = psutil.cpu_percent(interval=0.3)
        memory  = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        batt_str = f"{battery.percent}%" if battery else "Not detected"
        return json.dumps({
            "cpu":     f"{cpu}%",
            "ram":     f"{memory}%",
            "battery": batt_str,
        })
    except Exception as e:
        return f"System metrics error: {e}"


def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
            if results:
                lines = []
                for r in results:
                    lines.append(f"- {r.get('title', 'Source')}: {r.get('body', '')}")
                return "Search results:\n" + "\n".join(lines)
        return f"No results found for '{query}'."
    except Exception as e:
        return f"Search error: {e}"


def get_current_time() -> str:
    now = datetime.now()
    return now.strftime("Today is %A, %B %d, %Y. The time is %I:%M %p.")


def manage_desktop_file(action: str, filename: str, content: str = "") -> str:
    target = os.path.join(DESKTOP_PATH, filename)
    try:
        if action == "write":
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written to '{filename}' on your desktop."
        elif action == "append":
            with open(target, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return f"Appended to '{filename}' on your desktop."
        elif action == "read":
            if not os.path.exists(target):
                return f"'{filename}' does not exist on your desktop."
            with open(target, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        return f"File operation failed: {e}"


def execute_tool(name: str, arguments_json) -> str:
    """Dispatcher — routes a tool call by name to the correct function."""
    try:
        args = json.loads(arguments_json) if isinstance(arguments_json, str) else arguments_json
    except Exception:
        args = {}

    if name == "get_calendar_events":
        return get_calendar_events()
    elif name == "get_live_weather":
        return get_live_weather(args.get("location", "New York"))
    elif name == "open_local_application":
        return open_local_application(args.get("app_name", ""))
    elif name == "get_system_metrics":
        return get_system_metrics()
    elif name == "search_web":
        return search_web(args.get("query", ""))
    elif name == "get_current_time":
        return get_current_time()
    elif name == "manage_desktop_file":
        return manage_desktop_file(
            args.get("action"),
            args.get("filename"),
            args.get("content", "")
        )
    else:
        return f"Unknown tool: '{name}'"