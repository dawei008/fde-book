# hesheng-core Makefile — chapter demos depend on the substrate this
# Makefile brings up. Run from demos/hesheng-core/.

PY := python3

.PHONY: up down smoke data clean

up:
	$(PY) scripts/up.py

down:
	$(PY) scripts/down.py

smoke:
	$(PY) scripts/smoke.py

# Just regenerate local CSVs (no AWS calls)
data:
	$(PY) scripts/generate_data.py

# Wipe local generated artifacts (does not touch AWS)
clean:
	rm -rf data/raw data/stack-outputs.json
