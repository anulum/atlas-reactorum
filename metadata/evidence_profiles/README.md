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
does not become an accepted reactor architecture through migration. Every original-profile
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
All seven taxonomy products are prepared before publication; an ordinary I/O failure
restores replaced products. This is process-level rollback, not atomic multi-file
reading during a rebuild or durability across power loss. Serve accepted static
snapshots rather than rebuilding in a live served directory.

The release reconstruction contract declares 26 products. Owning inventory and
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

## Source-bound author assessments

`review_contract.py` admits a separate whole-catalogue input with schema
`atlas-author-review-1.1.0`, defined in `author_review.schema.json`.
Supply the complete assessment file and the trusted original taxonomy hash:

```sh
python metadata/evidence_profiles/review_contract.py --root . --snapshot TAXONOMY_SHA256 --reviews author_reviews.json
```

The public Python interface is `validate_author_reviews(root, snapshot_sha256,
document=None)`. An explicit in-memory document is also accepted. Without a
document or CLI input path, it reads `metadata/evidence_profiles/author_reviews.json`.
The reader validates the original whole profile before and after admission.
It returns the supplied assessment and writes no source or product.

Every original entry appears in order, with an assessment for each of its 21
unchanged values. Field dispositions distinguish editorial identity, source
qualification, required correction, unsupported claims, descriptive context and absent scores.
Claim references must belong to that entry and name their original sources.
Source-qualified fields require source references. Additional sources keep
separate identities, recorded capture custody and catalogue-only rights;
they cannot replace original source metadata or remain unused.

Observations retain exact sections and separate PDF and printed-page locators.
Event and publication dates have explicit year, month or day precision; unknown
dates retain null values and precision. Partial dates are compared as ranges.
Future forecasts remain forecasts and cannot establish attained maturity.
An attained event cannot postdate its reported publication, and publication
cannot postdate recorded acquisition or assessment. Current activity remains
unknown. Each author record declares `review_scope` as
`all-original-fields-and-selected-sources` and `review_basis` as
`author-source-inspection`. Its `complete_entry_review: true` records completion
of those field decisions, including explicit unknown and unsupported outcomes.
The original profile retains its historical false flag; `independent_review`
remains null in both contexts. Completion is not hardware qualification or a
claim that every field is known. Admission checks relationships and metadata;
source inspection owns the scientific interpretation.

An unsupported maturity assessment leaves the original classification intact
without accepting it as attained deployment. The catalogue and detail label
that maturity claim as unqualified; the full field decision states the selected
source limit. A separately supported laboratory stage does not become industrial
deployment. The selected JSON export retains both the original value and its
unsupported disposition.

Malformed JSON, duplicate members, nonfinite numbers, stale original bindings,
invalid locators, unsupported decisions and concurrent baseline changes refuse
through fixed CLI messages. This contract does not edit the original profile,
taxonomy or citation statements. The dedicated tests exercise actual whole
source assessments, normal and optimized CLI calls, owned damaged-schema
copies and concurrent file changes through the public entry points.

`AtlasTaxonomyAuthorReview.read(input, baseline)` supplies the same field,
source, locator and temporal admission in classic scripts and Node. The baseline
must be the complete original profile after its owning producer validation.
The actual page loads `author-review-values.js`, then `author-review-dimensions.js` and
`author-review-revisions.js`, then `taxonomy-author-review.js`.
Node uses the same files; `author-review-contracts.d.ts` declares the runtime
admission methods without changing their checks.

The JavaScript reader accepts parsed metadata. The original Python wire reader
owns duplicate-member and nonfinite-token refusal before browser products are
generated. Public metadata keeps original wording, reference order and unknown
dates. Dedicated native suites cover all four JavaScript modules; direct Python/Node
parity cases and native Chrome cases use the same complete source assessment.

Classification facets retain separate axes, such as entity role, geometry, coolant
and reaction mechanism. Each facet names entry-owned original claims or admitted
observations. Multiple values and axes remain possible; the declared primary
entity role must occur among them. This checks evidence relationships, without
independently accepting the author's interpretation.

Development assessments name a laboratory, pilot or industrial stage, a scoped
evidence object (experiment, simulation or operation), and attained maturity
observations belonging to the same entry. Forecasts, publication-only events and
evidence from another entry cannot establish an attained stage. Pilot and
industrial assessments require operation evidence. Separate assessments preserve
application boundaries instead of assigning a universal score or ranking. An
empty development collection asserts no attained stage; it does not erase
historical operation in the original source record.

Each observation declares its evidence object; an attained assessment must use
the same object as every referenced observation. An observed reaction and an
operating plant consequently remain different evidence objects, even where
both have historical attained dates.

Explicit revisions keep their proposed value separate from the original field.
Each revised field must have a source-qualified `correction-required` assessment;
every such assessment must have exactly one revision. Identity, original source
references, parent relationships, scores and historical review/audit fields
cannot be revised through this path. Duplicate, unchanged or unassessed changes
refuse before any projected row is returned.

`project_author_taxonomy(root, snapshot_sha256, document=None)` and
`AtlasTaxonomyAuthorReview.project(input, baseline)` return the complete ordered
21-field catalogue after whole admission, with only explicit revisions applied.
The original input and baseline stay intact; nested reference arrays are independent
copies. A last-entry failure refuses the entire projection. The CLI uses the same
API and writes only stdout:

```sh
python metadata/evidence_profiles/review_contract.py --root . --snapshot TAXONOMY_SHA256 --reviews author_reviews.json --project
```

A descriptive temperature or mode value supplies no common measured parameter
by itself. The author assessment records this limit without assigning a number,
changing the original context, or treating absent parameters as zero.

