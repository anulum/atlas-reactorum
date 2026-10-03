<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/VALIDATION.md
-->

# Validation report

Snapshot date: 2026-09-26

Command:

```bash
python3 scripts/validate.py research_reactors.tsv
```

Result: **PASS**

## Coverage summary

| Measure | Count |
|---|---:|
| Records | 172 |
| Open global discovery records | 161 |
| Official national-regulator records | 11 |
| Named countries | 40 |
| Records with coordinates | 106 |
| Records with operator | 35 |
| Records with thermal power | 3 |
| Records with first-criticality date | 0 |
| Records with shutdown date | 36 |

Status counts: `unknown 125`, `shutdown 34`, `decommissioned 7`, `decommissioning 3`, `planned 2`, `operational 1`.

The validator checks the exact 19-column header, stable-ID presence and uniqueness, required provenance, controlled status values, coordinate pairing/ranges, non-negative numeric power, date syntax, retrieval dates, and HTTPS source URLs. A separate scan found no unresolved bare Wikidata Q identifiers in country, reactor type, purpose, operator, or display name and no exact duplicate names.

SHA-256 of `research_reactors.tsv`:

```text
808d2e4a6e060a8fad855632fdcd9049f1d2aecba42039890a4bce148bea63a1
```

## Known limitations

- This release is a legally reusable discovery layer, not a census. The IAEA RRDB has much broader global and historical coverage but was not extracted because open bulk-redistribution rights are unclear.
- Wikidata class membership is community-edited. The importer explicitly excludes the known `SLOWPOKE reactor` family item, but other misclassified concepts may remain.
- Only 106 records have coordinates, and all coordinate precision is conservatively `unknown` pending authoritative verification.
- A missing status is not interpreted as operational. This is why 125 records remain `unknown`.
- Wikidata inception/service dates are not treated as first criticality. No source in this release supplied that concept unambiguously, so the entire field is blank.
- Generic Wikidata nominal power is not treated as thermal power. The three populated thermal values come from the cited CNSC regulator material.
- Current U.S. NRC pages and datasets were reviewed and registered, but no U.S. rows were copied from them because reactor-unit matching remains unfinished.
- The Canadian official supplement intentionally keeps current-facility status `unknown` where the current regulator page lists the facility without explicitly asserting operation.

These limitations are data-quality findings, not validation failures.
