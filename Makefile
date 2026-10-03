# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — Makefile

PYTHON ?= python3.12
VENV   ?= .venv
ATLAS_PYTHON ?= $(abspath $(VENV))/bin/python
SHELL  := /bin/bash

.DEFAULT_GOAL := help
.PHONY: help setup hooks lint typecheck test validate build verify preflight clean research-example

help:  ## List the available targets
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | sort

setup:  ## Create the development environment from the verified lock
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --require-hashes --no-deps -r requirements-dev.txt

hooks:  ## Check staged source hooks using the same development graph
	PATH="$(abspath $(VENV))/bin:$$PATH" $(VENV)/bin/python -m pre_commit run --all-files --show-diff-on-failure

lint:  ## Lint and check formatting
	$(VENV)/bin/python -m ruff check .
	$(VENV)/bin/python -m ruff format --check .

typecheck:  ## Strict mypy across every source directory
	ATLAS_MYPY="$(abspath $(VENV))/bin/mypy" ./tools/typecheck.sh

test:  ## Python tests at the 100 per cent coverage floor
	@mapfile -t source_dirs < <(find . -name '*.py' \
	  -not -path './tests/*' -not -path '*/.venv/*' \
	  -not -path '*/node_modules/*' -not -path '*/.git/*' \
	  -not -path '*/__pycache__/*' -not -path '*/.mypy_cache/*' \
	  -not -path '*/.pytest-scratch/*' -not -path '*/docs/internal/*' \
	  -printf '%h\n' | sort -u); \
	  test "$${#source_dirs[@]}" -gt 0 || exit 1; \
	  coverage_args=(); \
	  for directory in "$${source_dirs[@]}"; do coverage_args+=("--cov=$$directory"); done; \
	  ATLAS_PYTHON="$(ATLAS_PYTHON)" $(VENV)/bin/python -m pytest tests/ "$${coverage_args[@]}"

validate:  ## Presentation checks, including the map engine tests
	PATH="$(abspath $(VENV))/bin:$$PATH" bash 04_interactive_presentation/validate.sh

build:  ## Verify pinned FFDB and regenerate offline exports and inventory
	ATLAS_PYTHON="$(ATLAS_PYTHON)" node 04_interactive_presentation/scripts/export_taxonomy.cjs
	node 04_interactive_presentation/scripts/evidence_history.cjs --build .
	$(VENV)/bin/python 04_interactive_presentation/scripts/build_datasets.py
	$(VENV)/bin/python metadata/coverage_audit/build_coverage.py
	./metadata/build_inventory.sh

preflight:  ## Reproducibility, docs, secrets and header checks
	$(VENV)/bin/python tools/preflight.py

verify: lint typecheck test validate preflight  ## Everything a change must pass

clean:  ## Remove local caches and scratch space
	rm -rf .mypy_cache .ruff_cache .pytest_cache .pytest-scratch .coverage

research-example:  ## Restore the included comparison without changing source files
	$(VENV)/bin/python -c 'import json; from pathlib import Path; from tools.research_comparison import restore_comparison; p=Path("examples/research"); m=json.loads((p/"comparison-manifest.json").read_text()); print(json.dumps(restore_comparison(Path.cwd(),p/m["comparison_file"],m["profile_sha256"],m["bundle_sha256"]),ensure_ascii=False,indent=2,allow_nan=False))'
