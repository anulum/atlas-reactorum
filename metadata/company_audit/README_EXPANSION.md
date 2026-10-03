<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/README_EXPANSION.md
-->

# Fusion-company expansion audit

Audit date: **2026-09-27**

`expansion_candidates.tsv` is a conservative discovery layer for organizations absent from the existing 51-row `audited_companies.tsv`. It does not modify or supersede that audit. The expansion contains **18 candidates**: **12 fusion reactor/device developers**, **2 fusion propulsion/device developers**, **1 historical/dormant developer**, **1 speculative non-mainstream nuclear claimant**, **1 public-program operator/technology supplier**, and **1 materials supplier/integrator**.

## Method

1. Treat the existing company and alias columns as a protected identity set.
2. Search current official sites, the Fusion Industry Association 2025 company profiles, the UKAEA 2026 global guide, government and national-laboratory releases, IEA material, the IAEA device survey, and targeted reporting for post-2025 entrants.
3. Normalise names by case-folding and removing punctuation and whitespace; reject any candidate whose name or alias collides with an audited identity.
4. Keep company claims separate from the highest independently supported milestone. A source that proves the existence of a company or design program does not prove plasma performance, fusion yield, gain, electricity production, cost, or schedule.
5. Include suppliers or integrators only when the row explicitly says they are not reactor developers. Keep historical and LENR-like entries in separate identity classes.
6. Require an official URL, at least one independent/source-registry URL, source dates, the fixed audit date, an evidence tier, and a confidence label on every row.

## Evidence interpretation

- **A**: a bounded milestone verified by a government operator or similarly authoritative independent record.
- **B**: independent government, laboratory, scholarly, or institutional support for a bounded milestone.
- **B/C**: a credible research lineage, partnership, device listing, or engineering activity exists, but company-specific reactor performance is not established.
- **C**: identity/program evidence exists; technical performance is primarily self-reported or conceptual.
- **C-H**: historical evidence exists, with no current active program established.
- **D**: claim-led and outside broadly accepted validation; no reproducible independent energy result.

The FIA report is useful for discovery and identity details, but its company profiles contain self-reported survey answers. It is never treated here as independent validation of performance.

## Files and regeneration

- `build_expansion.py`: source-controlled row definitions and deterministic TSV builder.
- `expansion_candidates.tsv`: 18 candidate records with a stable 19-column schema.
- `validate_expansion.py`: schema, completeness, URL syntax, audit-date, duplicate, and collision checks.
- `expansion_validation.json`: machine-readable validation counts.

Run:

```bash
python3 metadata/company_audit/build_expansion.py
python3 metadata/company_audit/validate_expansion.py
```

## Coverage and limitations

- This is a documented expansion, not a claim of global completeness. Private/stealth firms, non-English corporate records, newly incorporated entities, university projects without a separate company, and ventures with no durable public source may be missing.
- The scan identified additional weak leads, including recently discussed Chinese ventures and hybrid concepts, but omitted them where a stable primary identity plus a credible independent/source-registry URL could not both be established by the cutoff.
- Website availability was checked on 2026-09-27. A `403` or bot challenge does not by itself imply inactivity; a reachable website does not prove technical activity.
- Corporate status is based on public evidence, not paid corporate-registry extracts. “Active” means recent public activity was found, not legal good standing or financial health.
- The validator checks URL form and data integrity, not the continuing truth of remote content. Source pages can change after the audit date.
- General Atomics and Oxford Sigma are deliberately retained as non-developer industrial actors. Their facility/component/materials milestones must not be added to private-reactor counts.
- NIF, DIII-D, SUNIST, CMFX, and other public or university machines are not attributed as company-built power demonstrations merely because a company uses their results or personnel.

The producer writes only through its CLI; importing it leaves persisted data untouched. For isolated generation use `python3 metadata/company_audit/build_expansion.py --audited /path/to/audited_companies.tsv --output /path/to/expansion_candidates.tsv`. The original audit is required with its exact schema and valid distinct identities. Public `read_protected` and `check_identities` interfaces check full names and aliases, candidate IDs and row schema before any output write. Bad or missing previous evidence is refused; resolved output paths cannot replace the selected audit. These are discovery candidates, not automatic authoritative registry admissions.

The availability checker runs only through its CLI and checks every distinct source URL once. Use `check_expansion_urls.py --input /path/to/expansion_candidates.tsv --output /path/to/checks.tsv`. Transfers and redirects are restricted to anonymous HTTPS with certificate verification; `--ca-certificate` accepts a trusted institutional certificate bundle. `--timeout` bounds each curl transfer. New snapshots use the current UTC date, or an explicit valid `--checked-on YYYY-MM-DD`. A failed transfer never claims reachability even if response headers arrived; 401/403/406/429 remain recorded access barriers. Availability does not establish source truth or scientific validation. The saved 2026-09-27 snapshot is historical and is not silently refreshed by import.
