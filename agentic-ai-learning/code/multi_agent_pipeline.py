"""
Lesson 5.1/5.2 — Multi-Agent Pipeline
Run: python agentic-ai-learning/code/multi_agent_pipeline.py

Demonstrates: 3 specialized agents working in a pipeline
  Researcher → Writer → Editor → Final Output

Each "agent" is just an LLM call with a different system prompt!
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


def call_agent(system_prompt: str, user_message: str, agent_name: str) -> str:
    """Call a single agent (LLM with a specific persona)."""
    print(f"\n{'─'*50}")
    print(f"🤖 [{agent_name}] working...")
    print(f"{'─'*50}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=500
    )

    result = response.choices[0].message.content
    print(f"📝 [{agent_name}] output:\n{result[:200]}...")
    return result


# ============================================================
# THE PIPELINE: Researcher → Writer → Editor
# ============================================================

def content_pipeline(topic: str) -> str:
    """Run a topic through a 3-agent pipeline."""
    print(f"\n{'='*60}")
    print(f"📋 TOPIC: {topic}")
    print(f"{'='*60}")

    # Agent 1: RESEARCHER
    research = call_agent(
        system_prompt="You are a Research Agent. Find and list 3-4 key facts about the topic. Be concise and factual.",
        user_message=f"Research this topic: {topic}",
        agent_name="Researcher"
    )

    # Agent 2: WRITER
    draft = call_agent(
        system_prompt="You are a Writer Agent. Write a short, engaging paragraph (3-4 sentences) based on the research provided.",
        user_message=f"Write a short paragraph based on this research:\n{research}",
        agent_name="Writer"
    )

    # Agent 3: EDITOR
    final = call_agent(
        system_prompt="You are an Editor Agent. Improve the text for clarity, grammar, and impact. Return ONLY the improved text.",
        user_message=f"Edit and improve this text:\n{draft}",
        agent_name="Editor"
    )

    return final


# ============================================================
# BONUS: Debate Pattern (2 agents + judge)
# ============================================================

def debate(question: str) -> str:
    """Two agents argue, a judge decides."""
    print(f"\n{'='*60}")
    print(f"⚖️ DEBATE: {question}")
    print(f"{'='*60}")

    # Agent A: argues FOR
    arg_for = call_agent(
        system_prompt="You argue FOR the statement. Give 2 strong reasons. Be persuasive but honest.",
        user_message=f"Argue FOR: {question}",
        agent_name="Agent-FOR"
    )

    # Agent B: argues AGAINST
    arg_against = call_agent(
        system_prompt="You argue AGAINST the statement. Give 2 strong counter-reasons. Be persuasive but honest.",
        user_message=f"Argue AGAINST: {question}",
        agent_name="Agent-AGAINST"
    )

    # Judge: decides
    verdict = call_agent(
        system_prompt="You are a Judge. Weigh both arguments fairly and give a balanced verdict in 2-3 sentences.",
        user_message=f"FOR argument:\n{arg_for}\n\nAGAINST argument:\n{arg_against}\n\nGive your verdict.",
        agent_name="Judge"
    )

    return verdict


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    # Pipeline demo
    final_article = content_pipeline("AI agents in healthcare")
    print(f"\n{'='*60}")
    print(f"✅ FINAL OUTPUT:\n{final_article}")
    print(f"{'='*60}")

    # Debate demo
    verdict = debate("AI agents will replace most office jobs within 10 years")
    print(f"\n{'='*60}")
    print(f"⚖️ VERDICT:\n{verdict}")
    print(f"{'='*60}")