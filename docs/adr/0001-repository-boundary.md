<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — ADR 0001
-->

# ADR 0001 — Repository boundary

**Status:** accepted, 2026-09-29
**Owner decision.**

## Context

The workspace began as a research prototype handed over by a previous agent. It
needed a name, a boundary, and a place in the SCPN reactor-family portfolio.

The reactor-family standard assigns a standalone device core to each materially
distinct reactor family, and names SCPN-STUDIO as the portfolio catalogue and
evidence workbench. An evidence library is neither a device core nor the studio.

## Decision

Atlas Reactorum is a **standalone repository**: an English-first, source-aware
atlas and research library of reactor technology across fission, fusion,
chemical and biochemical, hybrid and speculative domains. It is associated with
the SCPN reactor-family portfolio and will be cross-linked with owner projects.

It owns no reactor physics, no solver mathematics and no control authority. It
does not actuate anything. It catalogues evidence and presents it.

## Consequences

- The repository holds catalogues, overlays, validators and a static front end;
  it does not acquire device models or control adapters.
- Cross-linking to device projects is by citation, not by shared code.
- Publication to the homepage is a separate authority profile and is not
  implied by local scaffolding.
- **Placement confirmed, 2026-09-29.** Checked against
  `SCPN_REACTOR_FAMILY_REPOSITORY_STANDARD.md` and
  `configs/scpn_reactor_family_repository_map.json` (schema 1.1.0). The map
  defines four classes: `existing_repositories` (2 device cores),
  `planned_repositories` (22 device cores), `shared_library_projects` and
  `shared_interface_projects`. It contains no atlas, evidence-library or
  `reactorum` entry.

  Atlas Reactorum matches none of those classes. It has no governing
  confinement physics, no primary driver, no shot or plant lifecycle, no
  diagnostic or clock model and no solver, evidence or control-contract
  boundary — the five properties the separation rule uses to define a device
  repository. Nor is it a physics, geometry, numerics, CAD or meshing kernel
  library.

  It therefore sits **outside** the family map rather than in conflict with
  it: a standalone research and evidence library, associated with the
  portfolio and cross-linked by citation. The standard neither assigns nor
  forbids it, and no `configuration_assignments` entry is affected.

  Note the boundary with SCPN-STUDIO, which owns the manifest-driven
  *portfolio* catalogue for SCPN's own devices. Atlas Reactorum catalogues
  externally published world reactor technology. The two do not overlap, and
  this repository must not acquire portfolio, federation or execution
  responsibilities that belong to SCPN-STUDIO.
