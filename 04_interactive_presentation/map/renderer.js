// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — canvas painting for the facility map.

/**
 * Canvas operations and state touched by the renderer; a real 2D context satisfies this contract.
 * @typedef {Pick<CanvasRenderingContext2D, "save"|"restore"|"fillRect"|"beginPath"|"moveTo"|"lineTo"|"stroke"|"closePath"|"fill"|"arc"|"fillText"|"fillStyle"|"strokeStyle"|"lineWidth"|"globalAlpha"|"font"|"textAlign"|"textBaseline">} DrawingContext
 */

/**
 * Screen-space glyph fields consumed without modifying the original cluster.
 * @typedef {{x: number, y: number, count: number, domain: string, accent?: string|null}} PaintedCluster
 */

/**
 * Required sizing function and optional back-to-front domain order.
 * @typedef {{radiusFor: (count: number) => number, order?: string[]}} ClusterPaintOptions
 */

/**
 * Host for the classic-script canvas-painting API.
 * @typedef {{AtlasMap?: {renderer?: typeof import("./renderer.js")}}} RendererGlobal
 */

/**
 * Publish the same canvas operations to CommonJS and the browser map namespace.
 * @param {RendererGlobal} root Browser namespace host when CommonJS is absent.
 * @param {() => typeof import("./renderer.js")} factory Canvas API builder.
 * @returns {void}
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.renderer = factory();
  }
})(
  /** @type {RendererGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Build palette lookup and canvas painters without creating a canvas.
   * @returns {RendererAPI} Canvas API shared between browser and Node consumers.
   */
  function () {
    "use strict";

    // Palette carried over from the atlas stylesheet so the map stays part of
    // the same visual system rather than becoming a foreign component.
    /**
     * API types derived from the actual palette and functions in this factory.
     * @typedef {{THEME: typeof THEME, domainColour: typeof domainColour, drawBackground: typeof drawBackground, drawGraticule: typeof drawGraticule, drawLand: typeof drawLand, drawClusters: typeof drawClusters, drawClusterLabels: typeof drawClusterLabels, drawFocus: typeof drawFocus, formatCount: typeof formatCount}} RendererAPI
     */
    var THEME = {
      ocean: "#10231f",
      land: "#36534b",
      landEdge: "#88a49b",
      graticule: "rgba(136,164,155,0.20)",
      clusterText: "#0d1a17",
      focusRing: "#d8ff63",
      /** @type {Record<string, string>} */
      domains: {
        fission: "#ff6b35",
        fusion: "#b48cff",
        chemical: "#2aaa7c",
        hybrid: "#5177d9",
        unknown: "#c9d3cf",
      },
    };

    /**
     * Resolve the colour for a domain, falling back for unknown values.
     * @param {string|null|undefined} domain Domain name; absent and unregistered names use the unknown colour.
     * @returns {string} A CSS colour.
     */
    function domainColour(domain) {
      return domain && Object.hasOwn(THEME.domains, domain)
        ? THEME.domains[domain]
        : THEME.domains.unknown;
    }

    /**
     * Paint the ocean background.
     * @param {DrawingContext} ctx Drawing context.
     * @param {{width: number, height: number}} viewport Canvas size in device-independent pixels.
     * @returns {void}
     */
    function drawBackground(ctx, viewport) {
      ctx.save();
      ctx.fillStyle = THEME.ocean;
      ctx.fillRect(0, 0, viewport.width, viewport.height);
      ctx.restore();
    }

    /**
     * Draw meridians and parallels.
     *
     * The graticule is what makes a reprojected map readable as a projection
     * rather than as an oddly shaped blob, so it is drawn beneath the land.
     * @param {DrawingContext} ctx Drawing context.
     * @param {import("./cluster.js").ScreenTransform} viewport World-to-screen conversion.
     * @param {Pick<import("./projection.js").Projection, "forward">} proj Geographic-degrees to world-plane conversion.
     * @param {number|null} [stepDegrees] Positive finite line spacing in degrees; omitted, null or zero uses 30.
     * @returns {void}
     * @throws {RangeError} If spacing is nonnumeric, nonfinite, negative or cannot advance longitude.
     */
    function drawGraticule(ctx, viewport, proj, stepDegrees) {
      var step =
        stepDegrees === undefined || stepDegrees === null || stepDegrees === 0
          ? 30
          : stepDegrees;
      if (
        typeof step !== "number" ||
        !Number.isFinite(step) ||
        step <= 0 ||
        -180 + step === -180
      ) {
        throw new RangeError(
          "Graticule spacing must be finite, positive and advance longitude.",
        );
      }
      ctx.save();
      ctx.strokeStyle = THEME.graticule;
      ctx.lineWidth = 1;
      var lon;
      var lat;
      for (lon = -180; lon <= 180; lon += step) {
        ctx.beginPath();
        for (lat = -90; lat <= 90; lat += 2) {
          var w = proj.forward(lon, lat);
          var s = viewport.toScreen(w.x, w.y);
          if (lat === -90) ctx.moveTo(s.x, s.y);
          else ctx.lineTo(s.x, s.y);
        }
        ctx.stroke();
      }
      for (lat = -60; lat <= 60; lat += step) {
        ctx.beginPath();
        for (lon = -180; lon <= 180; lon += 2) {
          var wp = proj.forward(lon, lat);
          var sp = viewport.toScreen(wp.x, wp.y);
          if (lon === -180) ctx.moveTo(sp.x, sp.y);
          else ctx.lineTo(sp.x, sp.y);
        }
        ctx.stroke();
      }
      ctx.restore();
    }

    /**
     * Draw the landmasses from geographic rings.
     * @param {DrawingContext} ctx Drawing context.
     * @param {import("./cluster.js").ScreenTransform} viewport World-to-screen conversion.
     * @param {Pick<import("./projection.js").Projection, "forward">} proj Geographic-degrees to world-plane conversion.
     * @param {Array<Array<[number, number]>>} rings Geographic rings.
     * @returns {void}
     */
    function drawLand(ctx, viewport, proj, rings) {
      ctx.save();
      ctx.fillStyle = THEME.land;
      ctx.strokeStyle = THEME.landEdge;
      ctx.lineWidth = 0.6;
      ctx.beginPath();
      for (var r = 0; r < rings.length; r += 1) {
        var ring = rings[r];
        for (var i = 0; i < ring.length; i += 1) {
          var w = proj.forward(ring[i][0], ring[i][1]);
          var s = viewport.toScreen(w.x, w.y);
          if (i === 0) ctx.moveTo(s.x, s.y);
          else ctx.lineTo(s.x, s.y);
        }
        ctx.closePath();
      }
      ctx.fill("evenodd");
      ctx.stroke();
      ctx.restore();
    }

    /**
     * Draw aggregated facility clusters.
     *
     * A cluster is filled by its majority domain, so the map reports honest
     * proportion, and ringed in its rarest domain when one is present, so a
     * single fusion device inside four hundred chemical sites still announces
     * itself. Clusters carrying a rare domain paint last. Both choices are part
     * of the map's honesty, not cosmetics.
     * @param {DrawingContext} ctx Drawing context.
     * @param {PaintedCluster[]} clusters Clusters in screen space.
     * @param {ClusterPaintOptions} options Sizing function and optional back-to-front domain order.
     * @returns {void}
     */
    function drawClusters(ctx, clusters, options) {
      var opts = options || {};
      var radiusFor = opts.radiusFor;
      var order = opts.order || [
        "chemical",
        "unknown",
        "hybrid",
        "fission",
        "fusion",
      ];
      /**
       * Rank a cluster by its accent when present, otherwise by its majority domain.
       * @param {PaintedCluster} entry Screen-space cluster.
       * @returns {number} Order index, or -1 for a domain absent from the configured order.
       */
      var rank = function (entry) {
        // Rank by the rarest domain the cluster carries, so accented clusters
        // still paint above plain ones.
        return order.indexOf(entry.accent || entry.domain);
      };
      var ranked = clusters.slice().sort(
        /**
         * Sort a copied array from lower to higher paint rank.
         * @param {PaintedCluster} a Left cluster.
         * @param {PaintedCluster} b Right cluster.
         * @returns {number} Signed rank difference; zero retains input order.
         */
        function (a, b) {
          return rank(a) - rank(b);
        },
      );
      ctx.save();
      for (var i = 0; i < ranked.length; i += 1) {
        var entry = ranked[i];
        var radius = radiusFor(entry.count);
        ctx.beginPath();
        ctx.arc(entry.x, entry.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = domainColour(entry.domain);
        ctx.globalAlpha = entry.count > 1 ? 0.88 : 1;
        ctx.fill();
        ctx.globalAlpha = 1;
        if (entry.accent) {
          // A rarer domain hides inside this cluster; ring it in that domain's
          // colour so it cannot be lost inside the majority fill.
          ctx.lineWidth = 2;
          ctx.strokeStyle = domainColour(entry.accent);
          ctx.stroke();
        } else if (entry.count > 1) {
          ctx.lineWidth = 1;
          ctx.strokeStyle = "rgba(6,18,15,0.65)";
          ctx.stroke();
        }
      }
      ctx.restore();
    }

    /**
     * Label clusters large enough to carry a readable count.
     * @param {DrawingContext} ctx Drawing context.
     * @param {PaintedCluster[]} clusters Clusters in screen space.
     * @param {function(number): number} radiusFor Radius function.
     * @returns {void}
     */
    function drawClusterLabels(ctx, clusters, radiusFor) {
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = THEME.clusterText;
      for (var i = 0; i < clusters.length; i += 1) {
        var entry = clusters[i];
        var radius = radiusFor(entry.count);
        if (entry.count < 2 || radius < 11) {
          continue;
        }
        ctx.font =
          "700 " +
          Math.max(9, Math.round(radius * 0.85)) +
          "px system-ui, sans-serif";
        ctx.fillText(formatCount(entry.count), entry.x, entry.y);
      }
      ctx.restore();
    }

    /**
     * Abbreviate a record count for display inside a glyph.
     * @param {number} count The count.
     * @returns {string} A short label.
     */
    function formatCount(count) {
      if (count >= 1000) {
        return Math.round(count / 100) / 10 + "k";
      }
      return String(count);
    }

    /**
     * Highlight the hovered or keyboard-focused entry.
     * @param {DrawingContext} ctx Drawing context.
     * @param {{x: number, y: number, count: number}|null|undefined} entry Active screen-space glyph; absence paints nothing.
     * @param {function(number): number} radiusFor Radius function.
     * @returns {void}
     */
    function drawFocus(ctx, entry, radiusFor) {
      if (!entry) {
        return;
      }
      ctx.save();
      ctx.beginPath();
      ctx.arc(entry.x, entry.y, radiusFor(entry.count) + 4, 0, Math.PI * 2);
      ctx.strokeStyle = THEME.focusRing;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    }

    return {
      THEME: THEME,
      domainColour: domainColour,
      drawBackground: drawBackground,
      drawGraticule: drawGraticule,
      drawLand: drawLand,
      drawClusters: drawClusters,
      drawClusterLabels: drawClusterLabels,
      drawFocus: drawFocus,
      formatCount: formatCount,
    };
  },
);
