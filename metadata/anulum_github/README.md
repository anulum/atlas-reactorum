<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — metadata/anulum_github/README.md
-->

# ANULUM GitHub reactor-repository catalog

This catalog is a dated public-metadata snapshot of reactor-related repositories under `github.com/anulum`. It prevents the presentation from maintaining a short hand-written selection that silently misses device families.

Included categories are device-family architecture, shared physics/kernels, control/integration and directly supporting hardware/compute. General AI, agent infrastructure and unrelated forks are excluded. Repository presence, code volume, tests or formal software properties do **not** independently validate reactor physics, hardware performance, energy gain or commercial readiness.

Offline reproduction uses the accepted dated snapshot and a separate output bundle:

```bash
python3 build_repo_catalog.py --output-dir /tmp/atlas-repository-catalogue
```

The bundle contains `reactor_repositories.tsv`, `reactor_repositories.json`,
`anulum_reactor_repos.json` and `anulum_reactor_repos.js`. Accepted catalogue
and presentation files are not rewritten. The historical catalogue date
2026-09-27 applies only to the default accepted source. A custom `--source PATH`
requires its explicit `--date YYYY-MM-DD`; an update timestamp is not a capture
date. Review a candidate before integrating it into the dated catalogue.

A deliberate online refresh prepares both an isolated source snapshot and bundle:

```bash
python3 build_repo_catalog.py --refresh \
  --snapshot-out /tmp/atlas-repository-refresh/source_snapshot.json \
  --output-dir /tmp/atlas-repository-refresh/catalogue
```

Online retrieval uses today's calendar date unless `--date` is explicitly
provided, and records it in the new snapshot envelope as well as catalogue
rows. It follows the GitHub REST API's `Link` next relation through every
page; duplicate identities, malformed links, loops, changes of authority or
endpoint, API error bodies and resource-limit failures are refused. Anonymous
HTTPS verifies certificates and limits total response bytes, pages, redirects
and socket operations. Socket timeout is not a whole-download deadline.
`--api-url` and `--ca-file` support an explicitly trusted HTTPS mirror during
refresh; neither permits credential-bearing URLs or private-repository import.

Every source record must retain its exact public ANULUM repository/API identity,
boolean flags, scalar metadata, well-formed topic list and timezone-aware ISO
update timestamp. Snapshot envelopes must have matching schema/count/records.
The original fixed portfolio selection and evidence boundaries are preserved;
a missing relevant repository refuses the whole candidate. This dated public
catalogue is separate from the current canonical portfolio registry and does
not establish physical performance, current publication visibility or a
software licence beyond the GitHub metadata observation.

All requested destinations must remain outside the accepted Atlas and separate
from resolved source/CA/snapshot/output paths. Full parsing and rendering precede
writing. Individual files are replaced atomically; the source plus four outputs
are not a single multi-file transaction. Offline `validate.py --input PATH`
can check a generated TSV; its frozen 30-record/archival rules remain unchanged.

The dedicated producer tests use all 43 original public records, including the
13 actual exclusions, through a localhost HTTPS server with a generated trusted
certificate. `tests/data/anulum_github/SOURCE.json` records the original and
minimised fixture hashes and omitted unused fields. The fixture retains every
consumed cell; it does not establish a newer capture date or grant rights to
referenced software or hardware. Native CLI tests cover online snapshot creation,
offline reproduction and output alias refusal. Real file-size limits exercise
both write and buffered-close failures: neither changes the previous destination
or leaves its partial temporary file.

Pagination reference:
https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
