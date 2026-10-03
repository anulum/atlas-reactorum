<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — threat model
-->

# Threat model

## What is being protected

The integrity of the evidence: that every record traces to a real source, that
no value was invented, and that a claim is never presented as a result. The
public source selection excludes the complete FFDB viewer and permission-page
containers. Their originals remain in private acquisition custody.

## Assets

1. Source catalogues and enrichment overlays (TSV).
2. Generated datasets and their checksums.
3. The atlas page and its map engine.
4. The build and validation scripts.

## Adversaries and exposures

**Untrusted source data.** Records come from external registries and contain
attacker-influenceable text — facility names, notes, URLs. It is escaped before
rendering and never evaluated. Source URLs are constrained to HTTP(S) at build
time, and the build refuses to publish a record without one.

**Supply chain.** The offline build consumes pinned local inputs rather than
refreshing publishers. Acquisition tools and source checks may use explicitly
selected mirrors, institutional certificate bundles or catalogue URLs. These
are trust boundaries, not constant-only inputs; their URL, redirect, deadline
and executable-selection guards require source-specific transport tests.
The retained historical Fusion collector refuses every live request before
opening any protocol. Its CLI returns an authored refusal with exit code 2;
the frozen historical integration remains separate from acquisition. Workflows pin every action
to a full commit SHA; development dependencies use a hash-locked graph.

**Captured-source integrity.** The default FFDB integration redecodes the
complete visible-data selection and requires agreement with its manifest, TSV and
field provenance before writing outputs. It refuses missing or changed
products without a historical fallback. Digests prove consistency with the
recorded artifact and original-response linkage; they do not authenticate a publisher, establish physical
identity or grant redistribution rights.

The public source tree excludes the full viewer response and permission-page
HTML. The data projection selects dictionaries and visible pane indices directly
from the retained original, with a distinct artifact hash and labelled header.
The reader and registered producer check its acquisition identity; publisher
data permission does not license the excluded renderer or unrelated material.

**Silent corruption.** The realistic failure is not an intruder but a refactor
that changes output unnoticed. Mitigated by deterministic builds, checksums,
and tests that rebuild from deleted artefacts rather than comparing files that
are already correct.

**Fabricated completeness.** The most damaging failure mode for a research
atlas is overstating coverage. Mitigated by per-layer provenance, explicit
missing-field counts, catalogue-only records where redistribution is
restricted, and caveats retained on every record.

## Out of scope

Network attacks on a service (there is none), authentication and authorisation
(no accounts), and confidentiality of deliberately published catalogue values. Private
acquisition containers are outside the distributable source tree.

## Residual risk

Native browser checks use isolated profiles and loopback-only DevTools. The
normal Chrome sandbox is enabled by default. The explicit
`ATLAS_BROWSER_NO_SANDBOX=1` test option is for hosts configured to run trusted
local assets in that mode; its evidence must identify the changed boundary.
It does not change the checks or qualify untrusted pages.

The 24 subprocess import/invocation reports have individual B404/B603 annotations.
Importing the module creates no process. Each invocation uses an argument list,
a finite deadline and either a fixed sibling/build command or an operator-selected
native tool. External source bytes enter the PDF tool through standard input;
URLs enter curl after its explicit option separator and HTTPS-only guards.
The annotations leave executable syntax unchanged and apply to those exact calls.
A scan with annotations ignored retains all 24 reports. Independent review
accepted the original acquisition refusal and all 12 invocation sites. Ten
current sites retain those exact bytes; the two historical validators changed
for frozen-bundle input selection and require their successor disposition.
The boundary assumes a trusted operator, native-tool lookup and local scripts,
with finite per-process deadlines. It does not promise descendant containment.
The historical URL-opening sink has been removed by the acquisition refusal.

An annotated scanner pass does not establish source rights or whole release
approval. FFDB permission covers its selected data and generated mapping;
historical compilation permission covers six fields for 146 identities.
Neither extends to other data, coordinates, linked works or new live copying.
The component rights map preserves the separate source contributions; remaining
mixed-source and isolated historical factual scopes require their own decisions.

A source publisher may itself be wrong. The atlas records what the source
states, with its retrieval date and access limitations, so a reader can check
the original. It does not adjudicate between conflicting publishers; it records
both and marks the disagreement.
