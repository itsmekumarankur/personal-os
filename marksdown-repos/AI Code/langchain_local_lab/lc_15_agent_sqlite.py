"""LC-15  A real agent (create_agent) that queries a SQLite database + remembers the chat.  Run: python lc_15_agent_sqlite.py"""
import sqlite3
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from common import get_llm, ensure_demo_db

DB = ensure_demo_db()          # creates shop.db: products(id,name,price,stock), orders(id,product_id,qty,city)


@tool
def describe_database() -> str:
    """List all tables and their columns. Call this first to learn the schema."""
    con = sqlite3.connect(DB)
    out = []
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({name})")]
        out.append(f"{name}({', '.join(cols)})")
    return "\n".join(out)


@tool
def run_sql(query: str) -> str:
    """Run a READ-ONLY SQL SELECT query on the shop database and return the rows."""
    if not query.strip().lower().startswith("select"):
        return "Error: only SELECT queries are allowed."
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)   # read-only connection = second safety lock
    try:
        return str(con.execute(query).fetchall())
    except Exception as e:
        return f"SQL error: {e}"                              # the model reads this and self-corrects


agent = create_agent(
    get_llm(),
    tools=[describe_database, run_sql],
    system_prompt="You answer questions about the shop database. Check the schema first, then query. Be concise.",
    checkpointer=InMemorySaver(),          # gives the agent memory across calls with the same thread_id
)

cfg = {"configurable": {"thread_id": "demo"}}
for question in ["Which products are out of stock?", "And what is the total quantity ordered from Chennai?"]:
    print("\n" + "=" * 70 + f"\nYOU: {question}")
    for step in agent.stream({"messages": [("user", question)]}, cfg, stream_mode="values"):
        step["messages"][-1].pretty_print()      # watch: AI asks tool -> tool result -> AI answer



"""
In this example, you are learning how to build an AI agent that can answer questions by looking up real data in a database, instead of answering from its own knowledge.
 Imagine you own a shop and ask Claude, “Which products are out of stock?” 
 Claude asks your Python program to show it what information is available in the database, writes a SQL query to find the answer, and uses a tool called run_sql to fetch the results.
 Claude then explains the results to you in simple language. When you ask a second question, the agent can also remember the earlier conversation using InMemorySaver.

                 YOU ASK A QUESTION
                         |
                         v
             +-----------------------+
             |   LangChain Agent     |
             |   (LLM / Claude)      |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | What information      |
             | do I need?             |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | describe_database()   |
             | Learn tables/columns  |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | Agent writes SQL      |
             | SELECT query           |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | run_sql(query)        |
             | Read shop.db safely   |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | SQL results returned  |
             | to the agent          |
             +-----------------------+
                         |
                         v
             +-----------------------+
             | Claude explains       |
             | the results           |
             +-----------------------+
                         |
                         v
                  ANSWER TO YOU




  EXTRA: MEMORY
  --------------
  InMemorySaver remembers conversation history
  for thread_id = "demo", across these two calls.

  SAFETY
  ------
  run_sql() allows only queries beginning with SELECT.
  The database connection is also opened read-only.


                  QUESTION 1:
        "Which products are out of stock?"
                |
                v
        Agent checks database schema
                |
                v
        Agent queries products where stock = 0
                |
                v
        Returns the matching products


                  QUESTION 2:
        "And what is the total quantity ordered from Chennai?"
                |
                v
        Agent remembers the conversation thread
                |
                v
        Checks schema / runs SQL as needed
                |
                v
        Queries orders for Chennai
                |
                v
        Adds the quantities using SQL SUM(qty)
                |
                v
        Returns the total quantity

Concept:
     create_agent packages the loop from LC-13 for you. You give it a model, tools and a system prompt.

New things in this step

- langchain.agents.create_agent
- A read-only SQL tool with two safety locks (SELECT check + read-only connection)
- checkpointer=InMemorySaver() gives follow-up questions memory by thread_id

Architecture view:
     THE DB LAYER: model decides, tool runs the SQL on shop.db, result goes back to the model. 
                Errors are returned as text so the model can fix its query.
"""