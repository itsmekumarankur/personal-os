"""LC-06  Compose chains: sequential + parallel.  Run: python lc_06_compose_chains.py"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from common import get_llm

llm, parser = get_llm(), StrOutputParser()

idea_chain = ChatPromptTemplate.from_template("Give ONE startup idea for the {industry} industry. One sentence.") | llm | parser
pros_chain = ChatPromptTemplate.from_template("Give 2 short pros of this idea: {idea}") | llm | parser
cons_chain = ChatPromptTemplate.from_template("Give 2 short cons of this idea: {idea}") | llm | parser

full = (
    {"idea": idea_chain}                                  # step 1: dict-of-runnables -> output {"idea": "..."}
    | RunnablePassthrough.assign(pros=pros_chain,         # step 2: keeps "idea", ADDS pros + cons
                                 cons=cons_chain)         #         (these two run in parallel)
    | RunnableLambda(lambda d: f"IDEA: {d['idea']}\n\nPROS:\n{d['pros']}\n\nCONS:\n{d['cons']}")  # step 3: plain python
)

print(full.invoke({"industry": "wealth management"}))


"""
Concept. Real pipelines have several steps. LCEL lets you mix sequential steps, parallel branches and plain Python in one chain.

New things in this step

A dict of runnables = run them in parallel
RunnablePassthrough.assign(...) keeps existing keys and adds new ones
RunnableLambda wraps any Python function as a step
Architecture view. idea_chain runs first; pros and cons then run at the same time on its output; a Python function formats the final text.
"""