<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/README.md
-->

# Industrial chemical and biochemical facility discovery layer

This reproducible layer contains **6,550 public facility/site records**: 6,150 European chemical or food-and-beverage industrial sites reported for 2024 through the EEA Industrial Emissions Portal, plus 400 operational U.S. livestock anaerobic-digester projects from EPA AgSTAR.

These are **not 6,550 individually verified reactor vessels**. The EEA records establish reported industrial sites and activity classifications, but generally do not disclose the number or design of process reactors. Only EPA AgSTAR rows populate `reactor_type_if_explicit`, because that source explicitly publishes a digester type.

The separately validated `expansion_round2/` layer adds 1,776 source-published facility points: 908 Canadian NPRI records and 868 Australian NPI records. Combined presentation coverage is therefore 8,326 industrial facility/site records. These additions likewise do not infer individual reactor vessels, reactor types, capacities or operating status.

The separately validated `expansion_round3/` layer adds 722 source-published UK PRTR facility points under the Open Government Licence v3.0. Combined presentation coverage is therefore 9,048 industrial facility/site records. The same non-inference boundary applies.

The `expansion_round4/` source-gap audit evaluates seven further jurisdictions and imports 93 qualifying 2024 SwissPRTR facilities. Source LV95 coordinates are retained and WGS84 display points are converted using the documented swisstopo formula. Combined presentation coverage is 9,141 industrial facility/site records; the other jurisdictions remain explicit backlog items rather than silently omitted or imported without a reuse basis.

The validated `expansion_round5/` process-specific layer adds 362 UK REPD anaerobic-digestion planning-project/site records and 31 ADEME hydrogen-production sites. The validated `expansion_round6/` layer adds 589 Brazilian EPE biofuel-layer records and 542 U.S. EPA LMOP landfill-gas energy projects. The validated `expansion_round7/` bundle adds 153 Swiss SFOE biogas plants
and 268 Italian ARPAE biogas-classified bioenergy records. Combined
presentation coverage is 11,086 records. Round seven preserves its complete
selected source snapshot, source/capture registries, rights notes and manifests.
The map builder checks the full seven-artifact bundle before merging any row.
Swiss records retain `LicenseRef-opendata-swiss-terms-by`; Italian records
retain `CC-BY-4.0`. These source records are not assumed to be unique physical plants or individual reactor vessels, and no unpublished process pathway, reactor type, capacity, status or vessel count is inferred.

Rebuild and validate:

```bash
python3 build_industrial_facilities.py --source /path/to/frozen-source.json \
  --output /tmp/industrial-facilities.tsv --date 2026-09-27
python3 validate.py --dataset /tmp/industrial-facilities.tsv
```

The accepted table is never rewritten by the builder. Offline sources use a
versioned envelope with `captured_at` as an ISO calendar date and `sources`
containing `EEA`, `Mixed`, `Cattle`, `Poultry`, `Swine` and `Dairy`. Each source
contains an independent integer `count` and all original scalar `records`.
Every count must agree with the records; coordinates must be finite and in
range, source OBJECTIDs must be unique, and site/project identities must remain
valid. EEA records must retain the selected 2024 year and activity sectors.
Stable-ID collisions refuse the candidate rather than silently merging sites.
Unknown optional quantities stay blank; reported ranges remain source text.

Capture a new source and prepare a separate candidate deliberately:

```bash
python3 build_industrial_facilities.py --refresh \
  --snapshot-out /tmp/industrial-source.json \
  --output /tmp/industrial-candidate.tsv
```

The six services are queried anonymously over certificate-verified HTTPS.
Each acquisition first asks for the count under the same selection predicate,
then requests ordered pages until that exact count is reached. Errors, empty or
oversized pages, malformed feature objects, incomplete acquisition and resource
limits refuse the candidate. A response is limited to 16 MiB, acquisition to
100 pages per service, and each socket operation to 30 seconds; socket timeout
is not a whole-acquisition deadline. `--eea-url`, `--epa-base` and `--ca-file`
allow explicit trusted HTTPS mirrors during refresh. Redirects also require
anonymous HTTPS. These options never change the published source attribution.

All sources, row rendering and UTF-8 encoding are checked before any write.
Destinations must be outside Atlas and separate from resolved inputs, the CA
file and each other. Individual files are atomic; the snapshot and table are
not a multi-file transaction. Failed writes or buffered closes preserve the
prior destination and remove the owned partial temporary file.

Refresh uses today's capture date, retained in the snapshot. Offline rows use
the saved capture date unless `--date` is explicit. The complete test sources
were captured on 2026-09-30 and reproduce all 6,550 historical rows byte for
byte when the original row date 2026-09-27 is requested. That reproduction
does not establish a historical raw-response capture. The source manifest at
`tests/data/industrial_base/SOURCE.json` records original response hashes,
dates, fields and source-specific attribution. No live rebuild automatically
changes the accepted catalogue or its historical count.

## Coverage limits

- EEA: selected systematically where reporting year is 2024 and sector is `CHEMICALS` or `FOOD AND BEVERAGE`; this is European regulatory-reporting coverage, not a global chemical-reactor census.
- EPA AgSTAR: an official but voluntary U.S. program database; EPA states it is not exhaustive and invites corrections.
- No confidential plant inventories, inferred reactor counts or guessed process designs are included.

## Read-only validation

`python3 validate.py --dataset industrial_facilities.tsv` validates an explicit
input path; without the option it reads this directory's historical dataset.
Importing the module performs no validation or output. Validation never rewrites
its input or generates a report file.

The table must be nonempty, with the exact documented column order and complete
rows. Required source observations cannot be blank. The validator checks
coordinate bounds, unique IDs, anonymous HTTPS source URLs and exact ISO calendar
retrieval dates. EEA site records must leave the explicit reactor-type field
empty; EPA's source-published digester labels remain permitted. Optional capacity,
operator and process observations may remain unknown.

A successful run prints the record, country, coordinate, source and explicit-type
counts. Invalid input returns exit status 1 with at most 100 diagnostics and no
traceback. The same checks apply under Python's `-O` option. These checks verify
record integrity and the stated non-inference boundary; they do not establish
physical operating condition or independently verify the source observations.
