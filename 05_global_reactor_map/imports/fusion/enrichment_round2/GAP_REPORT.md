# Fusion facility round-2 gap report

Source-layer date: 2026-09-28

Effective records: **157** (146 base plus 11 round-1 additions).

Counts are calculated from the explicitly selected inputs. The public compilation selection omits the separately unqualified original Wikidata positions and dates; the complete frozen input route preserves them. The two round-2 coordinate additions remain explicitly attributed CEA host-campus points, not machine surveys.

| Field | Missing before | Missing after | Filled |
|---|---:|---:|---:|
| coordinates | 157 | 155 | 2 |
| configuration | 0 | 0 | 0 |
| device_subtype | 0 | 0 | 0 |
| status | 0 | 0 | 0 |
| organization | 5 | 1 | 4 |
| first_operation_date | 139 | 131 | 8 |
| last_operation_date | 149 | 146 | 3 |

`last_operation_date` is intentionally blank for most operating, planned, and under-construction records. Its raw missing count is not a defect count; applicability is lifecycle-dependent. Likewise, first-operation dates are not expected for unbuilt programmes.

Configuration, subtype, and status were complete before this pass. The status overlay for JT-60SA is a current, source-stated upgrade phase. No generalized vocabulary normalisation is attempted here.

Coordinate policy: only source-published coordinates tied to an unambiguous host facility are allowed. The two new coordinate pairs are the CEA-published GPS point for the Cadarache centre hosting WEST and its Tore Supra predecessor. They are marked campus-level and are not building surveys. No city centroid, geocoder, map click, or inferred coordinate is used.

IAEA FusDIS was not accessed or redistributed.

## Status distribution after round 2

- Cancelled: 1
- Decommissioned: 1
- Operating: 91
- Planned: 20
- Shut down: 28
- Shut down / transformed into WEST: 1
- Under construction: 14
- Under upgrade (post-first-plasma): 1

Country-level raw gap counts are in `gap_report_by_country.tsv`.
