<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 04_interactive_presentation/data/README.md
-->

# Atlas datasets

The presentation loads the entire local source datasets: 1,823 power-reactor-unit
records, 195 plant-level discovery records, 172 research-reactor records, 174
IAEA FFDB catalogue records, 11,086 industrial facility/site or process-project records and ten
supplemental records. One exact-name/domain supplemental duplicate is merged,
leaving 13,459 map records, plus 98 audited company and programme records. The
`.sample` filenames are retained for compatibility with the page.

`taxonomy-audit.json` and its `file://`-compatible JavaScript twin expose the
scientific/editorial audit for all 135 taxonomy entries. The first pass covered 123; the 11
later additions were audited on 2026-09-29 and the critical/subcritical entry
was split into two. All 135 have classification/source-scope records.
Schema 1.3.0 also carries 599 source-inspected statements for 135 entries in
`claim_citations`, with exact sections and distinct printed/PDF page pointers.
Four hundred and eighty statements bind complete principle, strength or challenge fields.
This includes 25 statements for the 15 physical fields of the batch, semi-batch,
CSTR, plug-flow and CSTR-cascade entries; model assumptions, exothermic
conditions and process-specific cascade benefits remain explicit.
Resolved sources expose their capture method and known retrieval timestamp;
retained NRC, IAEA and MDPI originals whose
retrieval dates are unknown keep a null timestamp.
Every record keeps `complete_entry_review: false`; full per-claim verification
remains pending. The [citation contract](../../metadata/taxonomy_audit/README.md)
explains source custody, semantic bindings and the additive TSV/JSON/JS exports.

The ecosystem panel loads 30 public reactor-related `github.com/anulum`
repositories from `anulum_reactor_repos.*`. Its dated source snapshot and refresh
script live in `../../metadata/anulum_github/`; unrelated repositories are excluded.
Repository metadata and software evidence are not reactor-performance evidence.

Run `python3 scripts/build_datasets.py` from the presentation directory to rebuild
both JSON and offline JavaScript bundles. The converter uses only local files;
it does not perform fresh research or upgrade the evidence quality of the inputs.
`dataset-inventory.json` records input hashes and output counts.

## Provenance and interpretation

- Plant records: `../../05_global_reactor_map/data/reactors.tsv`, derived from
  the World Resources Institute Global Power Plant Database snapshot. WRI data
  is CC BY 4.0; the source URL, publisher, license, quality flags and verification
  notes are retained in each output object. These are source plant records, not
  195 independently established reactor units. Names sometimes resemble unit
  names, but no unit inference is made. All 195 statuses remain `unknown`.
  Capacity is the source's plant-level electrical capacity, not thermal power.
- Supplemental records: `facilities-supplemental.json`, preserving the original
  presentation's ten records and authority links. The output downgrades their
  location completeness to `partial` because this integration does not verify
  their approximate coordinates. ISOLDE remains `context-only`, an accelerator
  isotope facility included as context, not a reactor. Original statuses are
  retained with an explicit recheck caveat; they are not newly verified.
- Research-reactor records: `../../05_global_reactor_map/imports/research_reactors/`.
  The open layer contains 172 records from Wikidata CC0 discovery and an openly
  licensed CNSC supplement. Fifty-four exact-ID official-source overlay rows
  add reviewed status, type, power, operator, purpose and date values without modifying the base. IAEA RRDB was
  referenced but not redistributed. The complete
  [primary field bundle](../../05_global_reactor_map/imports/research_reactors/official_source_enrichment/README.md)
  retains 358 individual decisions for originally blank fields: 275 selected,
  53 held, and 30 explicit unknown, composite, planned, nonapplicable or
  never-critical outcomes. Dataset schema 1.3.0 exposes every decision as
  research_primary_assertions in map details and JSON/CSV exports. Original
  nonempty cells and coordinate precision remain unchanged; scope and rights
  do not become an independent confirmation of current operation.
