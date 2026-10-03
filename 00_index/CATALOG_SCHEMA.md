<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 00_index/CATALOG_SCHEMA.md
-->

# Catalog schema

Section catalogs use tab-separated values with these columns:

| Column | Meaning |
|---|---|
| `category` | Reactor family or subject area |
| `title` | Document title |
| `year` | Publication year |
| `authors_or_org` | Authors or issuing organization |
| `url` | DOI, publisher or official source URL |
| `local_file` | Relative path when a full text was downloaded |
| `access` | Open, public-domain, metadata-only, or paywalled |
| `status` | Downloaded, cataloged, unavailable, or failed |
| `notes` | Evidence level, format, scope or limitation |

The merged catalog in `metadata/` is generated from the section catalogs after download verification.
