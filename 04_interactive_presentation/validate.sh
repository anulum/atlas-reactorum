#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — 04_interactive_presentation/validate.sh
set -euo pipefail
root_dir="$(cd "$(dirname "$0")" && pwd)"

# Fail closed on a missing checker: a checker that cannot run must never be
# reported as a check that passed.
for tool in node jq python3 grep; do
  command -v "$tool" >/dev/null 2>&1 || { echo "validate.sh: required tool not found: $tool" >&2; exit 1; }
done
echo 'x' | grep -qP 'x' 2>/dev/null || { echo "validate.sh: grep lacks -P (PCRE) support" >&2; exit 1; }
for file in index.html styles.css app.js taxonomy-claim-sources.js SOURCES.tsv data/global_reactors.sample.json data/global_reactors.schema.json data/fusion_companies.sample.json data/fusion_companies.schema.json data/anulum_reactor_repos.json data/anulum_reactor_repos.js data/taxonomy-audit.json data/taxonomy-audit.js; do
  test -s "$root_dir/$file"
done
node --check "$root_dir/app.js"
node --check "$root_dir/taxonomy-claim-sources.js"
node --check "$root_dir/data/taxonomy-expanded.js"
node --check "$root_dir/data/taxonomy-audit.js"
node --check "$root_dir/data/global_reactors.sample.js"
node --check "$root_dir/data/fusion_companies.sample.js"
node --check "$root_dir/data/anulum_reactor_repos.js"
jq empty "$root_dir"/data/*.json
node "$root_dir/scripts/export_taxonomy.cjs" >/dev/null
node --test "$root_dir"/map/tests/*.test.js
node --test --test-concurrency=1 --experimental-test-coverage \
  --test-coverage-include="$root_dir/scripts/export_taxonomy.cjs" \
  --test-coverage-include="$root_dir/scripts/taxonomy_citations.cjs" \
  --test-coverage-include="$root_dir/taxonomy-claim-sources.js" \
  --test-coverage-lines=100 --test-coverage-branches=100 --test-coverage-functions=100 \
  "$root_dir/../tests/taxonomy_citations.test.cjs" \
  "$root_dir/../tests/taxonomy_claim_sources.test.cjs" \
  "$root_dir/../tests/export_taxonomy.test.cjs"
python3 - "$root_dir" <<'PY'
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

root = Path(sys.argv[1]) / "data"
for name in ("global_reactors", "fusion_companies"):
    schema = json.loads((root / f"{name}.schema.json").read_text())
    records = json.loads((root / f"{name}.sample.json").read_text())
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(records))
    if errors:
        raise SystemExit(f"{name}: {len(errors)} schema errors; first: {errors[0].message}")
PY
# Scan for untranslated Slovak UI text. Compared as decoded characters rather
# than bytes: under a locale that cannot be set, a byte-wise regex matches the
# bytes of ordinary typography (em dash, curly quotes) and reports them as
# Slovak. The mandated branding header carries the owner's name, which is
# legitimately diacritic, so those fixed lines are excluded rather than the
# check being weakened.
python3 - "$root_dir" <<'RESIDUE'
import sys
from pathlib import Path

SLOVAK = set("\u00e1\u00e4\u010d\u010f\u00e9\u00ed\u013a\u013e\u0148\u00f3\u00f4\u0155\u0161\u0165\u00fa\u00fd\u017e"
             "\u00c1\u00c4\u010c\u010e\u00c9\u00cd\u0139\u013d\u0147\u00d3\u00d4\u0154\u0160\u0164\u00da\u00dd\u017d")
BRANDING = ("SPDX-License-Identifier", "Commercial license available", "ORCID:",
            "Contact: www.anulum.li", "\u00a9 Concepts", "\u00a9 Code")
root = Path(sys.argv[1])
findings = []
for name in ("index.html", "app.js", "README.md"):
    for number, line in enumerate((root / name).read_text(encoding="utf-8").splitlines(), 1):
        if any(marker in line for marker in BRANDING):
            continue
        hit = SLOVAK.intersection(line)
        if hit:
            findings.append(f"{name}:{number}: {''.join(sorted(hit))}")
if findings:
    print("Potential Slovak UI residue found", file=sys.stderr)
    print(*findings, sep="\n", file=sys.stderr)
    raise SystemExit(1)
RESIDUE
echo "Atlas Reactorum static checks passed."
