<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/research_reactors/README.md
-->

# Research reactor import

This directory contains a legally reusable, evidence-linked **discovery dataset** of nuclear research reactors. It is deliberately separate from the presentation and current global map.

## Release scope

`research_reactors.tsv` contains:

- a global CC0 Wikidata snapshot selected by the class path `instance of / subclass of* = research reactor (Q1438105)`; and
- a small reviewed Canadian regulator supplement under the Open Government Licence – Canada 2.0.

This is not a complete or authoritative replacement for the IAEA Research Reactor Database (RRDB). Wikidata is incomplete and community-edited, and many records lack coordinates, status, operator, power or dates. Unknown values are intentionally blank or `unknown`; values were not guessed from reactor names or unrelated dates.

The IAEA RRDB is catalogued as the primary worldwide verification registry, but it was **not scraped or redistributed**. Its website terms say databases can contain third-party submitted data and do not provide an unambiguous open bulk-redistribution licence. The U.S. NRC sources were reviewed and catalogued but not copied in this release because its public page is site/licensee oriented and needs careful unit-level reconciliation.

## Fields

The required header is:

`stable_id, name, aliases, country, lat, lon, precision, reactor_type, status, purpose, thermal_power_mw, operator, first_criticality, shutdown_date, source_url, source_role, retrieved, license, verification_notes`

The file is tab-separated. Multi-valued text uses `|`. Dates use ISO `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` at the precision actually supplied by the source. Coordinates are WGS84 decimal degrees; `precision=unknown` means that positional accuracy has not been independently verified.

`thermal_power_mw` is populated only when a reusable source clearly states thermal power. Wikidata's generic nominal-power property is not imported because it does not reliably distinguish thermal and electric output. `first_criticality` is not synthesized from inception, commissioning or service-entry dates.

## Rebuild

The fetcher writes an explicit candidate outside this Atlas checkout. An offline
build requires a versioned cache containing the complete SPARQL discovery reply,
every selected core entity and every referenced country/operator/purpose/status
or reactor-class label. Missing entities, changed identities, duplicate query
bindings, malformed consumed claims and non-finite or non-Earth coordinates are
refused before writing. The named SLOWPOKE family item remains excluded because
it describes a design rather than one facility.

From this directory, reproduce the historical Wikidata portion from the complete
captured fixture and combine it with the accepted regulator supplement:

```bash
python3 scripts/fetch_wikidata_research_reactors.py \
  --cache ../../../tests/data/research_reactors_wikidata/cache.json \
  --date 2026-09-26 --out /tmp/research-reactors-wikidata.tsv
python3 scripts/merge_supplements.py /tmp/research-reactors-wikidata.tsv \
  supplements/cnsc_official.tsv --out /tmp/research-reactors-combined.tsv
python3 scripts/validate.py /tmp/research-reactors-combined.tsv
```

The fixture was captured on 2026-09-30: all 166 original query bindings, 161
facility entities and 75 referenced entities are retained. Its original source
values reproduce all 161 historical Wikidata rows; the row date above is an
explicit historical reproduction argument, not the capture date. Without
`--date`, rows use the saved cache's capture date. `SOURCE.json` records raw
request hashes and precisely which unused fields were omitted.

For an explicit online refresh, keep both candidates separate from the accepted
checkout and from each other:

```bash
python3 scripts/fetch_wikidata_research_reactors.py --refresh \
  --cache-out /tmp/research-reactor-refresh/cache.json \
  --out /tmp/research-reactor-refresh/research-reactors.tsv
```

The exact class-path query is followed by numerically ordered batches of at most
50 entities. Requests require anonymous HTTPS and trusted certificates, including
redirect destinations. Each response is limited to 16 MiB, each socket operation
to 30 seconds, and network failures to four attempts with bounded backoff. These
are per-request limits, not a deadline for the entire acquisition. Invalid JSON
and API-error objects are refused immediately. Explicit `--query-url`,
`--entity-url` and `--ca-file` options support trusted HTTPS mirrors; they require
`--refresh`. They are also exercised by the actual TLS conformance tests.

Full source validation and UTF-8 preparation precede file writes. Resolved
Atlas/input/cache/CA destination aliases are refused. Each destination is replaced
atomically and a failed write or close removes its temporary file; the cache and
table are separate atomic files, not a transaction across both files. Inspect a
candidate before integrating it. The live query may drift, and a successful
refresh does not independently establish a reactor's physical or operating state.

Status normalisation matches explicit source labels; `inactive` and `not
operational` cannot match `active` or `operational` as substrings. Conflicting
labels remain `unknown`. Preferred claims take precedence and deprecated claims
are omitted. Unknown snaks remain absent. Source thermal power and first
criticality are not inferred; the Wikidata portion leaves both fields blank.
`source_registry.tsv` records the coverage and reuse decision for every source
reviewed. Apply the licence identified for each source; the cache covers
Wikidata structured data.

## Reuse and attribution

- Wikidata rows are CC0 1.0. Attribution is not legally required, but retaining provenance is strongly recommended.
- CNSC rows are under the Open Government Licence – Canada 2.0. Required attribution: “Contains information licensed under the Open Government Licence – Canada.”
- The combined table does not relicense third-party data. Apply the licence in each row.

No warranty is made. Confirm identity, status, location and technical values against a regulator, operator or the IAEA RRDB before safety, policy or operational use.
