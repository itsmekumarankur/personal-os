"""EXPERIMENT 4 — streaming over real HTTP: TTFT, cancel-on-disconnect, resume, heartbeat.
Starts the FastAPI server in a thread (real sockets, real time; the fake model's clock is compressed 10x).
Run:  python experiments/exp4_http.py"""
import socket
import threading
import time

import httpx
import uvicorn
from _common import table

import server
from sse_client import data_of, stream_chat


def start(**kw):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    srv = uvicorn.Server(uvicorn.Config(server.create_app(**kw), host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(100):
        try:
            httpx.get(f"http://127.0.0.1:{port}/health")
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    return srv, f"http://127.0.0.1:{port}"


def first_text_time(url, msg):
    t_first = t_done = None
    for t, ev in stream_chat(url + "/chat", {"message": msg}):
        if ev["event"] == "content_block_delta" and t_first is None:
            t_first = t
        if ev["event"] == "done":
            t_done = t
            d = data_of(ev)
    return t_first, t_done, d


if __name__ == "__main__":
    print("== 1. TTFT over real HTTP: cold cache, then warm cache ==")
    srv, url = start(time_scale=0.1)
    rows = []
    for i in range(3):
        tf, td, d = first_text_time(url, "explain streaming in 40 words")
        rows.append((i + 1, f"{tf * 1000:.0f} ms", f"{td * 1000:.0f} ms", d["usage"]["cache_read_input_tokens"], f"${d['cost_usd']:.4f}"))
    table(rows, ["request", "first text", "complete", "cache read", "cost"])
    print("(times are the model's virtual seconds x0.1; the first request pays to write the 4k-token prefix and is slower)\n")

    print("== 2. Client closes the tab after 6 events: does the server stop paying? ==")
    n_before = httpx.get(url + "/metrics").json()["cancelled"]
    got = list(stream_chat(url + "/chat", {"message": "explain streaming in 600 words"}, stop_after=6))
    time.sleep(0.5)
    mt = httpx.get(url + "/metrics").json()
    sid = data_of(got[0][1])["stream_id"]
    print(f"events received before leaving: {len(got)}; server cancelled counter: {n_before} -> {mt['cancelled']}")
    buf = srv.config.app.state.buffers[sid]
    print(f"events the server had produced when it stopped: {len(buf.events)} (a 600-word answer is ~300 events). The rest were never generated, so never billed.\n")
    srv.should_exit = True

    print("== 3. Policy 'keep' + reconnect with Last-Event-ID ==")
    srv, url = start(time_scale=0.1, on_disconnect="keep")
    got = list(stream_chat(url + "/chat", {"message": "explain streaming in 200 words"}, stop_after=8))
    last_id = got[-1][1]["id"]
    sid = data_of(got[0][1])["stream_id"]
    time.sleep(0.2)
    with httpx.Client(timeout=30) as c, c.stream("GET", f"{url}/chat/{sid}", headers={"Last-Event-ID": last_id}) as r:
        from sse_client import parse_sse
        rest = list(parse_sse(r.iter_lines()))
    ids = [int(e["id"].split(":")[1]) for _, e in got] + [int(e["id"].split(":")[1]) for e in rest]
    print(f"first connection: {len(got)} events (last id {last_id}); reconnect: {len(rest)} events; last event: {rest[-1]['event']}")
    print("ids contiguous with no duplicates:", ids == list(range(ids[0], ids[0] + len(ids))))
    print("TRADE-OFF: 'keep' lets the user resume but you pay for tokens even if they never come back. 'cancel' saves money but a flaky mobile network loses the answer.\n")
    srv.should_exit = True

    print("== 4. Heartbeats: ': ping' comment lines while the model is silent ==")
    srv, url = start(time_scale=0.3, heartbeat_s=0.05)
    pings = 0
    with httpx.Client(timeout=30) as c, c.stream("POST", url + "/chat", json={"message": "explain streaming in 20 words"}) as r:
        for line in r.iter_lines():
            pings += line.startswith(": ping")
    print(f"heartbeat lines seen during the long prefill: {pings}  (proxies drop connections that look idle; comments keep it alive and clients ignore them)")
    srv.should_exit = True