- Fusion records: `../../05_global_reactor_map/imports/fusion/ffdb/`. The default
  build uses all 174 visible FFDB catalogue records captured on 2026-10-02.
  It decodes the complete pinned capture and compares both cached source
  products before exporting. The 137 map points retain raw source precision;
  displayed rounding is recorded separately. Their facility/device granularity
  is unspecified. Operation dates and missing coordinates remain absent.
  Six supplemental fusion context records remain separate, so the domain has
  180 records. No historical enrichment or supplemental coordinates fill FFDB
  cells. IAEA's FFDB-specific reuse statement requires acknowledgement and no
  implied endorsement; it is not CC0, CC BY or the code's AGPL licence.
  See [source rights](../../05_global_reactor_map/imports/fusion/ffdb/RIGHTS.md).
  The explicit `--fusion-source historical` route retains 146 base identities
  with the six attributed compilation fields, three separate overlay passes and
  eleven additions. The complete original 18-column route requires
  its distinct frozen inputs; the public route also accepts
  `--historical-bundle /path/to/public-snapshot` and records all nine verified
  source and registry hashes. The complete original route uses
  `--fusion-source historical-full --historical-bundle /path/to/complete-inputs`.
  For the full route, all nine hashes and schemas are checked before capture and export;
  external source possession is not a redistribution grant. See the
  [historical input contract](../../05_global_reactor_map/imports/fusion/README.md)
  and [actual field rights](../../05_global_reactor_map/imports/fusion/source_rights.json).
- Power-reactor units: `../../05_global_reactor_map/imports/power_units/`. The
  1,823-record layer is adapted from GEM GNPT August 2026 under CC BY 4.0. Its
  590 plants/projects can overlap the older WRI plant layer. Source nameplate
  capacity is preserved without relabelling it as net or gross power.
- Industrial facilities: `../../05_global_reactor_map/imports/industrial_facilities/`.
  The 11,086 bounded records span EEA, EPA, Canadian, Australian, UK, Swiss,
  French, Brazilian and Italian official layers. They are public facility/project observations, not an inferred inventory of reactor vessels.
  Only AgSTAR rows carry an explicit source-published digester type.
  Round seven adds 153 Swiss SFOE biogas plants and 268 Italian ARPAE
  biogas-classified records. Its complete seven-artifact source bundle is
  validated before any map export, and all seven input hashes appear in
  `dataset-inventory.json`. A wholly absent round is optional; a partial,
  edited or dangling-artifact bundle refuses the build. Swiss CHP capacities
  stay in kW without an inferred electrical/thermal split, Italian fuel
  labels remain classifications, and original operator/status observations
  remain distinct from presentation normalisation. The sources retain their
  separate Swiss terms-by and Italian CC BY 4.0 licences.
- Companies: `../../metadata/company_audit/audited_companies.tsv`, joined to the
  original discovery candidate register and three expansion rounds. All 98 rows, including inactive programmes, suppliers,
  propulsion ventures and speculative claims, are retained. Claims, independently
  supported bounded milestones and unsupported/ambiguous claims are displayed separately.
  The 39 depth-enriched records use the latest overlay for both the current
  fields and their presentation aliases: status, milestone, limitations,
  official link and audit date. Source dates and evidence links also come from
  that overlay; superseded links are not merged into the current reference list.
  The [latest ten-profile review](../../metadata/company_audit/depth_round8/README.md)
  records 33 citations and 21 metadata fields reviewed, without asserting
  physical gap closure. Programme fuel plans remain distinct from unknown
  prototype fuel; company-authored papers and surveys retain their stated roles.
  Earlier source catalogues remain available as dated inputs;
  applying an overlay does not turn its claims into independent results.

Unknown values remain unknown. `source_checked` copies the prior catalog date,
not the date of a fresh verification. No headquarters coordinates are converted
into reactor locations. Company records are not automatically plotted on the
facility map. One exact-name/domain supplemental duplicate is merged; FFDB
source records retain their separate publisher identity and coordinates. Records
are not merged by geographic proximity because nearby records may be distinct.

The map is an incomplete discovery dataset. Authoritative record-level reconciliation,
additional national research-reactor sources, historical fusion facilities and
jurisdiction-by-jurisdiction industrial coverage remain necessary. The catalog does
not claim an exhaustive count of world reactors, facilities or companies.

## Data reuse

[source_rights.json](source_rights.json) records all default input hashes,
16 source components, original terms and ordered field-overlay scopes.
The facility JSON/JS are mixed data files; source terms apply to the source
cells and AGPL to original Atlas contributions. Preserve each layer's
attribution, source date, licence and adaptation notes. The code licence does
not replace source licences or grant rights to linked publisher works. See
[full attribution](../ATTRIBUTION.md).
