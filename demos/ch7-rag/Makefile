# ch7-rag Makefile. Depends on demos/hesheng-core being up.
#
# IMPORTANT: OpenSearch Serverless billing is per-OCU-hour (~$0.24/hour idle).
# `make up` -> `make run` -> `make down` should be a single uninterrupted flow.

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
	rm -rf data/ch7-state.json results/
