# ch15-mcp Makefile. Depends on demos/hesheng-core being up
# (only for region/account discovery — no Athena/S3 traffic in this demo).
#
# This demo proves stateful MCP cross-session persistence:
#   1. `make up`   -> create DynamoDB table fde-book-ch15-ticket-context
#   2. `make run`  -> spin up local MCP server, run two MCP client
#                     sessions with different Mcp-Session-Id, prove the
#                     doc attached in session A is visible in session B
#   3. `make down` -> delete the table, kill any leftover server
#
# Cost: PAY_PER_REQUEST DynamoDB with ~3 R/W ops total = effectively $0.

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
	rm -rf data/ch15-state.json results/
