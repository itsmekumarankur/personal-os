"""LG-12  Multi-agent #1: agents talk through SHARED STATE (researcher -> writer -> reviewer).  Run: python lg_12_multi_agent_shared_state.py"""
from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from common import get_llm

llm = get_llm()


class State(TypedDict):          # THIS is the "communication channel" between agents
    topic: str
    notes: str                   # written by researcher, read by writer
    draft: str                   # written by writer, read by reviewer
    review: str                  # written by reviewer


def run_agent(role_prompt: str, task: str) -> str:
    return llm.invoke([SystemMessage(role_prompt), HumanMessage(task)]).text


def researcher(s: State):
    return {"notes": run_agent("You are a researcher. Give exactly 4 short factual bullet points.", s["topic"])}


def writer(s: State):            # sees ONLY topic + notes (not the reviewer's key)
    return {"draft": run_agent("You are a writer. Write a 3-sentence paragraph using only the notes.",
                               f"Topic: {s['topic']}\nNotes:\n{s['notes']}")}


def reviewer(s: State):          # sees the draft + the original notes
    return {"review": run_agent("You are a strict reviewer. Reply 'OK' or list one factual problem vs the notes.",
                                f"Notes:\n{s['notes']}\n\nDraft:\n{s['draft']}")}


b = StateGraph(State)
b.add_node("researcher", researcher); b.add_node("writer", writer); b.add_node("reviewer", reviewer)
b.add_edge(START, "researcher"); b.add_edge("researcher", "writer"); b.add_edge("writer", "reviewer"); b.add_edge("reviewer", END)
graph = b.compile()

for update in graph.stream({"topic": "How UPI payments work in India"}, stream_mode="updates"):
    for agent_name, written in update.items():
        key, value = next(iter(written.items()))
        print(f"\n### {agent_name} wrote state['{key}']\n{value}")


"""
        TOPIC: "How UPI payments work in India"
                         |
                         v
              +-------------------+
              |    RESEARCHER     |
              | Finds 4 facts     |
              +-------------------+
                         |
                         v
              SHARED STATE: notes
              (Research findings)
                         |
                         v
              +-------------------+
              |      WRITER       |
              | Reads the notes   |
              | Writes 3 sentences|
              +-------------------+
                         |
                         v
              SHARED STATE: draft
              (Written paragraph)
                         |
                         v
              +-------------------+
              |     REVIEWER      |
              | Checks draft      |
              | against the notes |
              +-------------------+
                         |
                         v
              SHARED STATE: review
              (OK or factual problem)
                         |
                         v
                        END
"""