<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 05_global_reactor_map/imports/industrial_facilities/expansion_round6/VALIDATION.md
-->

# Validation report — industrial expansion round 6

Validation date: **2026-09-28**

Result:

```text
PASS: 1,131 reusable official biofuel and landfill-gas project records; deterministic and no inferred reactors/coordinates/status
```

## Coverage

| Source layer | Records | Records with explicit capacity |
|---|---:|---:|
| Brazil EPE ethanol layer | 431 | 430 |
| Brazil EPE biodiesel layer | 88 | 88 |
| Brazil EPE biomethane layer | 70 | 68 |
| U.S. EPA LMOP operational projects | 542 | 512 |
| **Total** | **1,131** | **1,098** |

All 1,131 coordinates are source-published. All 1,131 `reactor_type_if_explicit` fields are blank.

## Verified assertions

- Exact 18-column output, 17-column compact snapshot and 14-column gap-matrix schemas.
- Exact source counts and complete-layer selection for all four imports.
- 1,131 unique deterministic stable IDs and 1,131 unique source-layer row IDs.
- Output stable IDs exactly match snapshot source keys.
- No stable-ID collisions with the base industrial layer or expansion rounds 2–5.
- Every coordinate is numeric, globally valid and within broad country bounds.
- Every row contains source, role, retrieval date, licence, precision, status and non-inference notes.
- Every source status is explicitly labelled as source-published and not independently verified.
- No inferred reactor type, fermentation process, digester, upgrading technology, coordinate, capacity or status.
- Gap matrix covers ethanol, biodiesel, biomethane, landfill gas, hydrogen, gasification and refining.
- Only sources marked `IMPORT` in the matrix are built.
- `RIGHTS.md` records the CC BY 4.0 and CC0/public-use evidence and limits its conclusion to the exact imported layers.
- Offline rebuilding from the compact snapshot is byte-for-byte deterministic.

## Artifact hashes

- Output TSV: `7fc19ce251a78bbb592e425aca096d23e4a8ae266a8c2840ddf70edda9cf6e48`
- Selected snapshot: `0abfa42538062e30d64b7021884ed6d3910e30cab11d8754c09571ade75d53d1`
- Source-gap matrix: `f3639bc3313af1a098668cb98e0c6bc573edc94c33da35611324a7e80d3add21`
- Source registry: `e9405f80b08576bd381dbdb5ba030f92c064081ec43b257554146fba9ef50339`

## Live-source snapshot evidence

| Source | Raw rows | Bytes | SHA-256 |
|---|---:|---:|---|
| EPE ethanol | 431 | 159,117 | `96fbbbad06fbfa38cd513ab25f5e4efc6c2c09d13f1699aa9080104ae3efb5a7` |
| EPE biodiesel | 88 | 32,079 | `4051d92daae8b8863cfbd3471c54b449d74e8a980ff0946ee3cf6bf1318544f1` |
| EPE biomethane | 70 | 29,489 | `152c6e56bbcb6ca6a5f40b364107be6f6d51ce416018d3767692d6333c982d7f` |
| EPA LMOP projects | 542 | 344,140 | `4cabb678e3bc3e77d625ba0d93ed04cfeb1efdea99d2f5f6bcdb19bd0f9865f8` |

Live-service bytes and hashes can change when publishers update or reserialize their layers. The committed selected snapshot is the evidence input for normal deterministic builds.

## Interpretation limits

- A row is a source plant/project assertion, not an independently verified operating facility or reactor.
- EPE can publish multiple rows at one physical site for operating, construction or expansion records; the import does not collapse them.
- The EPE ethanol layer includes a small number of source types labelled sugar or aguardente; their labels are preserved without inferring ethanol fermentation.
- LMOP is voluntary, periodically updated and not exhaustive. EPA says not every field is updated every year.
- LMOP project technology describes energy use such as an engine, turbine, boiler or vehicle fuel. It is not a reactor-vessel classification.
- Published points are reference locations, not equipment coordinates or survey-grade positions.
