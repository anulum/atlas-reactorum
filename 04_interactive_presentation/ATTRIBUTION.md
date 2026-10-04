<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — 04_interactive_presentation/ATTRIBUTION.md
-->

# Attribution and licence boundary

The presentation code and original editorial text are licensed under
AGPL-3.0-or-later, with a separate commercial licence route; see the repository
LICENSE and COMMERCIAL-LICENCE.md. Third-party sources and adapted datasets
retain their own terms. Inclusion does not grant new rights to those works.

External publications, websites, trademarks and reactor/company names remain the property of their respective owners. Links and short factual summaries are provided for research attribution. No third-party PDFs or source code are embedded in this presentation. Consult `SOURCES.tsv` for provenance.

The world land outline is derived from Natural Earth 1:110m land data, in the public domain: https://www.naturalearthdata.com/about/terms-of-use/ . It is embedded in the page for offline use. CSS presentation graphics are original assets.

The 195 imported plant records derive from the World Resources Institute Global Power Plant Database, licensed CC BY 4.0, https://github.com/wri/global-power-plant-database . The 1,823 power-reactor-unit records are adapted from Global Energy Monitor's August 2026 Global Nuclear Power Tracker under CC BY 4.0. The 6,150 European industrial-site records are attributed to the European Environment Agency under its stated CC-BY reuse terms, and 400 U.S. digester records come from the federal EPA AgSTAR program. Research-reactor and fusion-device layers carry their own record-level source and licence fields.

The atlas transforms source columns to its presentation format, documents modifications and retains provenance; it does not establish current operating status or infer reactor vessels from industrial-site records. Company statements are separated from bounded independent evidence and unsupported or ambiguous claims. See `data/README.md` and each import directory for details.

The default fusion catalogue is adapted from the International Atomic Energy
Agency's Fusion Facility Database (FFDB), captured on 2026-10-02:
https://nucleus.iaea.org/sites/fusion-portal/SitePages/FFDB.aspx?web=1 .
The FFDB-specific reuse statement requires IAEA acknowledgement and no implied
endorsement. No endorsement by IAEA is implied. See
`../05_global_reactor_map/imports/fusion/ffdb/RIGHTS.md` for the separate
data and captured-container boundaries. The historical FusionBenchmark public selection retains six compilation/classification
fields under its dated CC BY4.0 terms. Other historical fields and overlays have
separate source scopes; original frozen inputs are not embedded here.

## Mixed data files

The facility JSON and offline JavaScript contain contributions under several
source licences. Their SPDX expression lists these terms together; it does not
apply the code's AGPL licence to foreign source cells. The
[data rights map](data/source_rights.json) binds all16 source components and the
ordered overlays to the input hashes in dataset-inventory.json. Retain the
source attribution, capture/update date, licence and modification notes for
each portion reused. A final per-record source label does not replace earlier
field origins when an overlay leaves a value unchanged.

Contains information licensed under the Open Government Licence – Canada.
UK PRTR and REPD information is attributed to DEFRA and the Department for
Energy Security and Net Zero under OGLv3.0. Swiss PRTR and biogas data retain
FOEN/SFOE attribution and the opendata.swiss terms_by notice. ADEME hydrogen
project data retain ADEME attribution and source update date under Etalab2.0.
EEA reuse retains item-specific and third-party exceptions; EPA source data
retain their distinct public-domain or source-declared CC0 scopes. None of
these grants extends to referenced operator publications, logos or images.

Company records and unlicensed-source overlays are original Atlas selections
and summaries of isolated factual assertions. Source expression remains
reserved. A .gov host, a citation or a data checksum is not by itself a
licence over a laboratory's article, report, slides or images.

## Research field sources

The complete research catalogue retains its original source cells and terms.
The [primary field bundle](../05_global_reactor_map/imports/research_reactors/official_source_enrichment/README.md)
adds individually scoped factual assertions and explicit held/no-fill decisions.
Its [source registry](../05_global_reactor_map/imports/research_reactors/official_source_enrichment/source_registry.tsv)
records original body hashes and retained rights. Publisher PDFs, pages and
scans are referenced rather than embedded; Atlas does not grant rights to them.