`context-only` applies only to the original temperature and mode descriptions.
It preserves those descriptive limits without treating them as normalized
measurements or denying their contextual meaning. Physical assertions cannot
use this disposition to bypass their scientific assessment.

## Reviewed profile products

The maintained `author_reviews.json` supplies the dated author assessment. The
default exporter prepares its versioned original/current profile pair alongside
the five original products. An explicit complete source input can be selected:

```sh
node 04_interactive_presentation/scripts/export_taxonomy.cjs --root . --reviews author_reviews.json
```

`taxonomy-reviewed-profiles.json` and its classic-script counterpart use
`atlas-reviewed-profiles-2.1.0`, defined in `reviewed_profiles.schema.json`. The
schema references the original-profile and author-review contracts through an
explicit local registry; admission retrieves no schema from the network. The
current row shape uses the same 21-field original taxonomy contract. Semantic
admission additionally checks hashes, whole-catalogue order and exact projection;
a shape-valid document alone establishes none of those relationships. They retain the entire original profile, the
separately admitted author review and all 135 current 21-field rows. Three
original input hashes and hashes of the actual original-profile and author-input
bytes identify the source set. Authored metadata licence and publisher-body
rights remain separate. This product contains no original publisher body.

Complete validation and source-byte checks precede publication. Duplicate or
missing selectors, changed source bytes, a different source context, an invalid
last entry and a review input aliased to a product destination refuse. All seven
products share the existing process-level rollback; failure of the final new
script restores the original five outputs and the earlier new JSON. This is
ordinary I/O rollback, not a multi-file power-loss transaction.

`validate_reviewed_profiles(root, snapshot_sha256, reviews_path, document=None)`
checks the actual frozen profile and author input, exact complete original and
current relationships, and source custody after admission. An explicit in-memory
whole product or the maintained generated JSON can be validated:

```sh
python metadata/evidence_profiles/reviewed_profiles.py --root . --snapshot TAXONOMY_SHA256 --reviews author_reviews.json
```

`AtlasTaxonomyReviewedProfiles.read(document, expectedInputs, original)` requires
explicit trusted source bindings and an owning-validated original profile. It
checks the complete input before returning any record. `readProfile(document,
expectedInputs, original, entryId)` returns independent copies of the selected
current taxonomy row, original profile and author review. Selecting an early
entry cannot bypass a damaged final entry. The actual page registers the reader
after the author-review modules; Node uses the same source.

The CLI omitting `--reviews` selects `metadata/evidence_profiles/author_reviews.json`
under the selected repository root. A missing or invalid maintained input refuses
before any product replacement; there is no silent original-only rebuild. Runtime failures
produce the fixed CLI response `Taxonomy export refused.` and a nonzero exit,
without source paths, interpreter diagnostics or partial output. Malformed CLI
arguments receive deliberately authored usage text. All
five original products retain their source context and byte representation. The
release reconstruction contract includes both reviewed products, and checks
source and product bytes in its fresh build. Field assessments and historical
observations preserve their stated limits, original historical flags and
completed author reviews at the declared scope;
reproducibility does not establish independent scientific acceptance.

The CommonJS API `exportTaxonomy(root)` retains its original five-product
snapshot contract for original-source migration and historical consumers.
`exportTaxonomy(root, reviewsFile)` prepares all seven products. The standard
CLI and release reconstruction always select the maintained author input,
and refuse a stale author binding after a source change. A new original
snapshot requires an explicitly reconciled author assessment before a revised
release can be rebuilt.

The maintained page loads the current/original product and its separately emitted,
frozen source bindings. It admits the whole product before catalogue navigation,
then uses current rows in cards, comparison and learning controls. Stable identity
selects the preserved original profile even where the current caption changes.
An absent original taxonomy script retains the explicitly unattributed fallback.

The detail dialog exposes all 21 original/current field decisions, source-scoped
classification facets, scoped attained stages and source observations. Event,
publication and capture dates stay separate; unknowns and declared precision are
shown. Native disclosure controls work by keyboard. Original profile, claims and
historical questions remain available alongside the dated author assessment.

`AtlasTaxonomyReviewedPresentation.render(document, expectedInputs, original,
entryId)` and `exportProfile(document, expectedInputs, original, entryId)` admit
the whole source-bound product before selecting a record. The latter returns
single-entry schema `atlas-entry-reviewed-profile-2.1.0`, the author and review
date in `author_review_context`, the current row, complete
original profile, author assessment, all five source bindings and every original
or additional source supporting those contexts. It contains no publisher body
or independent acceptance. The dialog offers this explicit download alongside
the unchanged original-profile download.

Python provides the same selected current/original contexts through
`read_reviewed_profile(root, snapshot_sha256, reviews_path, entry_id, document=None)`
and the same single-entry export through `export_reviewed_profile(...)` in
`reviewed_entry.py`. Both admit the entire real source-bound product before
selection; returned contexts and source metadata are independent copies. The
normal and optimized CLI selects an explicit stable identity:

```sh
python metadata/evidence_profiles/reviewed_entry.py --root . --snapshot TAXONOMY_SHA256 --reviews author_reviews.json --entry phwr-candu
```

Original/current field support and observations also disclose every supporting
source's exact metadata and capture uncertainty. Recorded UTC acquisition,
publication and event precision remain distinct. Missing source acquisition
stays unknown even where the catalogue or author review has a known date.

Attained deployment describes a named, dated application and remains distinct
from present activity. Historical electricity production and naval propulsion
do not become universal commercial-grid deployment. Regulatory authorization,
reported operation, supplier design identification and forecasts stay separate
observations. A target year passing never turns a forecast into attained maturity.
Source attribution remains explicit: project-participant or manufacturer reports
and an ARIS contributor supplement are not independent IAEA review or complete
entry acceptance.
