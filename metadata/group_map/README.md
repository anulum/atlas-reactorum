<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — group map contract
-->

# SCPN Reactor Systems group map

This directory holds the data behind the public
[group and project map](../../docs/ecosystem.md) of the SCPN Reactor Systems
Research Group. The atlas hosts the map as a navigation page
([ADR 0002](../../docs/adr/0002-group-and-project-map.md)). It owns none of the
projects on it and validates none of their statements.

| File | Role |
| --- | --- |
| `source_snapshot.json` | Dated source snapshot: one record per repository of the group. |
| `ecosystem_projects.json` | Project data derived from the snapshot, one entry per project. |
| `build_group_map.py` | Offline builder of the project data and of the page. |

## What a snapshot record holds

Each record holds only values read on the capture date from a named place:

- the repository's own files at the recorded commit: `pyproject.toml`
  (package name, description, licence, development-status classifier,
  requirements on other projects with their line), the SPDX line and the
  commercial-licence line of `README.md`, and the repository's manifest
  (`reactor-domain.json`, `kernels-domain.json` or `project-boundary.json`:
  declared evidence maturity, family, configurations, number of listed
  capabilities, registry pin);
- the public Python index: whether the package exists there, and its latest
  version;
- the public repository listing of the hosting account: whether a public
  repository of that name exists.

The collector runs outside this repository, because it reads the group's other
repositories. The recorded commit is the local canonical commit on the capture
date; a public link does not imply that this exact commit was published.

## How the project data are derived

`build_group_map.py` reads the snapshot and the retained
[portfolio citations](../reactor_portfolio/README.md) and nothing else. It
refuses a snapshot whose projects differ from the cited ones, a project
without a single stated licence, an unknown evidence maturity or family, and a
family that disagrees with the citation.

The status word follows three rules, in this order:

1. a package on the public index and at least one release tag: `released`;
2. the manifest declares `architecture_only`: `architecture stage`;
3. a public repository otherwise: `under development`.

A project that matches no rule is refused; no status is guessed.

A scaffold's scope is its manifest's boundary sentence. Where that sentence
names another scaffold by its plan identifier, the builder writes the project
that the snapshot records under that identifier instead; no other word of a
source is changed.

The file follows the working shape `ecosystem-projects/0.2` shared by the
groups of the ecosystem, which may still change. Beside the shared fields it
carries what this group's repositories state about themselves:
`declared_evidence_maturity`, `device` (family, confinement family,
configurations, number of listed capabilities), `family`, and the source of the
function and licence fields.

## Commands

```bash
python3 metadata/group_map/build_group_map.py --check
python3 metadata/group_map/build_group_map.py --output-dir /absolute/outside/directory
```

`--check` compares the accepted project data and page with the bytes rendered
from the accepted snapshot. `--output-dir` writes a candidate bundle into an
existing directory outside this repository; accepted files are never
rewritten by the builder. Review a candidate, then replace the accepted files
together with the snapshot they were rendered from.

## What the map does not establish

- A status or a declared evidence maturity is the repository's own statement
  on the capture date. It is not a validation of physics, accuracy, safety or
  readiness by this atlas or by the group.
- The number of listed capabilities is a count of manifest entries, not a
  measure of what they compute.
- Counts on the page are computed for the capture date. They are not totals
  or targets.
- A link is drawn only where a cited file states it. An optional interface or
  a pinned registry version is not a hard dependency.
- Unpublished repositories are named as local scaffolds. Naming them grants
  no registration, configuration identifier or publication.
