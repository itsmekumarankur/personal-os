# LangChain Cookbook (v1.0+, verified July 2026)

Six small, standalone Jupyter notebooks that teach LangChain using only **current, non-deprecated APIs**. Every import in these notebooks was verified to resolve against `langchain==1.3.14` / `langgraph==1.2.9`.

## Run order

| # | Notebook | What you'll learn |
|---|----------|--------------------|
| 00 | `00_setup_and_basics.ipynb` | Install packages, `init_chat_model`, invoke/stream, multi-turn messages |
| 01 | `01_prompts_and_chains.ipynb` | `ChatPromptTemplate`, LCEL (`prompt \| model \| parser`), batching, parallel runnables |
| 02 | `02_tools_and_agents.ipynb` | `@tool`, `create_agent`, running & streaming an agent |
| 03 | `03_memory_and_state.ipynb` | Checkpointers, `thread_id`-based memory, history summarization middleware |
| 04 | `04_structured_output.ipynb` | `.with_structured_output()`, Pydantic extraction, agent `response_format` |
| 05 | `05_rag_pipeline.ipynb` | Chunking, embeddings, `InMemoryVectorStore`, full RAG chain, RAG-as-a-tool |

## Before you start

1. You need an OpenAI or Anthropic API key (each notebook's setup cell lets you pick).
2. Run notebook `00` first at least once — it installs everything the rest of the cookbook needs.
3. Each notebook re-declares its own `model`/setup, so you can also jump straight to any single notebook.

## Deprecated things this cookbook deliberately avoids

If you see these in other tutorials, they're stale — this cookbook uses the current replacement instead:

| Deprecated (pre-1.0) | Current replacement |
|---|---|
| `LLMChain` | LCEL: `prompt \| model \| parser` |
| `AgentExecutor` / `initialize_agent` | `create_agent` |
| `ConversationBufferMemory` | Checkpointer (`InMemorySaver` + `thread_id`) |
| `RetrievalQA` chain | LCEL RAG chain (`{context, question} \| prompt \| model`) |
| `langchain_community` loaders/vectorstores | Standalone packages / `InMemoryVectorStore` |
| Manual "respond in JSON" prompting | `.with_structured_output(PydanticModel)` |

## Package versions this was validated against

```
langchain==1.3.14
langchain-openai==1.4.1
langchain-anthropic==1.5.2
langgraph==1.2.9
langchain-text-splitters==1.1.2
```
