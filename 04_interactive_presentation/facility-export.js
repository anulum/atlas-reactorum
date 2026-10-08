// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility-export.js
"use strict";

/** Complete filtered record serialization using the original CSV and JSON representations. */
var AtlasFacilityExport = (() => {
  /**
   * Serialize every selected original record without source-cell inference or normalization.
   * @param {import("./application-data.js").ApplicationFacility[]} rows Admitted original records in the selected source order.
   * @param {string} format Original export format; the JSON control selects json and the CSV control selects csv.
   * @returns {string} Original complete JSON or original-column CSV, including its final newline.
   */
  function serialize(rows, format) {
    /**
     * Retain the original scalar representation while quoting a CSV cell.
     * @param {unknown} value Original field or serialized source array.
     * @returns {string} Quoted original CSV representation.
     */
    function csvCell(value) {
      return `"${String(value ?? "").replaceAll('"', '""')}"`;
    }
    const fields = [
        "id",
        "name",
        "country",
        "domain",
        "record_kind",
        "type",
        "status",
        "lat",
        "lon",
        "operator",
        "organization",
        "purpose",
        "process_or_activity",
        "fuel_or_feed",
        "first_criticality",
        "research_field_origins",
        "research_primary_assertions",
        "field_observations",
        "source_urls",
        "source_url",
        "dataset_source",
        "data_caveat",
      ],
      payload =
        format === "json"
          ? JSON.stringify(rows, null, 2)
          : [
              fields.join(","),
              ...rows.map((row) =>
                fields
                  .map((field) =>
                    csvCell(
                      [
                        "field_observations",
                        "research_field_origins",
                        "research_primary_assertions",
                        "source_urls",
                      ].includes(field)
                        ? JSON.stringify(row[field] || [])
                        : row[field],
                    ),
                  )
                  .join(","),
              ),
            ].join("\n");
    return payload + "\n";
  }
  return Object.freeze({ serialize });
})();
globalThis.AtlasFacilityExport = AtlasFacilityExport;
if (typeof module !== "undefined") module.exports = AtlasFacilityExport;
