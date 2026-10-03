<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/expansion_round3/README.md
-->

# Fusion company and programme expansion — round 3

Audit date: **2026-09-28**

This directory is a non-destructive expansion of the 84-record combined company catalog. It adds organizations and programmes with particular attention to Latin America, Africa and the Middle East, while retaining recent independently identifiable entrants found during the same search. Nothing here has been merged into presentation files.

## Files

- `build.py` is the deterministic source-of-truth builder.
- `candidates.tsv` contains 14 audited candidate records.
- `source_registry.tsv` contains 28 source records with scope limitations.
- `validate.py` checks schemas, source references, dates, URLs, exact baseline counts and normalised name/alias collisions against all three earlier catalogs.
- `validation.json` records counts, distributions, hashes and validation errors.

Run from this directory:

```bash
python3 build.py
python3 validate.py
```

Importing the producer leaves catalogs untouched. For isolated generation use `--audit-root` and `--output-directory`; defaults retain the original directory layout. The public `read_protected` and `check_identities` interfaces require all three original schemas and individual baseline counts, then validate primary names, aliases and candidate IDs before output writes. Missing or damaged evidence is refused with a controlled diagnostic. Resolved output paths cannot replace protected input files, including the previous round’s `candidates.tsv`. Discovery candidates are not automatically admitted to an authoritative registry.

Validation reads persisted outputs without rebuilding them. For local copies use `python3 validate.py --directory /path/to/round3 --audit-root /path/to/company_audit --report /path/to/report.json`. The three baseline files must retain their individual 51/18/15 counts. Declared source IDs must match each candidate’s recorded URL set; shared institutional sources remain valid. Reports cannot overwrite an input, and validation does not establish scientific truth or continuing remote availability.

## Method

The search emphasized Spanish, Portuguese, Arabic/Persian and Chinese institutional material, national nuclear agencies, universities, the IAEA device/outlook corpus and current independent reporting. An entity was included only when it had a stable institutional identity and at least two registered sources. The builder normalizes Unicode names to case-folded alphanumeric strings and rejects overlap across organization names and aliases in:

1. `../audited_companies.tsv` (51 records),
2. `../expansion_candidates.tsv` (18 records), and
3. `../expansion_round2/candidates.tsv` (15 records).

Each row deliberately separates:

- the organization's own claim or programme description;
- the highest milestone supported outside that claim;
- unsupported, ambiguous or prospective assertions.

Evidence tiers are conservative:

- **A/B**: an operating research device or durable public programme is supported by an authoritative independent technical source;
- **B**: legal/programme identity and a material milestone are corroborated, but not reactor-level performance;
- **B/C**: identity, collaboration or design activity is corroborated while hardware performance remains claim-led or pre-hardware;
- **C**: the legal identity is corroborated but delivery or technical milestones are not;
- **D**: speculative, historical-refuted or simulation-only claims without accepted independent performance evidence.

These grades assess the public evidence available for the stated milestone, not the scientific merit of an approach.

## Coverage and counts

The round contains **14 candidates** and **28 registered sources**, bringing the unmerged combined research catalog from **84 to 98 records**.

Geographic labels:

- Latin America and Caribbean: 7 records (Brazil 1, Argentina 2, Mexico 1, Chile 1, Costa Rica 1, regional network 1).
- Middle East and North Africa: 3 public programmes (Arab region/Lebanon 1, Iran 1, Egypt 1), plus 1 UK-based consultancy with explicit MENA focus.
- Other recent or speculative entrants: China 1, France/Switzerland 1, United States 1.

Identity roles include seven national/public/academic operating or research programmes, two regional coordination/planning initiatives, one historical terminated claim, one advisory firm, one current reactor startup, one developer/magnet supplier and one explicitly speculative pre-hardware developer. Public laboratories and coordination networks are never counted as commercial reactor companies.

## Important limitations

- This is a targeted discovery pass, not a complete census of every university plasma group or supplier.
- African fusion-specific R&D is sparse in public sources. The IAEA identifies Egypt and Libya as tokamak hosts, but only Egypt met this pass's primary-plus-independent documentation threshold. No credible sub-Saharan commercial fusion-reactor developer was found. South African nuclear organizations encountered in search were fission/accelerator focused and were excluded.
- Libya's tokamak was not added because a sufficiently current, durable official programme page was not found. Algeria, Morocco and Tunisia have fusion-relevant plasma/materials work, but the reviewed public evidence did not establish a discrete fusion programme identity at the same threshold.
- The Arab Fusion Energy Initiative is a planning and workforce initiative; its proposed medium tokamak has no demonstrated construction milestone.
- Indimaj is a newly incorporated advisory business, not a hardware developer. Companies House supports legal identity only, not client work or technical capability.
- Brazil's permanent National Fusion Laboratory and programme remain planning/implementation propositions around existing research devices; no claim of gain or electricity follows.
- Device operation in Chile, Costa Rica, Iran and Egypt means plasma research operation only. It does not imply energy gain, a D-T power regime or electricity generation.
- Yan Fusion, Firefly Fusion and Kronos Fusion Energy have no independently validated reactor-performance milestone in this audit. Kronos is retained specifically as a clearly labelled speculative, simulation/design-stage claim.
- Websites and programme status can change after the audit date; source dates and access date are retained for reproducibility.

## Reproducibility and non-mutation

The generated TSVs have stable field order, row order and Unix newlines. `validation.json` includes SHA-256 hashes. The producer reads earlier catalogs for baseline and collision checks, and writes to the selected output directory. The validator reads persisted tables without rebuilding them. No integrated catalog, visual asset or presentation file is modified.
