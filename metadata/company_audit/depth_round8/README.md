<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — company depth round8
-->

# Company depth round 8

Ten dated profiles document programme fuel, actual prototype evidence where
reported, source dates and remaining verification limits. The review date is
2026-09-30. The 33 entries in [source_registry.tsv](source_registry.tsv) retain
the role of each source: company statement, developer participant survey,
issuer filing, institutional record, author paper or independent notice.
An external URL is not proof of independent authorship or replication.

## Selection and reproducibility

Selection uses the complete 98-row [round-4 matrix](../depth_round4/gap_matrix.tsv),
excluding the 29 distinct identities in rounds 4–7. Eligible rows have a
`fuel_cycle` or `status` gap and are ordered by descending `priority_score`, then
ascending `source_row`. The first ten are NearStar, Longview, Blue Laser Fusion,
EX-Fusion, Helical Fusion, Energy Singularity, nT-Tao, Acceleron, Fuse and ENG8.
Matching uses the exact organisation name and original `AUD-*` record ID.

```bash
python3 metadata/company_audit/depth_round8/review.py
python3 metadata/company_audit/depth_round8/build.py
python3 metadata/company_audit/depth_round8/validate.py
```

The read-only review CLI validates the complete frozen packet, original matrix,
historical schemas, identity ranking, source ownership, source dates, anonymous
HTTPS link syntax and field associations. It fetches nothing. `build.py` stages
all four TSV products after those checks; individual files replace owned regular
outputs atomically. `validate.py` compares every persisted cell with the frozen
reviewed inputs without rebuilding them. A valid report means structural and
editorial consistency, not scientific acceptance or permission to release Atlas.

For isolated generation, pass `--output-directory /absolute/output` to the
builder and `--directory /absolute/output --report /absolute/report.json` to the
validator. `--input-directory`, `--gap-matrix` and `--history-directory` select
complete alternate inputs. Invalid inputs are refused before product writes;
outputs and reports cannot replace source inputs or follow output symlinks.
The input packet is under [reviewed_inputs/](reviewed_inputs/); no downloaded
paper or source-page copy forms part of this layer.

## Reading the evidence

[enrichment_overlays.tsv](enrichment_overlays.tsv) preserves original editorial
paraphrases with date and limitation text. [field_source_bindings.tsv](field_source_bindings.tsv)
binds six substantive fields per profile to the appropriate registered sources.
The compatibility field `enriched_independent_urls` contains external evidence
links, including company-authored papers and participant surveys; its name
must not be interpreted as independent validation.

[gap_review.tsv](gap_review.tsv) accounts for 21 previously missing metadata
fields. It records dated reviews and explicit unknowns; it does **not** report
21 physical evidence gaps closed or ten known prototype fuel cycles. Programme
D-T does not establish a prototype's working isotope, and a plasma pulse,
optical component, resistive electrical load or apparatus report is not a
power-plant result.

The Longview profile preserves the conflict between the IEA direct-drive grouping
and developer/FIA indirect-drive description, and distinguishes historical from
current output projections. The cited IAEA report is *World Fusion Outlook 2024*,
second edition. HH70's working isotope and nT-Tao prototype isotope remain
unknown in the inspected sources. Historical Helical GALOP state is a developer
survey statement. The Acceleron profile uses exact arXiv author version
2606.05333v2: company and institutional authors report D-T experiments and
neutron observations with further analysis pending. That report is neither an
independent replication nor a closed-system energy result; the journal version
was not captured or compared. Reported pressure and temperature extrema are
paired separately, and the three reported campaign durations do not settle the
separate company claim exceeding 100 hours.

NIF achievements belong to LLNL. SEC filing and Companies House registration
establish corporate records, and an NRA meeting index establishes engagement;
none certifies fusion performance. UL's notice denies UL testing/certification
of EnergiCell and is scoped to UL. Fuse's 330-GW resistive-load result is not
fusion power. Sources retain their author affiliations and actual limitations.

## Rights

[source_rights.json](source_rights.json) records the source-specific boundary.
Original Atlas code and editorial metadata use the repository licence; the
referenced works retain their own terms. No third-party PDFs, figures, source
survey tables, private observations or original unaccepted draft are included.
The Fuse article states CC-BY-NC-ND-4.0. The exact MuFusE preprint's arXiv
non-exclusive licence is a grant to arXiv, not an unrestricted Atlas reuse grant.
An unspecified Creative Commons notice or free access is not a verified licence
variant. This layer does not settle the rights of other Atlas datasets.
