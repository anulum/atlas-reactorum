<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — native industrial round-seven source corpus
-->

# Native industrial round-seven sources

The corpus retains the complete publisher CSV archive and the complete Italian
bioenergy feature selection controls captured on 30 September 2026. Hashes,
actual acquisition timestamps, resource URLs and source-specific grants are in
[SOURCE.json](SOURCE.json).

| Source | Native records | Selection | Licence |
| --- | ---: | --- | --- |
| Swiss Federal Office of Energy, Biogasanlagen | 153 plants and 974 separate annual production records | Every plant | [opendata.swiss attribution terms](https://opendata.swiss/terms-of-use#terms_by) |
| Arpae Emilia-Romagna, Impianti a bioenergia, aggiornamento 2025 | 330 feature records | 268 rows whose published `TIPO_COMB` contains `biogas`, case-insensitively | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

The Swiss ZIP is unmodified. It contains plant data, three classification
catalogues and annual production data, with original Latin-1 or ASCII member
encoding. Annual production rows refer to plants and do not add facilities.

The Italian count, ID response and all 330 feature rows are unmodified. Layer
metadata retain only the original identity, point geometry declaration, complete
field schema with published unit aliases, and page limit. Map symbols and other
drawing metadata are omitted; the original metadata hash remains recorded.
Every source feature, including the 62 rows outside the biogas selection, remains
available to exercise completeness and selection.

The source corpus preserves literal missing-value markers, zero capacities,
source update dates and notes. Italian productive sections are not reactor
vessels. The 23 Italian source position warnings remain attached to their
records. Three Swiss source names contain `Holzgas` although their catalogue
classifies biogas plants; their actual processes require further evidence.
Swiss CHP capacity is published in kW without an electrical/thermal split.
Coordinates and source status do not establish survey accuracy or current
operation.

Dataset grants cover the stated dataset cells. The source-model PDF, its cover
photograph, full terms-page HTML and full catalogue texts are absent from this
corpus. Neither dataset grant licenses those works or other Atlas sources.

The capture and acquisition integration tests use a complete native custody set,
including verified acquisition receipts and source-specific rights metadata.
Set `ATLAS_INDUSTRIAL7_CAPTURE_DIR` to previously retained original custody to
reuse it. Without that variable the shared session fixture invokes the actual
publisher collector into a new external temporary directory. Importing the test
helper performs no download. OpenSSL supplies the local test TLS certificate;
TLS verification remains enabled for the original servers and the test mirror.
The tests also exercise a direct publisher acquisition. Full terms HTML remains
in temporary or owner-supplied custody and is never added to Git. Changes to
reviewed terms, source schema or native source counts require a new review.
