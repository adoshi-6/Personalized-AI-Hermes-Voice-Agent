from openai import OpenAI
from tools import TOOL_DEFINITIONS
from config import SMART_MODEL

# Uses the OpenAI-compatible API that Model server exposes on port 11434.
# This lets us use the standard OpenAI SDK to talk to local models.
client = OpenAI(
 base_url="http://localhost:11434/v1",
 api_key="ollama" # Model server requires any non-empty string here
)


def generate_response(conversation_history: list, system_prompt: str):
 """
 Sends the full conversation to the local model and returns a streaming
 response object. Tool definitions are passed so the model can decide
 to call a tool rather than reply in text.

 Returns None on connection error (e.g. Ollama not running).
 """
 messages = [{"role": "system", "content": system_prompt}] + conversation_history

 try:
 response = client.chat.completions.create(
 model=SMART_MODEL,
 messages=messages,
 tools=TOOL_DEFINITIONS,
 stream=True,
 )
 return response
 except Exception as e:
 print(f"[Model provider error: {e}]")
 return None