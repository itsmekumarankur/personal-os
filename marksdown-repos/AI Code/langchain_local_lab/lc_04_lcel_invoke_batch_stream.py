"""LC-04  Every chain is a Runnable: invoke / batch / stream.  Run: python lc_04_lcel_invoke_batch_stream.py"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from common import get_llm

chain = ChatPromptTemplate.from_template("Explain {topic} in one sentence.") | get_llm() | StrOutputParser()

print("chain type :", type(chain).__name__)            # RunnableSequence
print("its steps  :", [type(s).__name__ for s in chain.steps])

print("\n--- invoke (one input, one output) ---")
print(chain.invoke({"topic": "a vector database"}))

print("\n--- batch (many inputs, run in parallel) ---")
for out in chain.batch([{"topic": "Kubernetes"}, {"topic": "OAuth"}, {"topic": "idempotency"}]):
    print("-", out)

print("\n--- stream (tokens as they arrive) ---")
for piece in chain.stream({"topic": "event sourcing"}):
    print(piece, end="", flush=True)
print()


"""
Concept. Everything you build with | is a Runnable and automatically gets three ways to run: invoke, batch, stream.

New things in this step

RunnableSequence and .steps
.batch() runs many inputs in parallel
.stream() yields tokens as they are generated

Architecture view. Same chain, three execution modes. batch uses a thread pool; stream keeps one connection open.
"""