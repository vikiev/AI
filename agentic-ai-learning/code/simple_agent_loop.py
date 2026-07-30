"""
Lesson 3.2 — Simple Agent Loop
Run: python agentic-ai-learning/code/simple_agent_loop.py

This is a REAL agent: it loops, calls tools multiple times,
and decides when it has enough info to give a final answer.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# ============================================================
# TOOLS (same as Lesson 3.1)
# ============================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. 'Mumbai'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression. Use this for any math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression, e.g. '(32 + 15) / 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# ============================================================
# ACTUAL FUNCTIONS
# ============================================================
def get_weather(city: str) -> dict:
    fake_data = {
        "mumbai": {"temperature": 32, "condition": "sunny", "humidity": "75%"},
        "london": {"temperature": 15, "condition": "rainy", "humidity": "85%"},
        "new york": {"temperature": 22, "condition": "cloudy", "humidity": "60%"},
        "tokyo": {"temperature": 28, "condition": "humid", "humidity": "80%"},
    }
    city_lower = city.lower()
    if city_lower in fake_data:
        return {"city": city, **fake_data[city_lower]}
    return {"city": city, "temperature": 25, "condition": "clear", "humidity": "50%"}


def calculate(expression: str) -> dict:
    try:
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            result = eval(expression)
            return {"expression": expression, "result": result}
        return {"error": "Invalid characters"}
    except Exception as e:
        return {"error": str(e)}


available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
}

# ============================================================
# THE AGENT LOOP ⭐ (This is the core concept!)
# ============================================================
def agent_loop(user_message: str, max_iterations: int = 10):
    """
    A simple agent that keeps calling tools until done.
    This IS the THINK → ACT → OBSERVE loop.
    """
    print(f"\n{'='*60}")
    print(f"👤 User: {user_message}")
    print(f"{'='*60}")

    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use tools to gather information, then provide a complete answer."},
        {"role": "user", "content": user_message}
    ]

    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")

        # 🧠 THINK: Ask the LLM what to do
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        # ✅ DONE? If no tool calls, we have the final answer
        if not message.tool_calls:
            print(f"\n{'='*60}")
            print(f"🤖 Final Answer: {message.content}")
            print(f"{'='*60}")
            print(f"\n📊 Total iterations used: {iteration + 1}")
            return message.content

        # 🔨 ACT + 👁️ OBSERVE: Execute tools and feed results back
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"  🔧 Calling: {func_name}({func_args})")

            result = available_functions[func_name](**func_args)

            print(f"  📋 Result: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        # → Loop back to THINK

    print("⚠️ Max iterations reached — stopping to prevent infinite loop!")
    return None


# ============================================================
# TEST IT
# ============================================================
if __name__ == "__main__":
    # Simple: one tool call
    agent_loop("What's the weather in Tokyo?")

    # Multi-step: multiple tool calls across iterations
    agent_loop("What's the weather in Mumbai and London? Calculate the average temperature of both cities.")

    # No tools needed
    agent_loop("What is the capital of Japan?")