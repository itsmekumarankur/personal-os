"""
common.py - tiny shared helpers for the safeguards + evaluation lab.

get_llm()       -> a chat model (Claude if ANTHROPIC_API_KEY set, else local Ollama).
get_judge_llm() -> same as get_llm(), but named separately because in real systems
                    the "judge" model is often a DIFFERENT/cheaper model than the
                    one being evaluated, to reduce "model grading itself" bias.
"""
import os


def get_llm():
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"))
    from langchain_ollama import ChatOllama
    return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1"), temperature=0)


def get_judge_llm():
    # return ChatAnthropic(model="claude-haiku-5-5")   # <- swap to a separate judge model
    return get_llm()
