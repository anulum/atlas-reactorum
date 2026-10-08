// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — owning schema types for generated browser products.

import type { AtlasEvidenceJournal } from "./evidence-history.js";
import type { AtlasEvidenceDocument } from "./taxonomy-evidence-profile.js";
import type { TaxonomyRow } from "./scripts/taxonomy_export_inputs.cjs";
export type { AtlasEvidenceJournal } from "./evidence-history.js";
export type { AtlasEvidenceDocument } from "./taxonomy-evidence-profile.js";
/** The native DOM library's complete map of actual HTML element tags. */
export type AtlasElementTags = HTMLElementTagNameMap;
/** Native readonly array input, preserving the caller's source cells. */
export type AtlasReadonlyArray<T> = ReadonlyArray<T>;
/** Native map instance parameterized by the actual admitted facility row. */
export type AtlasFacilityMap = InstanceType<
  typeof import("./map/engine.js")<
    import("./application-data.js").ApplicationFacility
  >
>;
/** Authored fallback display cells; missing source identity remains explicitly absent. */
export type AtlasFallbackTaxonomyRow = Pick<
  TaxonomyRow,
  | "name"
  | "domain"
  | "family"
  | "maturity"
  | "evidence"
  | "principle"
  | "strength"
  | "challenge"
  | "temp"
  | "mode"
  | "scale"
  | "control"
> &
  Partial<TaxonomyRow>;

declare global {
  /** Original actual mounted facility-map instance, absent before initialization. */
  var atlasMap: AtlasFacilityMap | null;
  /** Original public taxonomy-detail function bound to its actual catalogue owner. */
  var openReactor: ReturnType<
    typeof globalThis.AtlasTaxonomyCatalogue.create
  >["open"];
  /** Original public facility-detail function bound to its actual source owner. */
  var openFacility: ReturnType<
    typeof globalThis.AtlasFacilityCatalogue.create
  >["open"];
  /** Original public complete filtered-record reader. */
  var filteredFacilities: ReturnType<
    typeof globalThis.AtlasFacilityCatalogue.create
  >["filtered"];
  /** Original native CSV/JSON download entry point. */
  var downloadFacilityData: ReturnType<
    typeof globalThis.AtlasFacilityCatalogue.create
  >["download"];
  /** Actual classic-script map namespace; each dependency and constructor may be absent before loading. */
  var AtlasMap: import("./map/engine.js").EngineGlobal["AtlasMap"];
  /** Generated or original dataset cells remain unknown until actual application admission. */
  var REACTOR_FACILITIES: unknown;
  /** Company claims retain their producer fields before actual display admission. */
  var FUSION_COMPANIES: unknown;
  /** Original authored taxonomy before complete shape admission. */
  var REACTOR_TAXONOMY: unknown;
  /** Authored locator table before any consuming source contract admits its cells. */
  var REACTOR_TAXONOMY_SOURCES: unknown;
  /** Authored catalogue limitations, version and snapshot wording before admission. */
  var REACTOR_TAXONOMY_META: unknown;
  /** Historical audit product before original-column admission. */
  var REACTOR_TAXONOMY_AUDIT: unknown;
  /** Repository source product before card-field admission. */
  var ANULUM_REACTOR_REPOS: unknown;
  /** Actual navigation controller; unavailable until page startup binds its controls. */
  var pageNavigation:
    ReturnType<typeof globalThis.AtlasPageNavigation.start> | undefined;
  /** Complete journal emitted only after native shape and integrity admission. */
  var REACTOR_EVIDENCE_HISTORY: AtlasEvidenceJournal;
  /** Complete profile product admitted by its source-bound Python exporter. */
  var REACTOR_TAXONOMY_EVIDENCE_PROFILES: AtlasEvidenceDocument;
}

export {};
