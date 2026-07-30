"""
Lesson 4.2 — Personal Research Agent
Run: python agentic-ai-learning/code/research_agent.py

A complete interactive agent that searches, takes notes, and summarizes.
Combines: tools + agent loop + memory + interactive chat.
"""

import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# ============================================================
# WORKING MEMORY (persists during session)
# ============================================================
notes = []

# ============================================================
# TOOLS
# ============================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_topic",
            "description": "Search for information on a topic. Returns relevant articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a note/finding for later reference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "The note to save"}
                },
                "required": ["note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notes",
            "description": "Retrieve all saved notes.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================
def search_topic(query: str) -> str:
    """Simulated search. Replace with real API (Tavily, SerpAPI) for production."""
    fake_db = {
        "ai agents": "AI agents are autonomous systems that use LLMs to reason, plan, and take actions using tools. Key frameworks: OpenAI Agents SDK, LangChain, CrewAI.",
        "python": "Python is a high-level programming language known for readability. Popular in AI/ML, web dev, and automation. Key libs: NumPy, Pandas, PyTorch.",
        "climate change": "Global temperatures have risen ~1.1°C since pre-industrial times. Key causes: fossil fuels, deforestation. Solutions: renewable energy, carbon capture.",
        "quantum computing": "Quantum computers use qubits (superposition + entanglement) to solve certain problems exponentially faster. Leaders: IBM, Google, IonQ.",
    }
    query_lower = query.lower()
    for key, value in fake_db.items():
        if key in query_lower or query_lower in key:
            return f"📄 Found: {value}"
    return f"No specific results for '{query}'. Try: AI agents, Python, climate change, or quantum computing."


def save_note(note: str) -> str:
    notes.append(note)
    return f"✅ Note saved ({len(notes)} total): {note}"


def get_notes() -> str:
    if not notes:
        return "No notes saved yet."
    return "\n".join(f"{i+1}. {n}" for i, n in enumerate(notes))


available_functions = {
    "search_topic": search_topic,
    "save_note": save_note,
    "get_notes": get_notes,
}

# ============================================================
# AGENT
# ============================================================
SYSTEM_PROMPT = """You are a Research Assistant agent. You help users research topics.

Your workflow:
1. Use search_topic to find information
2. Use save_note to record key findings
3. Use get_notes to review what you've collected
4. Provide clear, organized summaries

Always save important findings as notes before summarizing."""


def agent_chat(messages: list, user_input: str) -> str:
    """Process one user message through the agent loop."""
    messages.append({"role": "user", "content": user_input})

    for _ in range(10):  # max iterations
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            result = available_functions[func_name](**func_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "⚠️ Reached max iterations."


# ============================================================
# INTERACTIVE LOOP
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🔬 RESEARCH AGENT")
    print("   Type 'quit' to exit, 'notes' to see saved notes")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() == "quit":
            print("\n👋 Goodbye! Your notes:", get_notes())
            break
        if user_input.lower() == "notes":
            print(f"\n📝 Your notes:\n{get_notes()}")
            continue
        if not user_input:
            continue

        reply = agent_chat(messages, user_input)
        print(f"\n🤖 Agent: {reply}")