"""LC-09  Let LangChain manage history per session_id.  Run: python lc_09_memory_runnable_history.py

NOTE: RunnableWithMessageHistory / InMemoryChatMessageHistory are DEPRECATED in LangChain 1.x in favour of
LangGraph persistence (see LG-08 and LG-09). Kept here because most tutorials and legacy code still use
them, and they teach the "history store" idea clearly. Deprecation warnings are silenced below on purpose.
"""
import warnings; warnings.filterwarnings("ignore")
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from common import get_llm

store: dict[str, InMemoryChatMessageHistory] = {}      # session_id -> its own history (this is the "DB")


def get_history(session_id: str) -> InMemoryChatMessageHistory:
    return store.setdefault(session_id, InMemoryChatMessageHistory())


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise assistant."),
    MessagesPlaceholder("history"),            # <- past messages are injected here
    ("human", "{input}"),
])

chat = RunnableWithMessageHistory(
    prompt | get_llm(),
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

def ask(session: str, text: str):
    out = chat.invoke({"input": text}, config={"configurable": {"session_id": session}})
    print(f"[{session}] You: {text}\n[{session}] AI : {out.text}\n")

ask("alice", "Hi, I'm Alice and I love chess.")
ask("bob",   "Hi, I'm Bob and I love cricket.")
ask("alice", "What hobby did I tell you about?")      # alice's memory only
ask("bob",   "What hobby did I tell you about?")      # bob's memory only

print("messages stored -> alice:", len(store["alice"].messages), "| bob:", len(store["bob"].messages))


"""
Concept:
 A wrapper loads the right history by session_id before each call and saves the new messages after it.

New things in this step

- MessagesPlaceholder('history') inside the prompt
- RunnableWithMessageHistory + a get_history(session_id) function
- Two sessions never see each other's messages
Architecture view. Data flow: session_id -> your store -> history injected into prompt -> model -> new messages written back to the store.
"""