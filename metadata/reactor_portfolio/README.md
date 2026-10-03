<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — project citation interface
-->

# Reactor portfolio citations

[links.v1.json](links.v1.json) is a source-pinned citation snapshot of the
54 Reactor project repositories present at intake. The atlas itself is a
separate evidence library; it is not one of these devices, libraries or
composition proposals. [links.schema.json](links.schema.json) defines the
record format. Every source file is retained under its SHA-256 in `sources/`.

Each record uses the canonical case-preserving `project_id` and owning group.
`source.git_commit` and `source.sha256` identify the exact producer file;
`source.snapshot` preserves those bytes for offline inspection. Native device,
kernel and architecture-boundary manifests establish their own identities.
The two solver-library records cite committed package metadata and do not
infer a device identity or maturity from it.

`configurations` copies only identifiers declared by the source manifest.
`proposed_configuration_id` remains a proposal. `source_declared_maturity`
reports what the producer declared, not what the atlas validated. Missing
producer maturity stays null. No record grants registration, evidence
acceptance, federation, execution or control authority.

`public_repository` is either null or a link actually present in the dated
public GitHub catalogue. Its retrieval date and source snapshot digest remain
explicit. A public link does not imply that the cited local commit was pushed.
The 29 local expansion scaffolds receive no fabricated remote URL. The existing
30-record public ecosystem panel remains a different view: it also includes
control and supporting projects outside this Reactor group.

## Consuming citations and landscape records

A consumer selects a project by exact `project_id`, checks the snapshot schema
and digest against its independently recorded source pin, and checks the
selected producer file digest. It cites the snapshot and producer revision
with the particular record it used. Duplicate project IDs, a count mismatch,
unrecognised schema or missing/mismatched source bytes must refuse intake.
The caller's trusted digest must not be taken from the untrusted record itself.

Landscape citations also retain the original dataset and stable record ID,
source URL, retrieval date, source licence, claim attribution and evidence
scope. Facility rows are not verified reactor vessels. Organisation self-reports
remain self-reports after a correction or sponsorship discussion. Consumers
may use these records for discovery and comparison; scientific capability,
registry and control decisions stay with their existing owners and gates.

New repository suggestions enter the separate candidate review process with
the exact supporting atlas citations. A discovery record is not an approved
candidate, a newly assigned configuration or authority to create a repository.
The catalogue's candidate authority and consumer admission contracts remain
under review. No blanket reverse dependency is introduced into device repos.

## Refresh boundary

Create a new dated snapshot from committed canonical producer files after
reviewing changes; preserve the earlier bytes and revisions used by consumers.
Working-tree edits do not replace a cited commit. Refresh public links only
from a retained dated API snapshot, and do not infer publication from names.
