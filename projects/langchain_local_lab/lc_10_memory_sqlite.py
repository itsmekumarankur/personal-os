"""
LC-10  Memory that survives restarts: a custom SQLite history.
Run it TWICE (different messages) and watch it remember across processes:
    python lc_10_memory_sqlite.py "My name is Ankur and I manage a fintech platform."
    python lc_10_memory_sqlite.py "What is my name and what do I manage?"

NOTE: RunnableWithMessageHistory / InMemoryChatMessageHistory are DEPRECATED in LangChain 1.x in favour of
LangGraph persistence (see LG-08 and LG-09). Kept here because most tutorials and legacy code still use
them, and they teach the "history store" idea clearly. Deprecation warnings are silenced below on purpose.
"""
import warnings; warnings.filterwarnings("ignore")
import sqlite3, sys, json
from contextlib import contextmanager
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, message_to_dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from common import get_llm

DB = "chat_memory.db"


@contextmanager
def closing_connection():
    con = sqlite3.connect(DB)
    try:
        yield con
        con.commit()          # commit on success
    finally:
        con.close()


class SQLiteHistory(BaseChatMessageHistory):
    """The ENTIRE contract a memory backend must fulfil: read, add, clear."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        with self._db() as con:
            con.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id TEXT, body TEXT)")

    @staticmethod
    def _db():
        # A fresh short-lived connection per operation: simple and thread-safe.
        return closing_connection()

    @property
    def messages(self) -> list[BaseMessage]:                       # called BEFORE the model runs
        with self._db() as con:
            rows = con.execute("SELECT body FROM messages WHERE session_id=? ORDER BY id", (self.session_id,)).fetchall()
        return messages_from_dict([json.loads(r[0]) for r in rows])

    def add_messages(self, messages: list[BaseMessage]) -> None:   # called AFTER the model runs
        with self._db() as con:
            con.executemany("INSERT INTO messages(session_id, body) VALUES (?,?)",
                            [(self.session_id, json.dumps(message_to_dict(m))) for m in messages])

    def clear(self) -> None:
        with self._db() as con:
            con.execute("DELETE FROM messages WHERE session_id=?", (self.session_id,))


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant."), MessagesPlaceholder("history"), ("human", "{input}"),
])
chat = RunnableWithMessageHistory(prompt | get_llm(), SQLiteHistory, input_messages_key="input", history_messages_key="history")

user_text = sys.argv[1] if len(sys.argv) > 1 else "What do you know about me so far?"
reply = chat.invoke({"input": user_text}, config={"configurable": {"session_id": "ankur"}})
print("You:", user_text)
print("AI :", reply.text)

print("\n--- what is physically stored in", DB, "---")
con = sqlite3.connect(DB)
for sid, body in con.execute("SELECT session_id, body FROM messages ORDER BY id"):
    d = json.loads(body)
    print(f"  {sid} | {d['type']:5} | {str(d['data']['content'])[:70]}")



"""
Concept:
-  Swap the in-memory store for a database by implementing three methods: read messages, add messages, clear.

New things in this step
- BaseChatMessageHistory contract
- message_to_dict / messages_from_dict to serialise messages as JSON
- Run twice from the command line and it remembers across processes

Architecture view: 
    THE DB LAYER: the wrapper calls .messages (SELECT) before the model, then .add_messages (INSERT) after it. 
                  The model never touches the DB.
"""