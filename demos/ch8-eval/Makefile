# ch8-eval Makefile. Depends on demos/hesheng-core being up.
#
# Cost guardrail:
#   Bedrock Haiku 4.5 calls (10 tickets × ~600 tokens) ~ $0.005
#   Lambda invocations (10–20 calls @ free-tier) ~ $0
#   AgentCore evaluator registration is free; Evaluate calls cost ~$0
#   Total well under $0.10.

PY := python3

.PHONY: up run down verify-down clean

up:
	$(PY) scripts/up.py

run:
	$(PY) scripts/run.py

down:
	$(PY) scripts/down.py

verify-down:
	$(PY) scripts/verify_down.py

clean:
	rm -rf data/ch8-state.json data/predictions.jsonl results/
