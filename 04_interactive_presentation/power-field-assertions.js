// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — power-unit source roles and unresolved field details
"use strict";

if (typeof require !== "undefined") {
  require("./presentation-text.js");
  require("./power-field-contract.js");
}

/** Source-scoped power-unit details shared by the actual dialog and native renderer. */
var PowerFieldAssertions = (() => {
  const T = globalThis.AtlasPresentationText;
  /** @type {Record<string,string>} */
  const roles = {
    actual_operator: "Current operator",
    historical_operator: "Historical operator",
    explicit_intended_operator: "Intended operator",
    explicit_designated_future_operator: "Designated future operator",
    licensed_project_organisation_combined_install_and_operate:
      "Licensed project organisation",
    historical_design: "Historical reactor class",
    proposed_design: "Proposed reactor class",
  };
  /**
   * Admit original field decisions before the actual detail view consumes them.
   * @param {import("./application-data.js").ApplicationFacility} record Actual facility row.
   * @returns {import("./power-field-contract.js").PresentedPowerDecision[]} Original source-scoped decisions or an absent review.
   */
  function decisions(record) {
    return record.power_field_decisions === undefined
      ? []
      : globalThis.PowerFieldContract.admitPresentation(
          record.power_field_decisions,
          record,
        );
  }
  /**
   * Label a selected value by its reported role rather than its project owner.
   * @param {import("./application-data.js").ApplicationFacility} record Actual facility row.
   * @param {string} field Original operator or reactor_type field.
   * @param {string} fallback Existing label for an original nonempty field.
   * @returns {string} Source-scoped role label or the original fallback.
   */
  function label(record, field, fallback) {
    const decision = decisions(record).find(
      (row) => row.field === field && row.disposition === "qualified",
    );
    return decision ? roles[decision.role] : fallback;
  }
  /**
   * Render a document's date meaning separately from the original capture time.
   * @param {import("./power-field-contract.js").PresentedPowerCitation} row Resolved original documentary citation.
   * @returns {string} Escaped citation, precise date meaning and safe source link.
   */
  function citation(row) {
    return `<li><a href="${T.safeUrl(row.url)}" target="_blank" rel="noopener">Document ↗</a> · ${T.escape(row.locator)} · document date ${T.escape(row.document_date || "unknown")} (${T.escape(row.date_basis.replaceAll("_", " "))}) · captured ${T.escape(row.captured_at)}</li>`;
  }
  /**
   * Show each original disposition and documentary scope without filling held values.
   * @param {import("./application-data.js").ApplicationFacility} record Actual admitted facility row.
   * @returns {string} Escaped original decisions, observations and distinct capture attempts.
   */
  function render(record) {
    const rows = decisions(record);
    if (!rows.length) return "";
    return `<section class="field-sources"><h3>Power unit source review</h3><p>Roles and reactor classes retain their source period. Intended or licensed projects do not establish electricity generation. Author review completed; independent review not recorded.</p>${rows
      .map((row) => {
        const field = row.field === "operator" ? "Operator" : "Reactor class";
        const disposition =
          row.disposition === "qualified"
            ? roles[row.role] + ": " + row.value
            : row.disposition === "held"
              ? "Candidate held"
              : "Not established in reviewed sources";
        return `<article><h4>${T.escape(field)} · ${T.escape(disposition)}</h4><p>${T.escape(row.scope)}</p>${row.citations.length ? `<ul>${row.citations.map(citation).join("")}</ul>` : ""}${row.observations
          .map(
            (observation) =>
              `<details><summary>Source scope${observation.candidate_value && !(row.disposition === "qualified" && observation.candidate_value === row.value) ? " · unselected candidate: " + T.escape(observation.candidate_value) : ""}</summary><p>${T.escape(observation.scope)}</p>${observation.citations.length ? `<ul>${observation.citations.map(citation).join("")}</ul>` : ""}${observation.capture_attempts
                .map(
                  (attempt) =>
                    `<p>Capture attempt · HTTP ${T.escape(attempt.http_status ?? "unavailable")} · captured ${T.escape(attempt.captured_at)} · <a href="${T.safeUrl(attempt.requested_url)}" target="_blank" rel="noopener">Requested source ↗</a></p>`,
                )
                .join("")}</details>`,
          )
          .join("")}</article>`;
      })
      .join("")}</section>`;
  }
  return Object.freeze({ label, render });
})();
globalThis.PowerFieldAssertions = PowerFieldAssertions;
if (typeof module !== "undefined") module.exports = PowerFieldAssertions;
