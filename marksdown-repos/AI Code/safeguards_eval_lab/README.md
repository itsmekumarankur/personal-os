# Safeguards + Evaluation local lab (31 scripts)

1. pip install -r requirements.txt
2. No-model lessons first:  python sg_01_pii_regex.py   |   python ev_01_golden_set_deterministic.py
3. Model lessons (SG-03/04/05/06, EV-03/04/06/07/09): set ANTHROPIC_API_KEY, or run Ollama (ollama pull llama3.1).
4. Follow the study guide order: sg_01 ... sg_16, then ev_01 ... ev_15.

Scripts that need a model: sg_03, sg_04, sg_05, sg_06, ev_03, ev_04, ev_06, ev_07, ev_09.
eval_data.py is the shared golden set used by every ev_* script.
CI demo:  python ev_14_ci_quality_gate.py B ; echo $?     (exit code 1 = gate failed)
