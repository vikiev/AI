"""
Lesson 7.1 — Capstone: Personal AI Assistant
Run: python agentic-ai-learning/code/capstone_assistant.py

A production-ready agent combining:
- Agent loop with streaming
- Function calling (6 tools)
- Conversation memory
- Persistent notes (JSON file)
- Real APIs (Wikipedia — no key needed!)
- Error handling + retry logic
- Token budget tracking
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError

load_dotenv()
client = OpenAI(timeout=30.0)

# ============================================================
# CONFIG
# ============================================================
MODEL = "gpt-4o-mini"
MAX_ITERATIONS = 10
MAX_TOKENS_BUDGET = 50000
NOTES_FILE = Path(__file__).parent / "notes.json"

SYSTEM_PROMPT = """You are a helpful personal AI assistant. You have access to tools for:
- Looking up information (Wikipedia)
- Checking the weather
- Saving and recalling notes
- Doing calculations
- Telling the time

Be concise but helpful. Use tools when they'd provide better answers than your training data.
If you don't know something and no tool helps, say so honestly."""


# ============================================================
# TOOLS
# ============================================================

def get_time() -> str:
    """Get current date and time."""
    now = datetime.now()
    return f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}"


def calculate(expression: str) -> str:
    """Safely evaluate a math expression."""
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Error: Only basic math operations (+, -, *, /, parentheses) are allowed."
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information."""
    try:
        # Try direct page summary first
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        resp = requests.get(url, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            return f"📖 {data['title']}\n\n{data['extract']}"

        # Fallback: search
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 3
        }
        search_resp = requests.get(search_url, params=params, timeout=10)
        results = search_resp.json().get("query", {}).get("search", [])

        if not results:
            return f"No Wikipedia results found for '{query}'."

        output = [f"Search results for '{query}':"]
        for r in results:
            snippet = r["snippet"].replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            output.append(f"  • {r['title']}: {snippet}")
        return "\n".join(output)

    except requests.exceptions.Timeout:
        return "Error: Wikipedia request timed out."
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


def get_weather(city: str) -> str:
    """Get weather (uses wttr.in — no API key needed!)."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        area = data["nearest_area"][0]

        return (
            f"Weather in {area['areaName'][0]['value']}, {area['country'][0]['value']}:\n"
            f"  🌡️ Temperature: {current['temp_C']}°C (feels like {current['FeelsLikeC']}°C)\n"
            f"  ☁️ Condition: {current['weatherDesc'][0]['value']}\n"
            f"  💧 Humidity: {current['humidity']}%\n"
            f"  💨 Wind: {current['windspeedKmph']} km/h {current['winddir16Point']}\n"
            f"  👁️ Visibility: {current['visibility']} km"
        )
    except requests.exceptions.Timeout:
        return "Error: Weather service timed out."
    except Exception as e:
        return f"Weather error: {str(e)}"


def save_note(note: str) -> str:
    """Save a note to persistent storage."""
    try:
        notes = []
        if NOTES_FILE.exists():
            notes = json.loads(NOTES_FILE.read_text())

        notes.append({
            "text": note,
            "saved_at": datetime.now().isoformat()
        })

        NOTES_FILE.write_text(json.dumps(notes, indent=2))
        return f"✅ Note saved! (Total notes: {len(notes)})"
    except Exception as e:
        return f"Error saving note: {str(e)}"


def recall_notes() -> str:
    """Recall all saved notes."""
    try:
        if not NOTES_FILE.exists():
            return "No notes saved yet."

        notes = json.loads(NOTES_FILE.read_text())
        if not notes:
            return "No notes saved yet."

        output = [f"📝 Your notes ({len(notes)} total):"]
        for i, note in enumerate(notes, 1):
            date = datetime.fromisoformat(note["saved_at"]).strftime("%b %d, %I:%M %p")
            output.append(f"  {i}. \"{note['text']}\" (saved {date})")
        return "\n".join(output)
    except Exception as e:
        return f"Error reading notes: {str(e)}"


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression. Supports +, -, *, /, parentheses.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Math expression, e.g. '2 + 3 * 4'"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for factual information about any topic.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Topic to look up"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for any city in the world.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name, e.g. 'London' or 'Tokyo'"}},
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a note for later. Use when the user wants to remember something.",
            "parameters": {
                "type": "object",
                "properties": {"note": {"type": "string", "description": "The note text to save"}},
                "required": ["note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_notes",
            "description": "Recall all previously saved notes.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]

AVAILABLE_FUNCTIONS = {
    "get_time": get_time,
    "calculate": calculate,
    "search_wikipedia": search_wikipedia,
    "get_weather": get_weather,
    "save_note": save_note,
    "recall_notes": recall_notes,
}


# ============================================================
# AGENT ENGINE
# ============================================================

class Budget:
    """Track token usage."""
    def __init__(self, max_tokens=MAX_TOKENS_BUDGET):
        self.tokens_used = 0
        self.max_tokens = max_tokens
        self.api_calls = 0

    def track(self, usage):
        self.tokens_used += usage.total_tokens
        self.api_calls += 1

    def exceeded(self):
        return self.tokens_used > self.max_tokens

    def report(self):
        # gpt-4o-mini: $0.15/1M input, $0.60/1M output (rough avg $0.30/1M)
        cost = self.tokens_used * 0.0000003
        print(f"\n📊 Session stats: {self.api_calls} API calls | {self.tokens_used:,} tokens | ~${cost:.4f}")


def safe_api_call(messages, tools, budget: Budget, max_retries=3):
    """API call with retry logic."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                max_tokens=2000
            )
            budget.track(response.usage)
            return response
        except RateLimitError:
            wait = 2 ** attempt
            print(f"\n⚠️ Rate limited. Waiting {wait}s...")
            time.sleep(wait)
        except APIConnectionError:
            wait = 2 ** attempt
            print(f"\n⚠️ Connection error. Retrying in {wait}s...")
            time.sleep(wait)
    raise Exception("Max retries exceeded. Check your internet connection.")


def run_agent(user_message: str, messages: list, budget: Budget) -> str:
    """Run the agent loop for one user message."""
    messages.append({"role": "user", "content": user_message})

    for iteration in range(MAX_ITERATIONS):
        if budget.exceeded():
            return "⚠️ Token budget exceeded. Starting a new session is recommended."

        response = safe_api_call(messages, TOOLS, budget)
        message = response.choices[0].message
        messages.append(message)

        # No tool calls → final answer
        if not message.tool_calls:
            return message.content

        # Execute tool calls
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"\n🔧 [{func_name}]({func_args})")

            # Execute
            if func_name in AVAILABLE_FUNCTIONS:
                result = AVAILABLE_FUNCTIONS[func_name](**func_args)
            else:
                result = f"Error: Unknown function '{func_name}'"

            print(f"   → {result[:100]}{'...' if len(result) > 100 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "⚠️ Max iterations reached. The task may be too complex."


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("🤖 PERSONAL AI ASSISTANT")
    print("=" * 60)
    print("Tools: Wikipedia | Weather | Notes | Calculator | Time")
    print("Type 'quit' to exit, 'stats' for usage stats")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    budget = Budget()

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            budget.report()
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("\nGoodbye! 👋")
            budget.report()
            break
        if user_input.lower() == "stats":
            budget.report()
            continue

        print("\n🤖 Assistant: ", end="", flush=True)
        response = run_agent(user_input, messages, budget)
        print(response)


if __name__ == "__main__":
    main()