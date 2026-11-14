"""
common.py - tiny shared helpers so every lesson script stays short.

get_llm()        -> a chat model. Uses Claude if ANTHROPIC_API_KEY is set,
                    otherwise a local Ollama model (free, fully offline).
get_embeddings() -> a LOCAL embedding model (used only by RAG lessons).
ensure_demo_db() -> creates shop.db (SQLite) with sample data for the DB lessons.
"""
import os
import sqlite3


import os
from langchain_anthropic import ChatAnthropic

def get_llm():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY is not set")

    return ChatAnthropic(
        model="claude-sonnet-5-5"
    )


def get_embeddings():
    # Claude has no embedding model, so embeddings always run locally.
    try:
        from langchain_community.embeddings import FastEmbedEmbeddings
        return FastEmbedEmbeddings()          # pip install fastembed
    except Exception:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")   # ollama pull nomic-embed-text


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db")


def ensure_demo_db() -> str:
    """Create a small SQLite database once. Returns its path."""
    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER);
        CREATE TABLE IF NOT EXISTS orders   (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER, city TEXT);
        """
    )
    if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        con.executemany("INSERT INTO products(name,price,stock) VALUES (?,?,?)",
                        [("Keyboard", 1500.0, 40), ("Mouse", 600.0, 120), ("Monitor", 9800.0, 15), ("Webcam", 2300.0, 0)])
        con.executemany("INSERT INTO orders(product_id,qty,city) VALUES (?,?,?)",
                        [(1, 2, "Chennai"), (2, 5, "Mumbai"), (3, 1, "Chennai"), (1, 1, "Delhi"), (3, 2, "Mumbai")])
        con.commit()
    con.close()
    return DB_PATH
