<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/README.md
-->

# Global Reactor Map

This directory is reserved for an evidence-linked, map-ready registry of known reactor facilities and projects. English is the primary language.

## Scope model

The map must distinguish:

1. **Geolocated facilities** — a named facility, plant, experimental device or publicly announced project with a citable location.
2. **Reactor taxonomy** — a reactor type or concept that may have zero, one or many physical installations.
3. **Claims and proposals** — commercial, speculative or historical claims whose existence does not establish technical performance.

No single public registry covers every reactor domain. Nuclear power and research reactors have comparatively strong international registries; fusion-device data are fragmented; industrial chemical and biochemical reactors are numerous, often private, and cannot be exhaustively enumerated from public information. Completeness must therefore be reported separately for each domain and source.

## Planned authoritative inputs

- IAEA PRIS — nuclear power reactors.
- IAEA Research Reactor Database — research reactors.
- IAEA fusion device and fusion-energy information resources.
- National regulators, laboratories and facility operators for coordinates and current status.
- Public environmental permits and pollutant-release registries for selected industrial chemical/biochemical facilities, subject to their licences and coverage limitations.
- Crossref, OpenAlex, OSTI, NASA NTRS and publisher records for experimental and emerging systems.
- Project/operator disclosures only when explicitly labelled as self-reported.

Every record must include its source, retrieval date, geographic precision, evidence maturity and verification status. Conflicting values must be retained as source-specific assertions rather than silently overwritten.

## Files

- `reactor-map.schema.json` — validation schema for facility/project records.
- `sources.tsv` — planned source registry, including licence and coverage notes.
- `data/` — normalised records and source snapshots once ingestion begins.

The interactive presentation in `../04_interactive_presentation/` will consume a compact export generated from this registry; it should not become the canonical data store.

## Retained dataset scope (checked 2026-10-02)

The checked-in base contains a 195-plant nuclear subset of the CC BY 4.0 WRI Global Power Plant Database, pinned to a repository commit, plus a generated GeoJSON view. It is plant-level discovery data: reactor-unit identities and current/historic status require PRIS/national-regulator verification.

Four additional discovery layers are stored under `imports/`:

- 1,823 power-reactor units adapted from GEM GNPT August 2026.
- 172 research-reactor records from Wikidata CC0 and an openly licensed CNSC
  supplement, with 54 official-source overlays across five passes.
- 174 pinned IAEA FFDB catalogue records, including 137 publisher map points.
  The default presentation build validates the complete visible capture and
  both cached products. Source configuration/status cells remain dated source
  observations. Historical FusionBenchmark rows and overlays are retained
  separately under the explicit `--fusion-source historical` option; their
  unresolved rights are not inherited by the new source.
- 11,086 bounded industrial-site or process-project records from EEA, U.S. EPA,
  Canada NPRI, Australia NPI, UK PRTR, SwissPRTR, UK REPD, ADEME, Brazil EPE,
  Swiss SFOE biogas and Italian ARPAE bioenergy sources.

Their directories contain methodology, source registries, builders and
validators. IAEA PRIS and RRDB remain comparison registries. The dated FFDB
layer has its own [reuse and attribution boundary](imports/fusion/ffdb/RIGHTS.md).

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md),
[COMPLETENESS.md](COMPLETENESS.md), [VALIDATION.md](VALIDATION.md) and the
[dated Fusion rights observation](imports/fusion/source_rights.json). The
following commands rebuild only the WRI plant layer; they do not reproduce
the whole integrated map or resolve other sources' rights:

```bash
python3 scripts/fetch_wri_gppd.py --date 2026-09-26
python3 scripts/export_geojson.py
python3 scripts/validate.py
```
