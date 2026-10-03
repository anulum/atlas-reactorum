<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — evidence profile contract
-->

# Evidence profiles

Each of the 135 entries has a profile in `profiles.json`, checked against
`profiles.schema.json` version 1.0.0. Its stable identity, original 21-field
taxonomy record, nine citation-bound values, claim IDs, statements, locators
and historical audit remain intact: 599 citations and 148 sources.

Every non-null `parent_id` must identify an entry in the same complete
catalogue. This referential check also applies to the migration API and CLI;
it does not establish that the parent relationship is scientifically accepted.

Four decisions stay separate: the kind of entity, source support for a
statement, classification review and source rights. Entity categories are a
provisional mapping of the original 15 kind labels. An operating mode or device
does not become an accepted reactor architecture through migration. Every
complete-entry flag stays false. Historical classification questions retain
their original date; they are not fresh findings about the current source set.

The inherited inspection records `author-source-inspection`; its author's
identity was not recorded and remains null. An absent independent whole-entry
decision remains null. Existing scoped reviews are not expanded into whole-entry
acceptance. This contract does not certify performance, safety or readiness.

## Read an explicit snapshot

Use the pinned build dependencies, Python 3.12 or later and Node 24.21.0.
Obtain the taxonomy hash from a trusted snapshot manifest and pass it explicitly:

```sh
python metadata/evidence_profiles/validate.py --root . --snapshot TAXONOMY_SHA256
python metadata/evidence_profiles/validate.py --root . --snapshot TAXONOMY_SHA256 --entry pwr
python metadata/evidence_profiles/validate.py --root . --snapshot TAXONOMY_SHA256 --migrate
```

Migration prints the complete validated document to stdout and writes no
source or product. Selection cannot be combined with migration. Public Python
interfaces are `validate_profiles(root, snapshot_sha256)`,
`read_profile(root, snapshot_sha256, entry_id)` and
`migrate_profiles(root, snapshot_sha256)`. Every read validates the whole snapshot,
including its last record. Validation also accepts an explicit in-memory whole
document with the same schema and source binding.

The profile binds the hashes of the taxonomy, original citations and audit TSV.
The original citation reader checks complete order, physical-field text, source
references, capture methods, PDF bounds, printed pages and HTML/XML sections.
Missing audits, changed hashes, duplicate JSON keys, nonfinite numbers and
unsupported decisions refuse before an export writes any product.

## Rebuild and compatibility

```sh
node 04_interactive_presentation/scripts/export_taxonomy.cjs --root .
```

The exporter requires the complete authored profile input and historical audit.
Existing TSV and audit JSON/JS formats, including audit schema 1.3.0, remain
available. It adds `taxonomy-evidence-profiles.json` and its JS counterpart.
The five products are prepared before publication; an ordinary I/O failure
restores replaced products. This is process-level rollback, not atomic multi-file
reading during a rebuild or durability across power loss. Serve accepted static
snapshots rather than rebuilding in a live served directory.

The release reconstruction contract declares 20 products. Owning inventory and
checksum tools account for the assets. Source acquisition is outside this rebuild.

## Parameters and provenance

A known normalized value requires units, conditions, system boundary, conversion
method, original text and references to existing claims. These make interpretation
auditable; they do not independently verify its scientific correctness. Zero is a
value. Missing values use `not_reported`, `not_reviewed`, `not_applicable` or
`disputed`, each with a reason and original text. Migrated temperature descriptions
stay `not_reviewed`; no number is invented from informal catalogue text.

Retained-source capture dates remain null, separate from review dates. Every
source retains `catalogue-only; original not redistributed`: a checksum or locator
does not grant redistribution of a publisher's PDF.

## Browser and download

The detail dialog exposes the profile, dated questions, missing values and exact
citation scopes. Disclosure controls work by keyboard. The selected taxonomy row
must match its full original profile context.

`AtlasTaxonomyEvidenceProfiles.readProfile(document, snapshot, entryId)` requires
an explicit snapshot and identity. `render(document, snapshot, taxonomyRow)`
uses the existing safe citation renderer. `exportProfile(document, snapshot,
entryId)` emits schema `atlas-entry-evidence-1.0.0`, all three input hashes, the
original profile and every supporting source. This explicitly selected export
is not a whole-catalogue input to the validator.

The download states the authored metadata licence and separate source scope.
It includes no original publisher body or new rights grant.
