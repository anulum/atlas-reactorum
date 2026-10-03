<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/COMPLETENESS.md
-->

# Completeness and limitations

## What this release is

The retained local atlas combines bounded discovery layers. Counts below were
checked against the frozen source tables and integrated presentation bundle on
2026-10-02; that check does not establish present operation or approve source
redistribution. The older 195-plant WRI base is pinned to Git commit
`7a91cfbb2a4e272597acbc00506d61fc1ec73b3d` and identifies its CC BY 4.0 source.
Its licensing must not be extended to other integrated sources. The
[component rights map](../04_interactive_presentation/data/source_rights.json)
records each facility layer and overlay separately. The optional historical
FusionBenchmark selection retains six compilation fields per identity; its
[rights record](imports/fusion/source_rights.json) distinguishes that bounded
selection from excluded enrichment cells and current live copying restrictions.

The integrated presentation contains 13,459 facility/site/project records.
Layers can overlap and record boundaries differ, so this is not a count of
unique physical reactors worldwide. The map does not replace IAEA PRIS, RRDB,
FusDIS, national regulators or operator records.

## Domain assessment

- **Nuclear power:** `imports/power_units/` now contains 1,823 unit-level fission/unspecified records from GEM GNPT August 2026 under CC BY 4.0, spanning all tracker statuses. The older 195-record WRI layer remains separately identified as plant-level discovery data. PRIS is the authoritative comparison source but was not scraped or redistributed because open bulk-reuse rights were not established. GEM values still require regulator/operator reconciliation.
- **Research reactors:** `imports/research_reactors/` contains 172 discovery
  records across 40 known countries. The retained base has 106 coordinate
  pairs; the integrated presentation has 107 after source overlays and
  supplemental context are applied. Five passes provide 54 overlays for 54
  distinct records. Operator, purpose and first-criticality fields remain
  empty in 96, 117 and 145 integrated records respectively. RRDB is the
  authoritative comparison registry; its content was not bulk-redistributed.
  Discovery values still require regulator/operator reconciliation.
- **Default fusion catalogue:** `imports/fusion/ffdb/` reproduces 174 source
  identities from a complete visible IAEA FFDB data selection dated 2026-10-02.
  Its 137 map points preserve raw precision and separate displayed aliases;
  facility/device granularity is unspecified. Six supplemental fusion context
  records remain separate. Historical overlays, operation dates and approximate
  supplemental coordinates do not fill missing FFDB fields. The source-specific
  reuse statement requires IAEA acknowledgement and no implied endorsement;
  its scope does not establish physical verification or grant rights to every
  component of the captured viewer container. The labelled selection has a
  distinct artifact digest linked to the privately retained original response;
  every raw/display cell is retained without redistributing that renderer.
- **Historical fusion selection:** the optional historical route retains 146 base
  identities and six compilation fields: ID, name, country, type, operator and
  operating status. Eleven official-source additions and 40 overlay rows across
  three passes remain separate source contributions; the overlays target 34
  devices (32 base records and two additions). The public base omits 51 separately
  enriched Wikidata values and 14 coordinate-precision notes. It does not claim
  independent device location or present operation. The explicit
  public route can accept `--historical-bundle /path/to/public-snapshot`,
  verifying and capturing all nine public input files before output. Its
  inventory records all nine hashes; this does not restore omitted fields.
  The distinct
  `--fusion-source historical-full --historical-bundle /path/to/bundle` route
  validates all nine original frozen inputs, including exact sizes, hashes,
  table schemas and counts, before output. It permits offline reproduction from
  a separately retained complete bundle and does not download or reconstruct
  that bundle. The six-field compilation permission does not grant the other
  contributions or permit a new live collection under current copying
  restrictions. FusDIS remains a comparison registry and was not bulk-redistributed.
- **Advanced projects:** some publicly announced projects may appear when classified under a selected Wikidata class. This release does not claim a complete commercial-project pipeline. ARIS is registered as a follow-up source; GEM supplies the separately identified power-unit layer; operator announcements must be labelled self-reported until independently verified.
- **Historic/shutdown:** included where the open source asserts status or dissolution; missing status maps to `unknown`, not `operational`.

## Chemical and biochemical facility boundary

“Chemical reactor” is equipment inside a vast number of private industrial sites, not a globally registered facility class. The bounded layer contains 6,150 EEA chemical or food-and-beverage sites reported for 2024, 400 U.S. EPA AgSTAR anaerobic-digester projects, 908 Canadian NPRI sites, 868 Australian NPI sites, 722 UK PRTR sites, 93 SwissPRTR sites, 362 UK REPD anaerobic-digestion planning-project/site records, 31 ADEME hydrogen-production sites, 589 Brazilian EPE biofuel-layer records 542 U.S. EPA LMOP landfill-gas energy projects, 153 Swiss SFOE biogas plants and 268 Italian ARPAE biogas-classified bioenergy records. The rows do not infer a reactor count or design; only AgSTAR retains an explicitly published digester type. Planning, registry and programme records are not guaranteed to be unique physical plants, and their points do not establish unpublished process pathways or vessel designs. This is a bounded discovery layer, not global chemical-reactor completeness. Further work requires jurisdiction-specific registers, licences, thresholds and facility-boundary reconciliation.

## Known biases and safe use

Wikidata has language, notability and contributor-density bias; duplicate facilities/units, stale statuses and imprecise coordinates are possible. Coordinates are marked `unknown` precision until corroborated. Do not use this release for safety, emergency planning, safeguards, navigation, regulatory, investment, or operational decisions. Validate each consequential record with the relevant international registry, national regulator and current operator evidence.

## Reproduction boundaries

The following commands reproduce only the retained WRI plant layer. They
do not acquire all integrated layers or establish their rights. From this
directory run:

```bash
python3 scripts/fetch_wri_gppd.py --date 2026-09-26
python3 scripts/export_geojson.py
python3 scripts/validate.py
```

The WRI URL is pinned to a Git commit. The separately supplied general Wikidata importer is an optional live
discovery tool and is not the accepted research-reactor producer. The
[research-reactor importer](imports/research_reactors/README.md) documents its
complete offline cache and explicit refresh workflow. The presentation
[dataset builder](../04_interactive_presentation/data/README.md) assembles the
frozen accepted tables and source-verified FFDB products without new acquisition. The historical Fusion live
collector must not be run under the current publisher terms. A deterministic
local build does not resolve source rights or historical acquisition custody.
