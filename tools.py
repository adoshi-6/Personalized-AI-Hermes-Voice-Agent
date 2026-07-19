import json
import os
import requests
import psutil
from datetime import datetime
from duckduckgo_search import DDGS

# Master tool definitions map for Qwen
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
      "description": "Fetches real-time weather information for a specified location city.",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "The city name, e.g., London, Paris"}
        },
        "required": ["location"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "open_local_application",
      "description": "Opens a local desktop application natively on the computer system.",
      "parameters": {
        "type": "object",
        "properties": {
          "app_name": {"type": "string", "description": "The name of the app (notepad, calculator, chrome)"}
        },
        "required": ["app_name"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_system_metrics",
      "description": "Checks the computer's live hardware status including CPU usage, RAM memory usage, and battery life.",
      "parameters": {"type": "object", "properties": {}, "required": []}
    }
  },
  {
    "type": "function",
    "function": {
      "name": "search_web",
      "description": "Searches the live internet to extract real-time web summaries, current prices, news, or answers.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "The search term or question to look up on the web"}
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_current_time",
      "description": "Returns the current accurate local date and time from the system clock.",
      "parameters": {"type": "object", "properties": {}, "required": []}
    }
  },
  {
    "type": "function",
    "function": {
      "name": "manage_desktop_file",
      "description": "Writes, appends, or reads plain text files directly on the user's desktop screen.",
      "parameters": {
        "type": "object",
        "properties": {
          "action": {"type": "string", "enum": ["write", "append", "read"], "description": "The file operation to perform"},
          "filename": {"type": "string", "description": "The name of the file, e.g., todo.txt or notes.txt"},
          "content": {"type": "string", "description": "The text content to write or append to the file (leave empty for read)"}
        },
        "required": ["action", "filename"]
      }
    }
  }
]

def get_calendar_events():
  return json.dumps({"events": [
    {"id": 1, "title": "Brainstorming with Aryan", "time": "2:00 PM"},
    {"id": 2, "title": "Review AI Agent project configuration", "time": "4:30 PM"}
  ]})

def get_live_weather(location):
  try:
    clean_location = location.strip().replace(" ", "+")
    url = f"https://wttr.in/{clean_location}?format=3"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
      return response.text.strip()
    return f"I couldn't look up the weather for '{location}' right now."
  except Exception as e:
    return f"Weather engine error: {str(e)}"

def open_local_application(app_name):
  app = app_name.lower().strip()
  if "notepad" in app:
    os.system("start notepad")
    return "Successfully opened Notepad."
  elif "calculator" in app or "calc" in app:
    os.system("start calc")
    return "Successfully opened the Calculator."
  elif "browser" in app or "chrome" in app or "internet" in app:
    os.system("start chrome")
    return "Successfully opened your web browser."
  else:
    return f"Application context '{app_name}' is not in my allowed local safe-list yet."

def get_system_metrics():
  try:
    cpu = psutil.cpu_percent(interval=0.3)
    memory = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    battery_str = f"{battery.percent}%" if battery else "Not detected"
    return json.dumps({"cpu_utilization": f"{cpu}%", "ram_usage": f"{memory}%", "battery_level": battery_str})
  except Exception as e:
    return f"Failed to retrieve system metrics: {str(e)}"

def search_web(query):
  """Queries live web layers utilizing the official ddgs library to fetch real-time data."""
  try:
    with DDGS() as ddgs:
      results = ddgs.text(query, max_results=3)
      if results:
        clean_results = []
        for r in results:
          title = r.get("title", "Web Source")
          body = r.get("body", "")
          clean_results.append(f"- From {title}: {body}")
        return "Live Search Findings:\n" + "\n".join(clean_results)
    return f"The search completed, but no direct web description snippets were returned for '{query}'."
  except Exception as e:
    return f"Web browsing connection interface error: {str(e)}"

def get_current_time():
  now = datetime.now()
  return now.strftime("Today is %A, %B %d, %Y. The current local time is %I:%M %p.")

def manage_desktop_file(action, filename, content=""):
  desktop_path = r"C:\Users\Aryan\OneDrive\Desktop"
  target_file = os.path.join(desktop_path, filename)
  try:
    if action == "write":
      with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
      return f"Successfully created and wrote to '{filename}' on your Desktop."
    elif action == "append":
      with open(target_file, "a", encoding="utf-8") as f:
        f.write("\n" + content)
      return f"Successfully added the update to '{filename}' on your Desktop."
    elif action == "read":
      if not os.path.exists(target_file):
        return f"The file '{filename}' does not exist on your Desktop yet."
      with open(target_file, "r", encoding="utf-8") as f:
        return f.read()
  except Exception as e:
    return f"File management operation failed: {str(e)}"

def execute_tool(name, arguments_json):
  try:
    args = json.loads(arguments_json) if isinstance(arguments_json, str) else arguments_json
  except Exception:
    args = {}

  try:
    from trust_ledger import log_event
    log_event("TOOL_CALL", name, "EXECUTED", {"args": args})
  except Exception:
    pass

  if name == "get_calendar_events": return get_calendar_events()
  elif name == "get_live_weather": return get_live_weather(args.get("location", "New York"))
  elif name == "open_local_application": return open_local_application(args.get("app_name", ""))
  elif name == "get_system_metrics": return get_system_metrics()
  elif name == "search_web": return search_web(args.get("query", ""))
  elif name == "get_current_time": return get_current_time()
  elif name == "manage_desktop_file":
    return manage_desktop_file(args.get("action"), args.get("filename"), args.get("content", ""))
  else:
    return f"Error: Tool '{name}' is unknown."