"""
eval_data.py - ONE small dataset shared by every evaluation lesson (a real team keeps exactly this: a versioned golden set).

CORPUS      : the "knowledge base" a RAG system searches
GOLDEN      : questions + the expected answer + which document(s) hold it
SYSTEM_A/B  : recorded answers from two imaginary assistants (A mostly good, B mostly bad) so every metric is reproducible
retrieve()  : a deliberately simple keyword retriever (so you can see where retrieval fails)
"""
import re

CORPUS = {
    "d1": "Employees get 24 paid leave days per year. Up to 10 unused days carry forward.",
    "d2": "Employees may work from home 2 days per week with manager approval.",
    "d3": "Travel expenses above Rs. 5,000 need prior approval from the department head.",
    "d4": "The IT helpdesk is available Monday to Friday, 9 AM to 6 PM IST.",
    "d5": "Health insurance covers employees and dependents. Claims must be filed within 30 days.",
}

GOLDEN = [
    {"id": "q1", "question": "How many paid leave days per year?",                  "expected": "24",                "relevant_docs": ["d1"]},
    {"id": "q2", "question": "How many days can I work from home?",                 "expected": "2",                 "relevant_docs": ["d2"]},
    {"id": "q3", "question": "What expense needs department head approval?",        "expected": "above Rs. 5,000",   "relevant_docs": ["d3"]},
    {"id": "q4", "question": "When is the IT helpdesk open?",                       "expected": "Monday to Friday",  "relevant_docs": ["d4"]},
    {"id": "q5", "question": "Within how many days must insurance claims be filed?", "expected": "30",                "relevant_docs": ["d5"]},
    {"id": "q6", "question": "How many unused leave days carry forward?",           "expected": "10",                "relevant_docs": ["d1"]},
]

SYSTEM_A = {   # one wrong answer (q2)
    "q1": "Employees get 24 paid leave days per year.",
    "q2": "You can work from home 3 days per week.",
    "q3": "Travel expenses above Rs. 5,000 need approval from the department head.",
    "q4": "The IT helpdesk is available Monday to Friday, 9 AM to 6 PM IST.",
    "q5": "Insurance claims must be filed within 30 days.",
    "q6": "Up to 10 unused days carry forward.",
}
SYSTEM_B = {   # three wrong answers (q3, q4, q5), terse style
    "q1": "24 days.",
    "q2": "2 days a week, with approval.",
    "q3": "I am not sure.",
    "q4": "The helpdesk is open 24x7.",
    "q5": "Within 60 days.",
    "q6": "10",
}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


STOP = {"the", "a", "an", "is", "are", "of", "to", "i", "can", "do", "how", "many", "what", "when", "per", "in", "does", "my", "me", "get"}


def retrieve(question: str, k: int = 3) -> list[str]:
    """Rank documents by keyword overlap with the question. Returns doc ids, best first."""
    q = {t for t in tokens(question) if t not in STOP}
    # ties are broken arbitrarily (later doc first) so luck in doc ordering cannot inflate the score
    scored = sorted(CORPUS, key=lambda d: (-len(q & set(tokens(CORPUS[d]))), -int(d[1:])))
    return scored[:k]
