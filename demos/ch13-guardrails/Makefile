# ch13-guardrails Makefile. Depends on demos/hesheng-core being up
# (only for region/account discovery).
#
# What this demo proves: Bedrock Guardrails sits at the model layer
# and is decoupled from agent IAM. Same model, same prompt — guardrail
# decides what flows in/out via PII anonymization, denied topic, prompt
# attack, and (when wired in) contextual grounding.
#
#   make up   -> create guardrail + publish version 1
#   make run  -> 4 Converse calls: PII / denied topic / prompt attack /
#                normal ticket
#   make down -> delete guardrail (versions go with it)
#
# Cost: Guardrail is per-text-unit (1k chars per unit) + Bedrock haiku.
# 4 short calls < $0.01 total for a 30-min demo.

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
	rm -rf data/ch13-state.json results/
