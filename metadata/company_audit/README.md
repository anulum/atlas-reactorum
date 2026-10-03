<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/README.md
-->

# Fusion-company and project audit

This file audits the 51 names in the discovery candidate register. It distinguishes reactor/device developers from suppliers, engineering consortia, neutron/isotope businesses, historical programs and speculative non-mainstream claims.

Each row separates:

- the company claim;
- the highest independently supported bounded milestone found in the review;
- claims that remain unsupported or ambiguous;
- an evidence tier and audit confidence;
- official and independent source links.

Evidence tiers are intentionally conservative: `B` means a bounded milestone has government or peer-reviewed support, not that commercial fusion power is demonstrated; `C` is public-program/company evidence without independent validation of the claimed performance; `C-H` is historical; and `D` is claim-led without broadly accepted independent validation.

Run `python3 build_audit.py` to regenerate the TSV from the frozen candidate register, then `python3 validate.py`. This is a structured screening audit, not investment advice, certification, or a substitute for technical due diligence. Company status and schedules are time-sensitive.

The producer reads and writes only through its CLI; importing it leaves persisted data untouched. For isolated generation use `build_audit.py --input /path/to/fusion_companies_candidates.tsv --output-directory /path/to/audit`. Public `read_candidates`, `build_rows` and `summarize` interfaces preserve the original review overrides and claim limitations. Exact discovery schema, intact rows, distinct nonblank primary identities and required claim context are checked before output writes. Resolved output paths cannot replace the discovery input. The review date and historical screening findings are not silently refreshed from current company claims.

Three expansion catalogues bring the integrated screening register to 98
companies and programmes. Five later depth passes supply 39 exact-name overlays.
The [latest ten-profile review](depth_round8/README.md) provides its frozen
review inputs, native build and validation commands, 33-source citation registry,
field associations and rights boundary. The source register's external-citation
field includes company-authored material; a citation does not establish
independent replication or resolve unknown prototype fuel.
