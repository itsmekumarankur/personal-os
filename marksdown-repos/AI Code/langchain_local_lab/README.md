# LangChain + LangGraph local lab (30 scripts)

1. pip install -r requirements.txt
2. Set ANTHROPIC_API_KEY (Claude) OR run `ollama pull llama3.1` (offline).
3. Start with: python lg_01_hello_graph.py   (needs no key)
4. Then follow the study guide: lc_01 ... lc_15, then lg_01 ... lg_15.

Scripts that need NO model: lg_01, lg_02, lg_03, lg_04, lg_05, lg_14, lg_15.
Run lc_10 and lg_09 twice with different messages to see memory survive restarts.
