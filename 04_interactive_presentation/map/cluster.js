// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — screen-space density aggregation for facility points.

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.cluster = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
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
  var DOMAIN_PRECEDENCE = ["fusion", "hybrid", "fission", "chemical"];

  /**
   * Aggregate projected points into screen-space cells.
   *
   * Clustering happens in screen space rather than world space so a cluster
   * stays the same visual size at every zoom level, and so the aggregation
   * threshold means the same thing to the reader wherever they are looking.
   *
   * @param {Array<object>} points Points carrying ``x``, ``y`` and ``domain``.
   * @param {object} transform A viewport exposing ``toScreen``.
   * @param {number} cellSize Cell edge in device-independent pixels.
   * @returns {Array<object>} Clusters, each with ``x``, ``y``, ``count``,
   *   ``domain`` (majority), ``accent`` (rarest present, or null),
   *   ``domains`` and ``members`` when small enough to expand.
   */
  function aggregate(points, transform, cellSize) {
    if (!(cellSize > 0)) {
      throw new Error("cluster: cellSize must be positive");
    }
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

    var out = [];
    cells.forEach(function (cell) {
      out.push({
        x: cell.sumX / cell.count,
        y: cell.sumY / cell.count,
        count: cell.count,
        domain: majorityDomain(cell.domains),
        accent: accentDomain(cell.domains),
        domains: cell.domains,
        members: cell.members,
      });
    });
    return out;
  }

  /**
   * The most numerous domain in a cluster, which sets its fill colour.
   *
   * @param {object} domains Map of domain name to member count.
   * @returns {string} The majority domain.
   */
  function majorityDomain(domains) {
    var best = "unknown";
    var bestCount = -1;
    Object.keys(domains).forEach(function (key) {
      if (domains[key] > bestCount) {
        bestCount = domains[key];
        best = key;
      }
    });
    return best;
  }

  /**
   * The rarest domain present, when it is not already the majority.
   *
   * Drawn as an accent ring so that a cluster of four hundred chemical sites
   * containing one fusion device still advertises the fusion device.
   *
   * @param {object} domains Map of domain name to member count.
   * @returns {string|null} The accent domain, or null when there is none.
   */
  function accentDomain(domains) {
    var majority = majorityDomain(domains);
    var rarest = dominantDomain(domains);
    return rarest === majority ? null : rarest;
  }

  /**
   * Choose the rarity-ranked domain for a mixed cluster.
   *
   * @param {object} domains Map of domain name to member count.
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
   * Area grows with the square root of the count so that glyph area, not
   * radius, is proportional to the number of records — the encoding a reader
   * judges correctly. Growth is capped so a dense cell cannot swallow a
   * continent.
   *
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
   *
   * @param {object} entry A cluster.
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
});
