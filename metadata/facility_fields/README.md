<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/facility_fields/README.md
-->

# Source-supported facility field projection

These native tools retain explicit published uses, feedstocks and fuel
classifications with each original field, record identity, source URL, capture
date, licence and SHA-256. They perform no network requests and do not modify
the original source tables.

The complete projection contains 1,631 assertions: 1,092 published uses and
539 fuel/feed classifications or feedstocks. It preserves 195 WRI primary
whole-plant categories and all six secondary categories (four Oil, one Hydro,
one Gas), 397 AgSTAR biogas end uses, 542 LMOP end-use categories, 70 EPE
feedstocks, 153 Swiss valorisation labels and 268 Italian fuel classifications.
Three absent AgSTAR end-use cells remain absent.

WRI categories describe whole plants, including ancillary classifications;
they do not describe reactor fuel material or isotope composition. Italian
labels are publisher fuel classifications. EPE `MateriaPri` is an explicit
feedstock field. Animal classes, crop names embedded in plant classes and
hydrogen production labels are not converted into inferred reactor feedstocks.

`source_pins.json` records ten complete original-source artifacts and four
accepted target tables. Original native identities bind assertions to their
specific discovery records; neither facility names nor geographic proximity
are used to merge records. The preparation input corpus includes genuine
retained source fixtures from the complete research checkout. The prepared
`observations.json` and `observations.sha256` form the frozen release input.
The map builder validates the pin digest, every present target-table digest
and the complete assertion scope before amending any record. Release builds
do not require the preparation fixtures. Historical source-rights review
remains separate.

From any working directory, use absolute script paths:

```sh
python /path/to/metadata/facility_fields/build.py \
  --source-root /path/to/complete/research/checkout \
  --output /existing/external/directory/new-field-observations.json

python /path/to/metadata/facility_fields/validate.py \
  --source-root /path/to/complete/research/checkout \
  --dataset /existing/external/directory/new-field-observations.json
```

The producer requires a new destination outside both the original source tree
and the repository, below an existing parent without symlink ancestors.
Protected writes use an atomic hard link and never replace existing bytes.
The facility schema is 1.1.0; the company schema remains 1.0.0. Original
industrial stable identifiers retain their case even when map identifiers
are normalised for display. A wholly absent optional target layer contributes
no assertions; a present changed layer or incomplete projection is refused.

The read-only validator compares every output byte with the complete original
projection. Both CLIs retain their guards under Python `-O`.

The projected values retain CC BY 4.0, U.S. public-domain/CC0 and the reviewed
Swiss attribution terms according to their source. Code is AGPL-3.0-or-later.
No source classification establishes current operation, vessel count,
reactor design or an independently verified physical fuel cycle.
