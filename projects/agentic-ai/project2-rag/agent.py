import os

from anthropic import Anthropic

from rag import index

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = (
    "You answer questions using the company documents available through the "
    "search_documents tool. Always search before answering a factual question. "
    "Answer only from the passages returned, and name the source file you used. "
    "If the passages do not contain the answer, say you could not find it in the "
    "documents instead of guessing."
)

tools = [
    {
        "name": "search_documents",
        "description": "Semantic search over the document collection. Returns the most relevant passages with their source file names.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for, phrased as a short question or topic"}
            },
            "required": ["query"],
        },
    }
]


def run_search_documents(query: str, sources: set) -> str:
    hits = index.search(query, k=3)
    for h in hits:
        sources.add(h["source"])
    return "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)


def run_agent(user_message: str, max_turns: int = 5) -> tuple[str, list[str]]:
    messages = [{"role": "user", "content": user_message}]
    sources: set = set()

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            reply = "".join(b.text for b in response.content if b.type == "text")
            return reply, sorted(sources)

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_search_documents(block.input["query"], sources)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})

    return "Reached max turns without a final answer.", sorted(sources)
