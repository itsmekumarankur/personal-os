"""EV-05  Evaluate the RETRIEVER on its own: Hit@k, Recall@k, Precision@k, MRR.  No LLM.  Run: python ev_05_retrieval_metrics.py"""
from eval_data import GOLDEN, CORPUS, retrieve

# Add questions phrased with different words than the documents (where keyword search struggles)
EXTRA = [
    {"id": "x1", "question": "How many vacation days do I get?",   "relevant_docs": ["d1"]},     # 'vacation' vs 'leave'
    {"id": "x2", "question": "Is remote working allowed?",          "relevant_docs": ["d2"]},     # 'remote working' vs 'work from home'
]
K = 3

def rank_of_first_relevant(retrieved, relevant):
    for i, d in enumerate(retrieved, start=1):
        if d in relevant:
            return i
    return None

hit1 = hitk = rr_sum = recall_sum = prec_sum = 0
items = GOLDEN + EXTRA
print(f"{'id':3} {'retrieved top-3':22} {'relevant':8} first-rank")
for item in items:
    got = retrieve(item["question"], K)
    rel = set(item["relevant_docs"])
    r = rank_of_first_relevant(got, rel)
    hit1 += (r == 1); hitk += (r is not None)
    rr_sum += (1 / r) if r else 0
    found = len(rel & set(got))
    recall_sum += found / len(rel)
    prec_sum += found / K
    print(f"{item['id']:3} {str(got):22} {str(sorted(rel)):8} {r}")

n = len(items)
print(f"\nHit@1       = {hit1 / n:.2f}   (was the right doc ranked first?)")
print(f"Hit@{K}       = {hitk / n:.2f}   (was the right doc anywhere in the top {K}?)")
print(f"Recall@{K}    = {recall_sum / n:.2f}   (fraction of relevant docs found)")
print(f"Precision@{K} = {prec_sum / n:.2f}   (fraction of retrieved docs that were relevant)")
print(f"MRR         = {rr_sum / n:.2f}   (mean of 1/rank: rewards ranking the right doc higher)")

print("""
How to read this:
  * Evaluate retrieval SEPARATELY from generation. If the right chunk never reaches the model, no prompt can fix it.
  * x1 and x2 are paraphrases. Keyword matching cannot connect 'vacation' to 'leave' or 'remote working' to
    'work from home', so x1 ranks the right doc low and x2 misses it entirely. Embeddings (LC-14) or hybrid
    search fix exactly this. Re-run after swapping in the vector retriever and compare MRR.
  * Precision@3 is naturally low here (only 1 relevant doc per question out of 3 slots). Watch the trend, not the absolute.""")


"""
          USER ASKS A QUESTION
       "How many vacation days?"
                   |
                   v
        +----------------------+
        |      RETRIEVER       |
        | Searches documents   |
        | using the question   |
        +----------------------+
                   |
                   v
        +----------------------+
        |   TOP 3 DOCUMENTS    |
        |                      |
        | Rank 1: Document A   |
        | Rank 2: Document B   |
        | Rank 3: Document C   |
        +----------------------+
                   |
                   v
        +----------------------+
        | COMPARE WITH GOLDEN  |
        | SET (correct docs)   |
        |                      |
        | Did we find the      |
        | relevant document?   |
        | How high was it?     |
        +----------------------+
                   |
                   v
        +----------------------+
        | CALCULATE METRICS    |
        | Hit@k                |
        | Recall@k             |
        | Precision@k          |
        | MRR                  |
        +----------------------+
                   |
                   v
        +----------------------+
        | RETRIEVAL SCORECARD  |
        | Is search working    |
        | well enough?         |
        +----------------------+

In simple words: You are learning how to test whether your search system finds the right documents for a question. 
For example:
 - a user asks about “vacation days,” but the policy document says “leave days.” 
 - Your retriever searches for relevant documents and returns the top three results. 
- The program compares those results with the documents that should have been found and calculates scores to measure how well the search is working.


Key takeaway: 
Before testing whether an LLM generates a good answer, test whether it receives the right information in the first place. 
If retrieval fails to find the correct document, even a well-written prompt may not produce the correct answer.
What the four metrics mean
- Hit@k: Did the correct document appear anywhere in the top k results?
- Recall@k: How many of all relevant documents did the search find?
- Precision@k: How many of the retrieved documents were actually relevant?
- MRR (Mean Reciprocal Rank): How highly ranked was the first relevant document? A result at rank 1 scores more than one at rank 3.

The example uses keyword-based retrieval to show why different wording, such as “remote working” versus “work from home,” can cause search failures. Embedding-based or hybrid retrieval can help match documents by meaning rather than relying only on shared words.
"""