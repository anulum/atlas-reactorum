<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — original research source projection
-->

# Original research field sources

[The original-layer reader](integration.py) merges the base catalogue and
accepted enrichment rounds while retaining their exact source cells, source
URLs and selected or superseded assertions.

[The field projector](projection.py) accepts one reviewed decision for each
originally blank operator, purpose or first-criticality cell in a complete
merged cohort. It returns copies of every original row and retains every
ledger assertion. A selected assertion fills only a blank cell. Held claims,
unknowns, planned events, nonapplicable events, never-critical states and
unresolved composite identities do not supply scalar values. An unreviewed
field refuses the whole projection.

The UTF-8 TSV ledger has exactly these columns, in this order:

```text
stable_id field value selection source_id source_title source_url source_sha256 source_class source_document_date source_capture_date locator scope rights date_precision assertion_basis related_evidence
```

`selection` is `selected`, `held`, `unknown`, `not_applicable`, `never_critical`,
`planned`, `composite` or `unreviewed`. A selected value requires a native
original PDF, HTML response or original facsimile, an anonymous HTTPS source,
its original-body SHA-256, a page or section locator, rights and an explicit
scientific or historical scope. Rendered author-page extracts and discovery
registry JSON may remain held evidence; they cannot supply selected facts.
`related_evidence` retains a JSON array of corroborating or conflicting source
citations, including original reported values and their admissibility. Each
reference binds its source identity, anonymous HTTPS URL and SHA-256; private
file paths and unbound values refuse. An empty cell means no related evidence
was supplied. Document-body retrieval and review occur separately. A formatted digest or a
valid table does not prove authorship, scientific accuracy, current licensing
or permission to redistribute a publisher's document.

First-criticality values retain year, month or day precision. Publication and
capture dates have separate columns. A future criticality relative to a known
capture day remains a held forecast; it cannot be selected as an actual event.
Historical institutions, decommissioning responsibility, relocated facilities
and reactor configurations must have their actual scope recorded. Reading the
ledger does not decide those scientific or institutional questions.

[The projection CLI](build_projection.py) requires `--baseline`, `--assertions`
and `--output`. The baseline JSON contains the complete original `rows` array
with string-valued cells and unique stable identities. The output is a new
schema `1.0.0` JSON snapshot containing every row, every assertion, both input
SHA-256 digests and the actual selected-field count. It never overwrites an
existing destination. Source or output aliases, malformed input, incomplete
field coverage and unreviewed decisions refuse without a purported accepted
output or interpreter diagnostics.

The source input files remain byte-exact. The projection is deterministic and
contains no retrieval requests, publisher document copies or machine-specific
source paths. Its API and CLI tests use the complete production source cohort
and exercise preservation, malformed sources, incomplete review, date
precision, held forecasts, source classes and refusal behaviour. Citation
fixtures qualify those software contracts; they are not scientific acceptance
or an independent review of a facility.


## Presentation consumer

Place a complete reviewed bundle beside the modules in this directory:
`primary-baseline.json`, `primary-fields.tsv` and `primary-projection.json`.
Build the third member with the projection CLI using the first two as inputs.
The [release consumer](primary_integration.py) independently reconstructs the
projection, checks both original input digests and every output cell, and
requires the baseline to equal the actual merged research source rows.
A changed projection, partial bundle, alias, overwritten original value or
unreviewed field refuses. A historical source tree with no bundle retains its
original records. This optional historical path does not qualify a partial
review as ready for publication.

The presentation release CLI emits dataset schema `1.3.0` when primary
decisions are present; historical trees without the bundle retain `1.2.0`.
It applies selected values only to their original blank fields. It retains the older `research_field_origins` and adds every
reviewed disposition as `research_primary_assertions`, including unresolved
claims and explicit no-fill outcomes. The map detail shows scope, assertion
basis, rights, event precision, document and capture dates, original source
digests and related citations. JSON and CSV downloads retain those same
assertions; CSV encodes the assertion arrays as JSON cells. The dataset
inventory counts selected, held and each no-fill outcome separately and hashes
all three producer inputs. Citation formatting and passing software tests do
not decide the scientific admissibility of the real source review.

## Captured research field review

The checked-in bundle contains 358 individually scoped decisions for 172
original records: 275 selected fields and 83 held or explicit no-fill outcomes.
First-criticality precision and historical unit identity are retained. All
original nonempty cells survive unchanged. There are no unreviewed decisions.
[Source attribution and retained rights](RIGHTS.md) and the
[source registry](source_registry.tsv) describe every cited original payload;
no original publisher documents are distributed.

The reproducible command, from the repository root, is:

```sh
python3 05_global_reactor_map/imports/research_reactors/official_source_enrichment/build_projection.py \
  --baseline 05_global_reactor_map/imports/research_reactors/official_source_enrichment/primary-baseline.json \
  --assertions 05_global_reactor_map/imports/research_reactors/official_source_enrichment/primary-fields.tsv \
  --output /path/to/new/primary-projection.json
```

Choose a new output file; the producer refuses overwriting an existing one.
Then rebuild the presentation with its ordinary dataset/release entry points.
The schema carries all 358 decisions into map details and JSON/CSV downloads,
including the 83 outcomes that leave a scalar blank. The baseline, ledger and
projection are SHA-bound inputs in the dataset inventory.

The baseline reproduces the existing five-round merge, including accepted source
metadata. Its six source hashes use repository-relative paths. The original
reactor cells and complete 358-field decision ledger remain unchanged.
