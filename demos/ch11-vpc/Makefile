# ch11-vpc Makefile. Depends on demos/hesheng-core being up
# (only for region/account discovery — no traffic to the data lake).
#
# What this demo proves: a Bedrock VPC interface endpoint with a
# resource policy is the right perimeter for "this app may only call
# haiku-4.5". The same Lambda, with broad IAM, is forced into the
# allow-list by the network layer.
#
#   make up   -> create VPC + subnet + SG + bedrock-runtime endpoint
#                (with model-restricting policy) + Lambda in subnet
#   make run  -> Lambda calls haiku (allowed) and opus (denied)
#   make down -> tear down everything (Lambda, ENIs, endpoint, VPC)
#
# Cost: VPC free; interface endpoint $0.01/h; Lambda within free tier;
# Bedrock < 100 tokens. Total < $0.05 for a 30-min demo.

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
	rm -rf data/ch11-state.json results/
