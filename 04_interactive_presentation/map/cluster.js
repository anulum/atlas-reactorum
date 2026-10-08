// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — screen-space density aggregation for facility points.

/**
 * Projected coordinates and optional domain retained on the original point object.
 * @typedef {{x: number, y: number, domain?: string|null}} ClusterPoint
 */

/**
 * Screen-space aggregate preserving each original point while its cell has at most 64 members.
 * @template {ClusterPoint} Point
 * @typedef {object} ClusterEntry
 * @property {number} x Mean screen x.
 * @property {number} y Mean screen y.
 * @property {number} count Total cell membership.
 * @property {string} domain Majority domain.
 * @property {string|null} accent Rarity-ranked minority domain, or null.
 * @property {Record<string, number>} domains Domain histogram.
 * @property {Point[]|null} members Original points, or null above the retention limit.
 */

/**
 * Mutable accumulation state for one screen-space cell.
 * @template {ClusterPoint} Point
 * @typedef {object} ClusterCell
 * @property {number} sumX Accumulated screen x.
 * @property {number} sumY Accumulated screen y.
 * @property {number} count Total cell membership.
 * @property {Record<string, number>} domains Domain histogram.
 * @property {Point[]|null} members Original retained points, or null once the limit is exceeded.
 */

/**
 * Minimal world-to-screen boundary used for cell assignment.
 * @typedef {{toScreen: (x: number, y: number) => {x: number, y: number}}} ScreenTransform
 */

/**
 * Host for the classic-script aggregation API.
 * @typedef {object} ClusterGlobal
 * @property {{cluster?: typeof import("./cluster.js")}} [AtlasMap] Browser map namespace.
 */

