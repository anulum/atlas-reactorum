<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/expansion_round2/README.md
-->

# Fusion organization expansion — round 2

Audit date: **2026-09-27**

This directory is a second, additive discovery pass. It does not overwrite `audited_companies.tsv` or the first `expansion_candidates.tsv`. The catalog prioritizes Asian and non-English ecosystems, recent entrants, one Russian state research organization, and clearly separated suppliers or speculative ventures.

## Contents

- `candidates.tsv`: English-language normalised candidate records.
- `source_registry.tsv`: primary, official, government, institutional and independent source metadata, including explicit limitations.
- `build.py`: deterministic generator containing the reviewed records and source registry.
- `validate.py`: validates schemas, mandatory values, URLs, source references, audit date and name/alias collisions against both earlier catalogs.
- `validation.json`: generated counts, hashes and validation result.

Run from the repository root:

```bash
python3 metadata/company_audit/expansion_round2/build.py
python3 metadata/company_audit/expansion_round2/validate.py
```

The producer writes only through its CLI; importing it leaves catalogs untouched. Use `--audit-root` and `--output-directory` for isolated copies. Both earlier catalogs are required with exact producer schemas and valid identities. The public `read_protected` and `check_identities` interfaces refuse missing or damaged previous inputs, duplicate candidate IDs, and collisions involving any candidate name or alias before output writes. Output paths cannot replace protected inputs. These discovery candidates are not automatically admitted to an authoritative registry.

Validation reads persisted outputs without rebuilding. For local copies, use `python3 metadata/company_audit/expansion_round2/validate.py --directory /path/to/round2 --audit-root /path/to/company_audit --report /path/to/report.json`. Source references must match the candidate’s recorded links; names and aliases are checked against both earlier catalogs and every candidate in this round. Reports cannot overwrite source inputs.

## Method

Candidate discovery used Chinese-, Japanese-, Korean-, Spanish- and Russian-language searches as well as English official pages. Inclusion required a distinct organization identity and two source records: an official, primary, parent, investor or institutional source plus an independent, government or specialist-registry source. Where no corporate website was durable, a named investor, university, government or industrial partner release serves as the primary identity source.

Company claims are stored separately from the highest independently supported milestone. “First plasma” means only that a plasma was formed; it does not establish fusion reactions, reactor-relevant temperature, confinement, gain or electricity. A university or public device inherited as technical lineage is not treated as company-built hardware. Financing, incorporation or government-program selection validates organizational activity, not physics performance.

Identity classes deliberately separate:

- reactor/device and project-company developers;
- pre-hardware fusion R&D;
- suppliers and engineering platforms that are not reactor developers;
- state research operators that are not private commercial developers;
- speculative LENR or lattice-energy claims lacking broadly accepted replication.

Evidence labels are conservative: **A/B** indicates strong government or institutional corroboration of the bounded milestone; **B** or **B/C** indicates a real organization, component, device or research lineage but incomplete performance evidence; **C** indicates early-stage identity/program evidence; **D** denotes claim-led non-mainstream nuclear assertions without accepted independent validation.

## Coverage and limitations

- This pass contains **15 organizations** and **30 source records**. Geographic coverage is China 5, Japan 3, South Korea 2, India 3, Spain 1 and Russia 1.
- It is not globally exhaustive. Several newly financed Chinese names were omitted because stable legal identities, durable primary pages or sufficiently independent technical evidence could not yet be resolved.
- Chinese industry and securities reports are useful discovery sources but can repeat company claims; their limitations are recorded in the registry.
- South Korean and Indian entrants are exceptionally early stage. Incorporation and fundraising must not be mistaken for a device milestone.
- Russia/CIS visibility is limited by sanctions, language and sparse current public documentation. TRINITI is included as a state research operator, not a private startup.
- Corporate legal status was not checked against paid registry extracts. “Active” means recent public activity was found.
- Remote pages can change. The validator checks URL syntax and cross-references, not permanent availability or continuing truth.
- No row from either earlier catalog was modified, merged or promoted automatically.
