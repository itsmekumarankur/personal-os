"""LC-07  Routing: classify the question, then pick a chain.  Run: python lc_07_routing.py"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from common import get_llm

llm, parser = get_llm(), StrOutputParser()

classifier = ChatPromptTemplate.from_template(
    "Classify the question into exactly one word: math, code, or other.\nQuestion: {question}\nAnswer with the word only."
) | llm | parser

math_chain = ChatPromptTemplate.from_template("You are a math tutor. Answer briefly: {question}") | llm | parser
code_chain = ChatPromptTemplate.from_template("You are a senior developer. Answer briefly: {question}") | llm | parser
other_chain = ChatPromptTemplate.from_template("You are a helpful assistant. Answer briefly: {question}") | llm | parser


def route(info: dict):
    topic = info["topic"].strip().lower()
    print(f"  [router] topic = {topic!r}")
    if "math" in topic:
        return math_chain          # a Runnable returned here is executed automatically
    if "code" in topic:
        return code_chain
    return other_chain


full = RunnablePassthrough.assign(topic=classifier) | RunnableLambda(route)

for q in ["What is 17 * 23?", "How do I reverse a list in Python?", "Who wrote Gitanjali?"]:
    print("Q:", q)
    print("A:", full.invoke({"question": q}), "\n")


"""
Concept. Sometimes the next step depends on the input. A classifier chain picks, a router function returns the chain to run.

New things in this step

A RunnableLambda may return another Runnable, which is then executed
Classify first, answer second
Why routing is a stepping stone to LangGraph's conditional edges
Architecture view. Two LLM calls per question: one cheap classification call, then one specialised call.

"""