/**
 * Publish the same aggregation operations to Node or the browser map namespace.
 * @param {ClusterGlobal} root Namespace host when CommonJS is unavailable.
 * @param {() => typeof import("./cluster.js")} factory Aggregation API builder.
 * @returns {void}
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.cluster = factory();
  }
})(
  /** @type {ClusterGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Build screen aggregation, domain selection and glyph-sizing operations.
   * @returns {ClusterAPI} Shared aggregation API.
   */
  function () {
    "use strict";

    // Rarity order, rarest first. Chemical records outnumber fission roughly
    // five to one and fusion by seventy to one.
    //
    // Colouring a mixed cluster purely by rarity overstates the rare domain --
    // almost every cluster contains one fission record, so the whole map turns
    // orange and the reader loses the fact that most sites are chemical.
    // Colouring purely by majority hides fusion entirely. The cluster therefore
    // carries both: a majority fill for honest proportion, and a rarity accent
    // ring so a single fusion device is never invisible.
    /**
     * API types derived from the actual aggregation functions in this factory.
     * @typedef {{aggregate: typeof aggregate, dominantDomain: typeof dominantDomain, majorityDomain: typeof majorityDomain, accentDomain: typeof accentDomain, radiusFor: typeof radiusFor, isSingleton: typeof isSingleton, DOMAIN_PRECEDENCE: string[]}} ClusterAPI
     */
    var DOMAIN_PRECEDENCE = ["fusion", "hybrid", "fission", "chemical"];

    /**
     * Aggregate projected points into screen-space cells.
     *
     * Clustering happens in screen space rather than world space so a cluster
     * stays the same visual size at every zoom level, and so the aggregation
     * threshold means the same thing to the reader wherever they are looking.
     * @template {ClusterPoint} Point
     * @param {Point[]} points Original projected points with their domain and payload.
     * @param {ScreenTransform} transform Viewport exposing world-to-screen conversion.
     * @param {number} cellSize Cell edge in device-independent pixels.
     * @returns {ClusterEntry<Point>[]} Clusters, each with ``x``, ``y``, ``count``,
     *   ``domain`` (majority), ``accent`` (rarest present, or null),
     *   ``domains`` and ``members`` when small enough to expand.
     */
    function aggregate(points, transform, cellSize) {
      if (!(cellSize > 0)) {
        throw new Error("cluster: cellSize must be positive");
      }
      /** @type {Map<string, ClusterCell<Point>>} */
      var cells = new Map();
      for (var i = 0; i < points.length; i += 1) {
        var point = points[i];
        var screen = transform.toScreen(point.x, point.y);
        var col = Math.floor(screen.x / cellSize);
        var rowIndex = Math.floor(screen.y / cellSize);
        var key = col + ":" + rowIndex;
        var cell = cells.get(key);
        if (cell === undefined) {
          cell = {
            sumX: 0,
            sumY: 0,
            count: 0,
            domains: Object.create(null),
            members: [],
          };
          cells.set(key, cell);
        }
        cell.sumX += screen.x;
        cell.sumY += screen.y;
        cell.count += 1;
        var domain = point.domain || "unknown";
        cell.domains[domain] = (cell.domains[domain] || 0) + 1;
        // Members are retained only while a cell is small enough to be worth
        // expanding; beyond that the array would cost memory for nothing.
        if (cell.members !== null) {
          cell.members.push(point);
          if (cell.members.length > 64) {
            cell.members = null;
          }
        }
      }

      /** @type {ClusterEntry<Point>[]} */
      var out = [];
      cells.forEach(
        /**
         * Emit the cell centroid, complete histogram and retained original members.
         * @param {ClusterCell<Point>} cell Populated accumulation state.
         * @returns {void}
         */
        function (cell) {
          out.push({
            x: cell.sumX / cell.count,
            y: cell.sumY / cell.count,
            count: cell.count,
            domain: majorityDomain(cell.domains),
            accent: accentDomain(cell.domains),
            domains: cell.domains,
            members: cell.members,
          });
        },
      );
      return out;
    }

    /**
     * The most numerous domain in a cluster, which sets its fill colour.
     * @param {Record<string, number>} domains Domain-name histogram.
     * @returns {string} The majority domain.
     */
    function majorityDomain(domains) {
      var best = "unknown";
      var bestCount = -1;
      Object.keys(domains).forEach(
        /**
         * Select the first encountered domain whose count exceeds the current maximum.
         * @param {string} key Present histogram key.
         * @returns {void}
         */
        function (key) {
          if (domains[key] > bestCount) {
            bestCount = domains[key];
            best = key;
          }
        },
      );
      return best;
    }

    /**
     * The rarest domain present, when it is not already the majority.
     *
     * Drawn as an accent ring so that a cluster of four hundred chemical sites
     * containing one fusion device still advertises the fusion device.
     * @param {Record<string, number>} domains Domain-name histogram.
     * @returns {string|null} The accent domain, or null when there is none.
     */
    function accentDomain(domains) {
      var majority = majorityDomain(domains);
      var rarest = dominantDomain(domains);
      return rarest === majority ? null : rarest;
    }

    /**
     * Choose the rarity-ranked domain for a mixed cluster.
     * @param {Record<string, number>} domains Domain-name histogram.
     * @returns {string} The rarest domain present.
     */
    function dominantDomain(domains) {
      for (var i = 0; i < DOMAIN_PRECEDENCE.length; i += 1) {
        if (domains[DOMAIN_PRECEDENCE[i]] > 0) {
          return DOMAIN_PRECEDENCE[i];
        }
      }
      var keys = Object.keys(domains);
      return keys.length > 0 ? keys[0] : "unknown";
    }

    /**
     * Radius in pixels for a cluster glyph.
     *
     * Radius grows with the square root of the count so that glyph area, not
     * radius, is proportional to the number of records — the encoding a reader
     * judges correctly. Growth is capped so a dense cell cannot swallow a
     * continent.
     * @param {number} count Records in the cluster.
     * @param {number} [base] Radius of a single record.
     * @param {number} [maxRadius] Hard cap; must stay below half the cell size
     *   or neighbouring glyphs overlap and their labels collide.
     * @returns {number} Radius in pixels.
     */
    function radiusFor(count, base, maxRadius) {
      var b = base || 3;
      var cap = maxRadius || b * 4;
      if (count <= 1) {
        return b;
      }
      return Math.min(b * Math.sqrt(count), cap);
    }

    /**
     * Decide whether a cluster should be drawn as individual records.
     * @param {{count: number}} entry Cluster membership count to classify.
     * @returns {boolean} True when the cluster represents a single record.
     */
    function isSingleton(entry) {
      return entry.count === 1;
    }

    return {
      aggregate: aggregate,
      dominantDomain: dominantDomain,
      majorityDomain: majorityDomain,
      accentDomain: accentDomain,
      radiusFor: radiusFor,
      isSingleton: isSingleton,
      DOMAIN_PRECEDENCE: DOMAIN_PRECEDENCE,
    };
  },
);
