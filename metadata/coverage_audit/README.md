<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/coverage_audit/README.md
-->

# Coverage audit

`build_coverage.py` turns the integrated atlas into a machine-readable research backlog. It reports counts and missing fields by domain, record kind, source dataset and country, alongside company evidence and identity classifications.

Run from any directory:

```bash
python3 metadata/coverage_audit/build_coverage.py
```

The outputs are `coverage.json` and `COVERAGE.md`. Missing values must not be filled by inference. A zero or low missing count does not prove that a field is current or independently verified; inspect the source role, source date and caveat on the underlying record.
