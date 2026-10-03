<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/company_audit/depth_round5/README.md
-->

# Fusion catalog depth audit — round 5

Audit date: **2026-09-28**

Round 5 re-audits the six unresolved high-priority rows from round 4 after excluding its three already enriched identities (Neo Fusion, China Fusion Energy Corporation and Stellarex). It writes exact-name overlays only and does not modify any catalog or presentation file.

## Outputs

- `enrichment_overlays.tsv`: six exact-name, non-destructive enrichment records.
- `source_registry.tsv`: 18 current primary, government, journal, registry and industry sources, with an explicit limitation for each.
- `gap_closure.tsv`: round-4 gap fields, closures, remaining limitations and disposition.
- `build.py`: deterministic builder.
- `validate.py` and `validation.json`: structural and provenance validation.

Run `python3 build.py` and then `python3 validate.py` from this directory. Validation reads the persisted tables; it never rebuilds or repairs them. It checks the previous high-priority identity, source associations and bounded closure fields. For a local data copy, use `python3 validate.py --directory /path/to/round5 --gap-matrix /path/to/round4/gap_matrix.tsv --report /path/to/report.json`. The report cannot replace a source table. These checks verify metadata consistency, not source claims or scientific performance.

The builder accepts `--gap-matrix /path/to/round4/gap_matrix.tsv --output-directory /path/to/round5` for data copies. It checks the complete previous matrix and target IDs/priorities, and derives all closures before writing outputs. Public `read_matrix` and `build_closures` expose the same metadata derivation for local consumers; importing the module does not generate files. Closure means documented fields with retained limitations, not independently validated performance.

## Scope and method

The six targets are Alpha Ring, MIFTI, Electric Fusion Systems, Crossfield Fusion, Astral Systems and Deutelio. Each was matched by its exact normalised catalog name and freshly checked for status, device/project names, fuel cycle, bounded milestone, official URL and source dates.

Company statements establish what a company says and may establish its own current-status notice. They do not independently validate plasma conditions, fusion yield, gain, electricity or economics. Government registries support legal identity/status only. Government and partner announcements support participation, tenancy or procurement; promotional directories may still repeat company performance data. Peer-reviewed papers support the experiments they report but are not automatically independent replication when company authors participate.

An unavailable fact is recorded as an explicit negative finding. It is not inferred from reactor configuration. Host facilities and pulsed-power drivers are distinguished from company-owned devices.

## Material corrections and closures

- **Alpha Ring:** active experimental and educational programme is documented; Alpha-F is linked to proton-boron fusion. Alpha-E fuel and fusion-product interpretation remain unconfirmed. No independent gain or power result.
- **MIFTI:** current official URL is `miftifusion.com`. A 2026 peer-reviewed paper reports Double Eagle deuterium-target experiments and neutron yields above 10^11. Double Eagle and Zebra are host machines; neutron production is not gain.
- **Electric Fusion Systems:** its current official notice says active technical development has ended and the company is winding down. No independently supported operating device or fusion-performance milestone was found.
- **Crossfield Fusion:** the legal entity remains active, but its own 2021 work rejected the Epicyclotron route as unable to scale to net gain. The current programme is hydrogen-isotope separation, so the identity is reclassified as fuel-cycle R&D rather than an active power-reactor developer.
- **Astral Systems:** UKAEA confirms Culham tenancy and SSETB activity. A 2026 government prospectus publishes D-T duration and tritium claims, but without public metrology; those statements are not converted into independently measured performance or power gain.
- **Deutelio:** current evidence identifies active Swiss Deutelio AG (also SA/Ltd.), incorporated in 2024 and moved to Manno in 2025. The public milestone is a Polomac concept paper and legal/company activity, not an operating device. The earlier Croatia/inactive classification is not retained.

## Exact counts and limitations

Round 5 contains **6 overlays**, **18 sources** and **6 gap-closure rows**. All six original round-4 high-priority gap sets receive bounded replacements, but a filled field does not imply that the underlying technical claim was validated. Negative findings remain substantive outcomes: no independent Alpha Ring performance validation, no MIFTI gain, no EFS device result, no independent Crossfield fusion-yield record, no public independent Astral metrology, and no Deutelio hardware result were found.

Web evidence can change or disappear. The registry is an audit trail, not a permanent archive. No integrated catalog or presentation file is changed.
