"""
Lesson 3.1 — Function Calling Demo
Run: python agentic-ai-learning/code/function_calling_demo.py

This demonstrates how an LLM decides to call a tool,
and how your code executes it and sends the result back.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# ============================================================
# STEP 1: Define your tools (the "menu" for the LLM)
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
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression, e.g. '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# ============================================================
# STEP 2: Define the actual functions (YOUR code)
# ============================================================
def get_weather(city: str) -> dict:
    """Simulated weather lookup. In real life, call a weather API."""
    fake_data = {
        "mumbai": {"temperature": 32, "condition": "sunny", "humidity": "75%"},
        "london": {"temperature": 15, "condition": "rainy", "humidity": "85%"},
        "new york": {"temperature": 22, "condition": "cloudy", "humidity": "60%"},
    }
    city_lower = city.lower()
    if city_lower in fake_data:
        return fake_data[city_lower]
    return {"temperature": 25, "condition": "clear", "humidity": "50%", "note": f"No data for {city}, returning default"}


def calculate(expression: str) -> dict:
    """Safely evaluate a math expression."""
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            result = eval(expression)
            return {"expression": expression, "result": result}
        return {"error": "Invalid characters in expression"}
    except Exception as e:
        return {"error": str(e)}


# Map function names to actual functions
available_functions = {
    "get_weather": get_weather,
    "calculate": calculate,
}

# ============================================================
# STEP 3: The conversation loop
# ============================================================
def chat_with_tools(user_message: str):
    print(f"\n{'='*60}")
    print(f"👤 User: {user_message}")
    print(f"{'='*60}")

    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when needed."},
        {"role": "user", "content": user_message}
    ]

    # First LLM call — it may want to use a tool
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # Check: does the LLM want to call a tool?
    if message.tool_calls:
        print(f"\n🔧 LLM wants to call a tool!")
        
        # Add assistant's message (with tool_calls) to conversation
        messages.append(message)

        # Process each tool call (there could be multiple)
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            
            print(f"   → Function: {func_name}")
            print(f"   → Arguments: {func_args}")

            # Execute the function
            func = available_functions[func_name]
            result = func(**func_args)
            
            print(f"   → Result: {result}")

            # Send result back to LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        # Second LLM call — now it has the tool result
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )
        print(f"\n🤖 Assistant: {final_response.choices[0].message.content}")
    else:
        # No tool call — direct answer
        print(f"\n🤖 Assistant: {message.content}")


# ============================================================
# STEP 4: Try different questions
# ============================================================
if __name__ == "__main__":
    # This should trigger get_weather
    chat_with_tools("What's the weather like in Mumbai?")

    # This should trigger calculate
    chat_with_tools("What is 15% of 2400? Calculate it.")

    # This should NOT trigger any tool (direct answer)
    chat_with_tools("What is the capital of France?")