<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
ATLAS REACTORUM — ADR 0002
-->

# ADR 0002 — The atlas hosts the group and project map

**Status:** accepted, 2026-10-12
**Owner decision.**

## Context

Every research group of the ecosystem publishes a group and project map: what
exists, in which state, and how the parts relate. The SCPN Reactor Systems
Research Group had none. Its projects are separate repositories — solver
libraries, a kernel library, device cores and scaffolds — and none of them can
speak for the others.

[ADR 0001](0001-repository-boundary.md) keeps portfolio, federation and
execution responsibilities out of this repository. The atlas already cites
every project of the group with source digests
([portfolio citations](../../metadata/reactor_portfolio/README.md)).

## Decision

The atlas hosts the group's public map and is the presentation of the group's
portfolio: the page [`docs/ecosystem.md`](../ecosystem.md), generated from the
data in [`metadata/group_map/`](../../metadata/group_map/README.md).

This is navigation and citation. ADR 0001 stands unchanged: the atlas owns no
project on the map, assigns no configuration, registers nothing, federates
nothing and executes nothing. Every statement on the map is the owning
repository's own statement, dated and sourced.

## Consequences

- The map is built from a dated source snapshot by an offline builder; the
  page is never edited by hand.
- A change of a project's status reaches the map only through a new snapshot.
- The portfolio catalogue of SCPN-STUDIO and the reactor registry of
  SCPN-PHASE-ORCHESTRATOR keep their owners and their authority.
