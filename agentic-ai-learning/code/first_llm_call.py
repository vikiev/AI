"""
Lesson 2.3 — Your First LLM Call
Run: python agentic-ai-learning/code/first_llm_call.py
"""

from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env file
load_dotenv()

# Create the client (auto-reads OPENAI_API_KEY)
client = OpenAI()

# Send the request
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain AI agents in 2 sentences."}
    ]
)

# Print the response
print("=" * 50)
print("🤖 AI Response:")
print("=" * 50)
print(response.choices[0].message.content)
print("=" * 50)

# Bonus: Print token usage
usage = response.usage
print(f"\n📊 Token Usage:")
print(f"   Prompt tokens:     {usage.prompt_tokens}")
print(f"   Completion tokens: {usage.completion_tokens}")
print(f"   Total tokens:      {usage.total_tokens}")