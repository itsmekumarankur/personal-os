"""SG-04  Topical guardrail: keep the assistant on-topic (deterministic + judge).  Run: python sg_04_topical_guardrail.py"""
from pydantic import BaseModel, Field
from common import get_judge_llm


class TopicVerdict(BaseModel):
    on_topic: bool = Field(description="True if the question is about banking, loans, cards, or this company's products")
    redirect_message: str = Field(description="A short, polite message to send if off-topic, empty string if on-topic")


ALLOWED_TOPICS_HINT = "banking, loans, credit/debit cards, savings accounts, this company's products and support"

classifier = get_judge_llm().with_structured_output(TopicVerdict)


def check_topic(user_question: str) -> TopicVerdict:
    prompt = (
        f"This assistant ONLY answers questions about: {ALLOWED_TOPICS_HINT}. "
        f"Classify this user question and if off-topic, write a short polite redirect.\n\nQuestion: {user_question}"
    )
    return classifier.invoke(prompt)


tests = [
    "What's the interest rate on a 2-year fixed deposit?",
    "Can you write me a Python script to scrape a competitor's website?",
    "My card was declined, what should I check?",
    "What do you think about the upcoming election?",
]

for q in tests:
    v = check_topic(q)
    status = "ON-TOPIC " if v.on_topic else "OFF-TOPIC"
    print(f"[{status}] {q}")
    if not v.on_topic:
        print(f"           -> {v.redirect_message}")

print("\n-> Topical guardrails run BEFORE the main LLM call: if off-topic, skip the real call entirely")
print("   (saves cost) and return the redirect message straight away.")


"""
               USER'S QUESTION
                      |
                      v
       +-----------------------------+
       |    TOPICAL GUARDRAIL        |
       |                             |
       | Check whether the question  |
       | relates to banking, loans,  |
       | cards or company products   |
       +-----------------------------+
                      |
                      v
       +-----------------------------+
       |      LLM CLASSIFIER         |
       |                             |
       | Understand the meaning of   |
       | the user's question         |
       +-----------------------------+
                      |
             +--------+--------+
             |                 |
             v                 v
       +-------------+   +----------------+
       |  ON-TOPIC   |   |   OFF-TOPIC    |
       |             |   |                |
       | FD interest |   | Python scraper |
       | Card issue  |   | Election views |
       +-------------+   +----------------+
             |                 |
             v                 v
       +-------------+   +----------------+
       | Send to the |   | Return polite  |
       | main LLM    |   | redirect message|
       +-------------+   +----------------+
             |                 |
             v                 v
       +-------------+   Stop processing
       | Answer the  |   No main LLM call
       | user        |   (saves cost)
       +-------------+
"""