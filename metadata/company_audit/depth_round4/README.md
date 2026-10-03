<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/depth_round4/README.md
-->

# Fusion catalog depth audit — round 4

Audit date: **2026-09-28**

This directory audits field and evidence completeness across all 98 records in the four existing company/program catalogs. It does not merge, rewrite or supersede those catalogs. Three exact-name overlays enrich the highest-priority incomplete active developers without altering their source rows.

## Outputs

- `gap_matrix.tsv`: one row per catalog identity, with canonical field values, semantic completeness states, gap count and deterministic priority score.
- `summary_by_country.tsv`, `summary_by_identity.tsv`, `summary_by_evidence_tier.tsv`: group counts and core gap counts.
- `enrichment_overlays.tsv`: exact-name patches for Neo Fusion, China Fusion Energy Corporation and Stellarex.
- `overlay_sources.tsv`: nine current primary/government/independent sources, each with a limitation statement.
- `build.py`, `validate.py`, `validation.json`: deterministic generation and validation.

Run:

```bash
python3 build.py
python3 validate.py
```

The builder reads the four original catalogs before writing outputs. For a local data copy, use `python3 build.py --audit-root /path/to/company_audit --output-directory /path/to/round4`. Importing the builder does not generate files. Validation checks persisted outputs separately against the four original audits and every grouped statistic. To check a local output copy, use `python3 validate.py --directory /path/to/round4 --audit-root /path/to/company_audit --report /path/to/report.json`. These data paths cannot select a builder; reports cannot replace source or output inputs. Checks establish metadata consistency, not scientific validation.

## Completeness method

The matrix preserves the source wording for status, identity, approach/configuration, named devices/projects, independently supported milestone, unsupported claims, official URL, independent sources, source dates, country, confidence and evidence tier.

Completeness is assessed as:

- `complete`: populated without a recognised uncertainty marker;
- `partial: review`: populated but explicitly described as unclear, undisclosed, unverified, unstable or non-attributable, or (for the 51-row core audit) supported only by a broad date range rather than record-specific dates;
- `missing: review`: absent, including fuel cycles not explicitly stated in the audited record.

Fuel cycles are extracted only from explicit terms in the audited text: D-T, D-He3, p-B11/H-B11 and D-D. A tokamak, stellarator or other configuration is not automatically assumed to use D-T. This deliberately exposes a large documentation gap rather than manufacturing certainty.

## Priority score

Each non-complete field receives a fixed weight: status 2, identity 2, approach 2, device 2, fuel cycle 1, milestone 3, unsupported claims 2, official URL 2, independent source 3, source date 1, country 2 and confidence 1. Active/currently plausible reactor developers receive 3 additional points. Bands are high at 7+, medium at 4–6 and low below 4.

The activity bonus matches the word `active` or the disclosed current-activity phrase; `inactive` receives no activity bonus.

This is a documentation-priority score, not a technical ranking, investment score or probability of fusion success.

## Aggregate findings

The 98 records comprise 51 core-audit records, 18 first-expansion records, 15 second-round records and 14 third-round records.

- Identity class, unsupported-claim field, independent source, country and confidence are populated for all 98.
- Current status is complete for 90 and partial for 8.
- Approach/configuration is complete for 95 and partial for 3.
- Named devices/projects are complete for 96 and partial for 2.
- Fuel cycle is explicit for 17 and missing from the audited record for 81.
- Independently supported milestone wording is complete for 92 and partial for 6.
- Official URLs exist for 90 and are missing for 8.
- Source dates are record-specific for 47 and broad/partial for 51.
- Nine records are high priority, 63 medium and 26 low under the deterministic score.
- Nine records have no detected gap under this deliberately strict schema.

Country, identity and evidence-tier breakdowns are machine-readable in their respective summary files; each summary independently totals 98.

## Overlay decisions

### Neo Fusion

Government procurement and public-authority records now support the exact Chinese legal entity's role as the BEST construction/procurement vehicle, active ECRH procurement, and planned use of tritium. They do not establish first plasma, D-T operation, energy gain or electricity. No standalone official company site was found, so the overlay leaves its official URL blank.

### China Fusion Energy Corporation

CNNC and Shanghai government sources establish the tier-two CNNC company, shareholders and system-design/technical-validation mandate. A national standards registry confirms participation in magnetic-confinement safety-guideline drafting. No company-operated device or plasma result is attributed. The CNNC parent announcement is retained as the official source rather than presenting it as a standalone company website.

### Stellarex

The current Stellarex Energy site and Ontario/OPG sources establish active Canadian programme development, funded Centre for Fusion Energy participation and an intended prototype. The overlay records current branding, simplified stellarator approach and D-T/tritium programme context. It does not convert partnership funding, an MOU or experiments performed on another institution's device into a Stellarex hardware result.

## Limitations

- The matrix audits the content of the 98 catalog records as written; it is not a fresh full-source re-audit of every record.
- Semantic checks use disclosed deterministic phrases and therefore cannot detect every vague formulation.
- `complete` means the catalog field is sufficiently explicit for this schema, not that the underlying claim is true.
- The three overlays were selected by the score plus active-developer relevance. Other high-priority rows remain visible for later work.
- Government, university and partner announcements can corroborate identity, procurement and collaborations; they do not independently validate plasma temperature, confinement, fusion yield, gain or electricity.
- No presentation or integrated catalog file is modified.
