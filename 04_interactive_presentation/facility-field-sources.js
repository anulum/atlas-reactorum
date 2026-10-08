// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — facility-field-sources.js
"use strict";

const esc = globalThis.AtlasPresentationText.escape;
const safeUrl = globalThis.AtlasPresentationText.safeUrl;
/**
 * Render each admitted original field observation with its source meaning and capture date.
 * @param {import("./application-data.js").ApplicationFacility} record Original row admitted before display; source bindings remain owned by its producer.
 * @returns {string} Original escaped field-source HTML, or empty text when no observation exists.
 */
function render(record) {
  /** @type {Record<string, string>} */
  const meanings = {
    "published-end-use": "Published end use",
    "published-feedstock": "Published feedstock",
    "fuel-classification": "Publisher fuel classification",
    "primary-fuel-classification": "Primary whole-plant fuel category",
    "secondary-fuel-classification": "Secondary whole-plant fuel category",
  };
  const observations = record.field_observations || [];
  if (!observations.length) return "";
  return `<section class="field-sources"><h3>Source field assertions</h3><p>Plant classifications do not establish reactor fuel composition or current physical operation.</p>${observations.map((row) => `<p><strong>${esc(meanings[row.basis])}</strong>: ${esc(row.value)} · original field ${esc(row.source_field)} · captured ${esc(row.checked)} · ${esc(row.license)} <a href="${safeUrl(row.source_url)}" target="_blank" rel="noopener">source ↗</a></p>`).join("")}</section>`;
}
/** Original escaped observation HTML shared by actual detail views and native consumers. */
var AtlasFacilityFieldSources = Object.freeze({ render });
globalThis.AtlasFacilityFieldSources = AtlasFacilityFieldSources;
if (typeof module !== "undefined") module.exports = AtlasFacilityFieldSources;
