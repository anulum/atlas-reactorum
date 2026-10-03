<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — original evidence history and curator workflow
-->

# Evidence history and corrections

The journal retains complete original evidence-profile snapshots, their content
digests and explicit Atlas observation dates. The initial observation is
`2026-10-03T07:31:06.733Z`. It records the current catalogue; it does not invent
earlier revisions or use source acquisition dates as Atlas observations.
The source document describes third-party works and retains their source rights.
The journal redistributes catalogue metadata, not the original publications.

Open the history workspace within the presentation's taxonomy section. Choose
an entry, a claim and an Atlas observation to inspect its original wording,
source locator, support boundary and source metadata. A source or claim change
creates a revision; unrelated profile changes remain in complete retained
snapshots without inventing a claim change. Removed claims remain identifiable;
their disappearance and return have distinct dated revision digests.

Acquisition, claim review and Atlas observation have separate date fields.
The current source contract does not supply structured source-publication or
event dates: these stay null and appear as unknown. A year in a title cannot
fill them. Recorded identities and SHA-256 digests establish content binding,
not authenticated authorship, complete entry review or scientific acceptance.

## Explicit imports

The journal at `history.json` is a retained build input. The presentation JSON
and JavaScript are generated outputs. The native CLI accepts UTF-8 JSON in its
canonical two-space representation with a final newline; member order is
retained. Noncanonical inputs and duplicate keys are refused. All imports and
decisions use a new, nonexistent output path, preserving input custody.

After a separately reviewed source edit, regenerate current profiles and import
them using the actual UTC observation timestamp, with milliseconds:

```bash
node 04_interactive_presentation/scripts/export_taxonomy.cjs
node 04_interactive_presentation/scripts/evidence_history.cjs --import metadata/evidence_history/history.json 04_interactive_presentation/data/taxonomy-evidence-profiles.json ACTUAL_UTC_OBSERVATION NEW_JOURNAL_FILE
```

Review the new journal, retain the predecessor and install the successor as the
accepted journal input through the normal source review. Then run `make build`.
The importer validates every snapshot and source-bound profile, refuses
backdated or broken chronology and retains prior original content. Reimporting
the identical latest profiles returns identical history without a new dated
revision. Returning to older content records a new observation of the retained
snapshot rather than discarding intervening revisions.

`--initialise PROFILES ACTUAL_UTC_OBSERVATION NEW_JOURNAL_FILE` is solely for an
explicit first journal observation. It must not reset existing project history.
`--build ROOT` validates the retained journal and requires its latest profile
digest to match the current exported catalogue before generating either
presentation output. It records no new observation and performs no acquisition.
Output I/O failure rolls back prior presentation products and removes its owned
staging directory. The whole release build reproduces 22 declared products.

## Pending proposals and curator decisions

The page's correction form asks for proposed wording, an anonymous HTTPS source,
a locator, a reason and a contributor name. It prepares a **local download**;
it sends no submission. Supply the unchanged pending JSON to a curator using
the contribution process. It retains the exact original dated revision and
journal hash, proposal time and source information. The original remains intact.

The curator inspects that original content and the proposed source, then writes
a canonical JSON decision with exactly these fields:

```json
{
  "decision": "accepted-for-editing",
  "reviewed_by": "Curator name or handle",
  "reviewed_at": "ACTUAL_CANONICAL_UTC_TIMESTAMP",
  "reason": "Specific source-backed reason for the decision",
  "source_url": "https://publisher.example/original-source",
  "locator": "Exact page or section inspected"
}
```

Use `rejected` for a negative decision. Replace the illustrative values with
actual review metadata; the CLI rejects invalid dates and requires review time
at or after proposal time. The review source must be an anonymous HTTPS URL.
Keep both the original pending file and the new decision product:

```bash
node 04_interactive_presentation/scripts/evidence_history.cjs --review PENDING_PROPOSAL_FILE REVIEW_METADATA_FILE NEW_REVIEWED_PROPOSAL_FILE
```

Both outcomes preserve the original revision and pending digest. Neither
outcome changes source data or the journal. `accepted-for-editing` is followed
by a separately reviewed edit and explicit import as described above; it never
automatically promotes a scientific claim. Reviewer names are declarations,
not authentication. The journal has no dependency on a submission service.

## Exact historical links and validation

Share links bind the complete journal, entry, claim and dated revision:
`#history?version=1&history=…&entry=…&claim=…&revision=…`.
An unavailable digest, identity or revision causes visible refusal with exports
and proposals disabled. A newer journal does not resolve an older link as an
implicit latest alias; keep earlier published journal versions available when
publishing successors. The static current page serves its own exact journal.

The native history, corrections, renderer and CLI suites exercise complete
catalogue inputs and require 100 per cent owning line, branch and function
coverage. The actual Chrome cases exercise retained imports, removals/returns,
versioned navigation, local proposal custody, concurrent selections, mobile
keyboard/source disclosure and actual downloaded files. Coverage uses the
served controller's original native regions and function identities.
