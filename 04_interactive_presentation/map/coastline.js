// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — recover geographic coastline rings from the SVG basemap.

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.coastline = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // The bundled basemap path is authored in a 1000x500 viewBox whose axes are
  // a plate carrée graticule. That projection is exactly invertible, so the
  // original longitude and latitude are recoverable without shipping any
  // additional geometry — which also keeps the atlas free of a new
  // third-party data licence.
  var VIEW_WIDTH = 1000;
  var VIEW_HEIGHT = 500;

  /**
   * Convert a viewBox coordinate pair back to geographic degrees.
   *
   * @param {number} x Horizontal viewBox coordinate, 0..1000.
   * @param {number} y Vertical viewBox coordinate, 0..500, increasing south.
   * @param {number} [width] View width, for non-default basemaps.
   * @param {number} [height] View height, for non-default basemaps.
   * @returns {[number, number]} Longitude and latitude in degrees.
   */
  function toGeographic(x, y, width, height) {
    var w = width || VIEW_WIDTH;
    var h = height || VIEW_HEIGHT;
    return [(x / w) * 360 - 180, 90 - (y / h) * 180];
  }

  /**
   * Parse an SVG path of absolute move/line/close commands into rings.
   *
   * The basemap path uses only ``M``, ``L`` and ``Z``; any other command
   * would silently distort the coastline, so encountering one is an error
   * rather than something to skip.
   *
   * @param {string} d The path's ``d`` attribute.
   * @param {object} [options] Optional ``width`` and ``height`` overrides.
   * @returns {Array<Array<[number, number]>>} Rings of geographic points.
   * @throws {Error} When the path contains an unsupported command.
   */
  function parsePath(d, options) {
    if (typeof d !== "string" || d.trim() === "") {
      throw new Error("coastline: empty path data");
    }
    var opts = options || {};
    var unsupported = d.match(/[^MLZmlz0-9.,\-\s]/);
    if (unsupported) {
      throw new Error(
        "coastline: unsupported path command '" + unsupported[0] + "'",
      );
    }
    var rings = [];
    var current = null;
    var tokens = d.match(/[MLZmlz]|-?\d*\.?\d+/g) || [];
    var i = 0;
    while (i < tokens.length) {
      var token = tokens[i];
      if (token === "M" || token === "m" || token === "L" || token === "l") {
        i += 1;
        var x = Number(tokens[i]);
        var y = Number(tokens[i + 1]);
        i += 2;
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
          throw new Error("coastline: malformed coordinate pair");
        }
        if (token === "M" || token === "m") {
          current = [];
          rings.push(current);
        }
        if (current === null) {
          throw new Error("coastline: line command before any move");
        }
        current.push(toGeographic(x, y, opts.width, opts.height));
      } else if (token === "Z" || token === "z") {
        current = null;
        i += 1;
      } else {
        // A bare coordinate pair continues the previous command, which for
        // this basemap is always an implicit line-to.
        var px = Number(tokens[i]);
        var py = Number(tokens[i + 1]);
        i += 2;
        if (!Number.isFinite(px) || !Number.isFinite(py)) {
          throw new Error("coastline: malformed implicit coordinate pair");
        }
        if (current === null) {
          throw new Error("coastline: coordinates before any move");
        }
        current.push(toGeographic(px, py, opts.width, opts.height));
      }
    }
    return rings.filter(function (ring) {
      return ring.length >= 3;
    });
  }

  /**
   * Read the basemap path out of a DOM document.
   *
   * @param {Document} doc A document containing the basemap SVG.
   * @param {string} [selector] CSS selector for the land path.
   * @returns {Array<Array<[number, number]>>} Rings of geographic points.
   * @throws {Error} When the basemap path is absent.
   */
  function fromDocument(doc, selector) {
    var node = doc.querySelector(selector || "path.land");
    if (!node) {
      throw new Error("coastline: basemap path not found");
    }
    return parsePath(node.getAttribute("d"));
  }

  /**
   * Compute the geographic bounding box of a set of rings.
   *
   * @param {Array<Array<[number, number]>>} rings Rings of points.
   * @returns {{minLon: number, minLat: number, maxLon: number, maxLat: number}}
   *   The bounding box.
   */
  function boundsOf(rings) {
    var minLon = Infinity;
    var minLat = Infinity;
    var maxLon = -Infinity;
    var maxLat = -Infinity;
    rings.forEach(function (ring) {
      ring.forEach(function (point) {
        if (point[0] < minLon) minLon = point[0];
        if (point[0] > maxLon) maxLon = point[0];
        if (point[1] < minLat) minLat = point[1];
        if (point[1] > maxLat) maxLat = point[1];
      });
    });
    return { minLon: minLon, minLat: minLat, maxLon: maxLon, maxLat: maxLat };
  }

  return {
    parsePath: parsePath,
    fromDocument: fromDocument,
    toGeographic: toGeographic,
    boundsOf: boundsOf,
  };
});
