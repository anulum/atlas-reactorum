<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/discovery_audit/methodology.md
-->

# Cross-domain reactor-library discovery audit

Audit date: **2026-09-26**. Scope: nuclear fission, plasma fusion, chemical and biochemical reactors, hybrid systems, emerging concepts, LENR/solid-state fusion, and speculative reactor technologies. This is a bibliographic gap audit, not a validation or engineering-design review. Exhaustive completeness cannot be guaranteed: the literature, company landscape, preprint record, and access status change continuously, and some databases expose only partial metadata or require registration.

## Procedure

1. Read the three existing `sources.tsv` catalogs and compared their category/title coverage. Completed catalogs were not modified.
2. Built a reactor-family matrix and marked missing families, missing reactor-level engineering topics, missing official datasets, and sections represented only by old or commercial literature.
3. Searched authoritative agencies and repositories first: IAEA publications, ARIS, PRIS, INIS, IAEA Nuclear Data Services, OECD NEA, US NRC, DOE/OSTI, NASA NTRS, US CSB, EUROfusion, UKAEA, and DOE Fusion Energy Sciences.
4. Queried broad scholarly indexes for 2020-2026 reviews and OA locations, then followed backward-reference leads from major reviews for cornerstone works.
5. Added speculative technologies only when there was an identifiable primary source, review, patent/publication trail, or registry entry. Their evidence notes distinguish an operating experiment, a modeled concept, a company claim, and independently reproduced energy production.
6. Normalised DOI values to lowercase for comparison, stripped `https://doi.org/`, query strings, fragments, and trailing slashes from URLs for deduplication. Rows with the same normalised DOI were merged. When no DOI existed, normalised canonical URLs were compared.

## Queries and endpoints

The search phrases were deliberately broad and then narrowed by reactor family. Representative forms:

- Crossref REST, `https://api.crossref.org/works`: `query.title=nuclear reactor review`, date filter `2020-01-01` to `2026-12-31`; follow-up title queries for maritime reactors, fusion heat conversion, rotating packed beds, membrane bioreactors, and hybrid systems.
- OpenAlex Works, `https://api.openalex.org/works`: searches for `chemical reactor review`, `low energy nuclear reactions`, `fusion reactor`, and individual missing families, with 2020-2026 and `is_oa:true` where appropriate. OA URLs were treated as discovery leads and checked against the publisher/repository identity.
- DOAJ API, `https://doaj.org/api/search/articles`: title searches for `fusion reactor`, `photobioreactor`, `plasma reactor`, `electrochemical reactor`, and `hybrid energy system`.
- OSTI.GOV: web and API searches for `molten salt reactor`, `fusion pilot plant`, `microreactor`, `reactor transient`, and `slurry reactor`. The API request timed out during this run, so OSTI candidates were confirmed through DOI/Crossref and OSTI public landing pages instead.
- IAEA INIS, `https://inis.iaea.org/search/`: English title/keyword combinations for individual reactor families and official technical-document leads. INIS is included as a candidate discovery resource because its interface did not provide a stable unauthenticated bulk-export API in this run.
- IAEA ARIS/PRIS/FUSDIS and Nuclear Data Services: direct inspection of database scope, publications, and downloadable catalogues.
- NASA NTRS API and site search: `lattice confinement fusion`, `fusion fast fission`, and `space reactor`; API results included NTRS records `20250000180`, `20240013692`, and `20240014095`.
- arXiv export/API and site search: `fusion reactor`, `magnetic mirror`, `aneutronic fusion`, `reactor scale-up`, and `LENR`. The export endpoint returned HTTP 406 in this environment; canonical abstract pages found through the web index were used. Preprints are explicitly labelled and never treated as peer review.
- Backward/reference-chain leads: IAEA World Survey of Fusion Devices; FIA Global Fusion Industry reports; the 2023 commercial-fusion review; the 2024-2026 reactor-family reviews in `candidates.tsv`; and existing library reviews.

## Company/project sweep

The separate `fusion_companies_candidates.tsv` is a registry candidate list, not an investment or technical endorsement. It was cross-checked against the 2025 FIA survey, IAEA World Survey/FUSDIS, DOE Milestone Program announcements, the 2026 UKAEA global fusion guide, UK government sector directory, company sites, and available independent articles or scholarly publications. FIA membership and survey responses are self-selected; company milestones remain self-reported unless the evidence note says otherwise. `active_status` reflects public evidence found as of the audit date and may lag private shutdowns, stealth launches, acquisitions, or renamings.

## Evidence and access conventions

- `public official`: government or intergovernmental source.
- `open access`: full scholarly work legally readable without subscription.
- `publisher access` / `paywalled`: metadata or abstract only; no bypass attempted.
- `preprint`: public manuscript without peer-review inference.
- `speculative`: proposed mechanism/device without demonstrated reactor-scale net energy.
- Company claims, schedules, funding, and performance are recorded as claims unless independently confirmed.

## Limitations

- No large files were downloaded; this audit is metadata-only.
- Bibliographic APIs differ in DOI, OA, author, and date quality. Crossref and OpenAlex can inherit publisher errors; DOAJ covers only indexed OA journals.
- Conference presentations and corporate pages may change URLs or disappear.
- INIS, ICSBEP, and IRPhE have access/export constraints; inclusion here does not imply every record is freely downloadable.
- Chinese, Russian, Japanese, Korean, and other non-English company/project sources are underrepresented because English was primary.
- Patents were sampled through company and registry references, not exhaustively searched by family or assignee.
- A complete global company census is not possible: stealth companies are discoverable only after public announcement, and corporate status changes faster than annual surveys.
