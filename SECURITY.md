<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — security policy
-->

# Security policy

## Reporting

Report a suspected vulnerability privately to protoscience@anulum.li, or
through a GitHub private security advisory. Do not open a public issue.

Include what you observed, how to reproduce it, and the affected paths. You
will receive an acknowledgement within five working days.

## Scope

This repository is a static research library and an offline interactive atlas.
It ships no server, no authentication surface and no network service. The
realistic risk surface is therefore:

- **Build scripts** that fetch from official dataset endpoints. Every URL they
  open is a module-level HTTPS constant; none is caller-supplied. See
  `docs/internal/SECURITY_REVIEW.md` for the audited findings.
- **The published page**, which executes only its own bundled JavaScript. It
  loads no third-party script, no remote font and no analytics, and works from
  `file://` with no network access at all.
- **Source data**, which is untrusted text from external registries. It is
  escaped before rendering and never evaluated.

## Out of scope

Findings that require modifying the repository's own source files before
exploitation, and findings in third-party datasets we catalogue but do not
host.

## Supported versions

The current `main` is supported. There are no released versions yet.
