# ch14-agent Makefile. Depends on demos/hesheng-core being up.
#
# This demo deploys a Lambda alarm-code lookup tool and (best-effort) an
# AgentCore Gateway in front of it, then runs a Strands agent locally
# against 5 prompts to exercise the toolset described in Ch14.
#
# The Lambda + IAM roles are cheap to leave running (~$0/idle), but the
# whole pipeline is idempotent — `make up` is safe to re-run.

PY := python3
AGENTCORE_PROJ := agentcore_project/ch14hesheng

.PHONY: up up-resources up-runtime run down verify-down clean

# `make up` runs in two phases:
#   1. up-resources — Lambda + IAM + Gateway (~30s)
#   2. up-runtime   — agentcore deploy → AgentCore Runtime CDK stack (~3-5 min)
# After both, re-run up.py once more to discover the runtime ARN and grant
# Lambda+Athena permissions to the runtime IAM role.
up: up-resources up-runtime
	$(PY) scripts/up.py

up-resources:
	$(PY) scripts/up.py

up-runtime:
	cd $(AGENTCORE_PROJ) && agentcore deploy --yes --json

run:
	$(PY) scripts/run.py

down:
	$(PY) scripts/down.py

verify-down:
	$(PY) scripts/verify_down.py

clean:
	rm -rf data/ch14-state.json results/
