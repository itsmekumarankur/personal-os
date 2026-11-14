"""EXPERIMENT 1 — the graph engine: state, reducers, routing, parallel branches, loops.
Run: python experiments/exp1_graph.py"""
from _common import table, title

from miniflow import END, Graph, MemoryCheckpointer, Tracer, append, overwrite
from scenario import Shop, build_refund_graph

title("A. one run of the refund workflow, with its trace")
shop = Shop()
app = build_refund_graph(shop).compile(MemoryCheckpointer())
tr = Tracer()
r = app.invoke({"request": "Please refund order ORD-1001, headphones broke"}, thread="a", tracer=tr)
print("status:", r.status, "| nodes executed in order:", r.ran)
print("reply :", r.state["reply"])
print("log   :", r.state["log"])
print("\ntrace:\n" + tr.render())
print("\nNote: the nodes did not call each other. The ENGINE decided what runs next, from the edges and the state.")

title("B. conditional routing: same graph, four inputs, different paths")
rows = []
for req in ["refund ORD-1003 please", "refund ORD-1002 please", "refund ORD-9999 please", "what is your address?"]:
    shop = Shop()
    r = build_refund_graph(shop).compile(MemoryCheckpointer()).invoke({"request": req}, thread="b")
    rows.append((req, " -> ".join(r.ran), r.status, r.state.get("reply") or "(waiting: " + r.interrupt["payload"]["question"] + ")"))
table(rows, ["request", "path", "status", "reply / waiting for"])

title("C. parallel branches and the reducer: WHO WINS when two nodes write the same key?")
for label, red in [("overwrite (default)", overwrite), ("append", append)]:
    g = Graph(reducers={"findings": red})
    g.add_node("plan", lambda s: {})
    g.add_node("search_web", lambda s: {"findings": ["web: fees are 2%"]})
    g.add_node("search_docs", lambda s: {"findings": ["docs: fees are 1.8%"]})
    g.add_node("synthesize", lambda s: {"answer": f"{len(s['findings'])} source(s) used"})
    g.set_entry("plan").add_edge("plan", "search_web").add_edge("plan", "search_docs")
    g.add_edge("search_web", "synthesize").add_edge("search_docs", "synthesize").add_edge("synthesize", END)
    r = g.compile().invoke({})
    print(f"{label:<20} findings={r.state['findings']}  answer={r.state['answer']!r}  ran={r.ran}")
print("""
With overwrite, one source is silently dropped and the answer is built on half the evidence — no error anywhere.
Both branches ran in the same superstep and 'synthesize' ran ONCE after both finished (two edges into one node = a join).
This is why reducers exist, and why 'what happens when two branches write the same key' is a design question, not an implementation detail.""")

title("D. loops need a brake: a refine loop that never converges")
g = Graph(defaults={"n": 0})
g.add_node("draft", lambda s: {"n": s["n"] + 1, "quality": 0.1 * s["n"]})
g.set_entry("draft").add_conditional("draft", lambda s: END if s["quality"] >= 0.5 else "draft")
r = g.compile(max_steps=20).invoke({})
print("converging loop :", r.status, "after", r.state["n"], "drafts")
g2 = Graph(defaults={"n": 0})
g2.add_node("draft", lambda s: {"n": s["n"] + 1, "quality": 0.0})
g2.set_entry("draft").add_conditional("draft", lambda s: END if s["quality"] >= 0.5 else "draft")
r = g2.compile(max_steps=6).invoke({})
print("stuck loop      :", r.status, "after", r.state["n"], "drafts |", r.error)
print("Every cycle in a graph needs a step limit (LangGraph calls it the recursion limit). Same lesson as Project 17's brakes.")
