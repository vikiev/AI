"""
Lesson 4.1 — OpenAI Agents SDK Demo
Run: python agentic-ai-learning/code/agents_sdk_demo.py

First install: pip install openai-agents

Compare this to simple_agent_loop.py — same behavior, way less code!
"""

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# TOOLS — just use @function_tool decorator!
# No JSON schemas needed. The SDK reads your docstring + type hints.
# ============================================================

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    fake_data = {
        "mumbai": "32°C, sunny, 75% humidity",
        "london": "15°C, rainy, 85% humidity",
        "tokyo": "28°C, humid, 80% humidity",
    }
    return fake_data.get(city.lower(), f"25°C, clear (default for {city})")


@function_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression. Use for any math."""
    try:
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Error: invalid characters"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# CREATE THE AGENT — that's it!
# ============================================================

agent = Agent(
    name="HelperBot",
    instructions="You are a helpful assistant. Use tools when needed, then give a clear final answer.",
    model="gpt-4o-mini",
    tools=[get_weather, calculate]
)


# ============================================================
# RUN IT
# ============================================================

if __name__ == "__main__":
    questions = [
        "What's the weather in Mumbai?",
        "Calculate (32 + 15) / 2",
        "What is the capital of France?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"👤 User: {q}")
        print(f"{'='*60}")

        result = Runner.run_sync(agent, q)

        print(f"🤖 Agent: {result.final_output}")
        print(f"   (Steps taken: {len(result.steps)})")