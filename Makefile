# Plain equivalents (when make is absent) are documented in README.md.
PY ?= python3
TODAY ?= 2026-10-17

.PHONY: setup lint test eval eval-regression demo policy secretscan secretscan-hash report generate

setup:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	$(PY) -m mypy

test:
	$(PY) -m pytest

eval:
	$(PY) -m governance_board eval

# This target is supposed to exit non-zero. CI asserts that failure.
eval-regression:
	$(PY) -m governance_board eval-regression

policy:
	$(PY) -m governance_board policy --inventory inventory/fleet.yaml --prompts prompts/registry.yaml --today $(TODAY)

secretscan:
	$(PY) -m governance_board secretscan

secretscan-hash:
	$(PY) -c "import hashlib, pathlib; p=pathlib.Path('src/governance_board/secretscan.py'); d=hashlib.sha256(p.read_bytes()).hexdigest(); text=pathlib.Path('docs/PROVENANCE.md').read_text(encoding='utf-8'); needle='sha256: '+d; raise SystemExit(0 if needle in text else 'sha256 mismatch ' + d)"

generate:
	$(PY) -m governance_board generate-traces --inventory inventory/fleet.yaml --profile traces/generation.yaml --out traces/fleet.jsonl

report:
	$(PY) -m governance_board report --inventory inventory/fleet.yaml --traces traces/fleet.jsonl --out docs/example-board --generated-on $(TODAY) --source simulated-generator

demo:
	$(PY) -m governance_board demo --out demo-out --today $(TODAY)
