// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — map projections for the facility canvas engine.

/**
 * Geographic projection with an explicit forward and inverse coordinate contract.
 * @typedef {object} Projection
 * @property {string} id Stable projection identifier.
 * @property {string} label Display name.
 * @property {boolean} equalArea Whether the projection preserves relative area.
 * @property {(lon: number, lat: number) => {x: number, y: number}} forward Degrees to plane units.
 * @property {(x: number, y: number) => {lon: number, lat: number}} inverse Plane units to degrees.
 */

/**
 * Public projection registry exported to Node and the classic-script map namespace.
 * @typedef {object} ProjectionAPI
 * @property {Projection} plateCarree Exactly invertible equirectangular projection.
 * @property {Projection} equalEarth Equal-area map projection.
 * @property {(id: string) => Projection} get Lookup, refusing an unregistered identifier.
 * @property {(proj: Projection, step?: number) => {minX: number, minY: number, maxX: number, maxY: number}} bounds Sampled graticule extent.
 * @property {() => Projection[]} list All registered projections in insertion order.
 */

/**
 * Host object for the browser map namespace; Node uses its own module export.
 * @typedef {object} MapGlobal
 * @property {{projection?: ProjectionAPI}} [AtlasMap] Classic-script map namespace.
 */

/**
 * Publish the same projection API to Node or the classic-script browser namespace.
 * @param {MapGlobal} root Namespace host used when CommonJS is unavailable.
 * @param {() => ProjectionAPI} factory Builder for the projection registry.
 * @returns {void}
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.projection = factory();
  }
})(
  /** @type {MapGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Construct both native projection implementations and their public registry.
   * @returns {ProjectionAPI} Coordinate transforms, lookup, sampled bounds and enumeration.
   */
  function () {
    "use strict";

    var DEG = Math.PI / 180;

    /**
     * Plate carrée (equirectangular) projection.
     *
     * Longitude and latitude map linearly onto x and y. This is the projection
     * the original SVG basemap was authored in, so it is also the inverse used
     * to recover true coordinates from that pre-projected geometry.
     *
     * Not equal-area: high-latitude regions are stretched east–west. Retained
     * because it is exactly invertible and is the source geometry's own frame.
     */
    var plateCarree = {
      id: "plate-carree",
      label: "Plate carrée",
      equalArea: false,
      /**
       * Project geographic coordinates to projected plane units.
       * @param {number} lon Longitude in degrees, -180..180.
       * @param {number} lat Latitude in degrees, -90..90.
       * @returns {{x: number, y: number}} Plane coordinates; x in -pi..pi,
       *   y in -pi/2..pi/2, y increasing northward.
       */
      forward: function (lon, lat) {
        return { x: lon * DEG, y: lat * DEG };
      },
      /**
       * Invert plane coordinates back to geographic degrees.
       * @param {number} x Plane x.
       * @param {number} y Plane y.
       * @returns {{lon: number, lat: number}} Geographic coordinates in degrees.
       */
      inverse: function (x, y) {
        return { lon: x / DEG, lat: y / DEG };
      },
    };

    // Equal Earth coefficients (Šavrič, Patterson & Jenny, 2018).
    var A1 = 1.340264;
    var A2 = -0.081106;
    var A3 = 0.000893;
    var A4 = 0.003796;
    var M = Math.sqrt(3) / 2;

    /**
     * Derivative dy/dtheta of the Equal Earth northing polynomial.
     *
     * The easting denominator must be exactly this derivative for the
     * projection to be equal-area; deriving it here rather than restating a
     * separate constant keeps the two halves of the projection consistent.
     * @param {number} t Parametric latitude theta, in radians.
     * @returns {number} dy/dtheta at t.
     */
    function northingDerivative(t) {
      var t2 = t * t;
      var t8 = t2 * t2 * t2 * t2;
      var t10 = t8 * t2;
      return A1 + 3 * A2 * t2 + 9 * A3 * t8 + 11 * A4 * t10;
    }

    /**
     * Equal Earth projection.
     *
     * An equal-area pseudocylindrical projection: every projected region
     * preserves its true relative area, so visual density on the map is
     * honest density on the globe. That property is the reason it is the
     * atlas default — a facility map whose dense regions are area-distorted
     * would misrepresent concentration.
     *
     * Reference: Šavrič, B., Patterson, T. & Jenny, B. (2018),
     * "The Equal Earth map projection", International Journal of
     * Geographical Information Science.
     */
    var equalEarth = {
      id: "equal-earth",
      label: "Equal Earth",
      equalArea: true,
      /**
       * Project geographic coordinates to projected plane units.
       * @param {number} lon Longitude in degrees, -180..180.
       * @param {number} lat Latitude in degrees, -90..90.
       * @returns {{x: number, y: number}} Plane coordinates, y increasing
       *   northward.
       */
      forward: function (lon, lat) {
        var theta = Math.asin(M * Math.sin(lat * DEG));
        var t2 = theta * theta;
        var t3 = t2 * theta;
        var t9 = t3 * t3 * t3;
        var t11 = t9 * t2;
        return {
          x: (lon * DEG * Math.cos(theta)) / (M * northingDerivative(theta)),
          y: A1 * theta + A2 * t3 + A3 * t9 + A4 * t11,
        };
      },
      /**
       * Invert plane coordinates back to geographic degrees.
       *
       * The northing polynomial has no closed-form inverse, so theta is
       * recovered by Newton–Raphson. The iteration is seeded with y and
       * converges to double precision well inside the iteration cap for every
       * latitude in range.
       * @param {number} x Plane x.
       * @param {number} y Plane y.
       * @returns {{lon: number, lat: number}} Geographic coordinates in degrees.
       */
      inverse: function (x, y) {
        var theta = y;
        for (var i = 0; i < 24; i += 1) {
          var t2 = theta * theta;
          var t3 = t2 * theta;
          var t9 = t3 * t3 * t3;
          var t11 = t9 * t2;
          var f = A1 * theta + A2 * t3 + A3 * t9 + A4 * t11 - y;
          var step = f / northingDerivative(theta);
          theta -= step;
          if (Math.abs(step) < 1e-14) {
            break;
          }
        }
        var lat = Math.asin(Math.sin(theta) / M) / DEG;
        var lon = (x * M * northingDerivative(theta)) / Math.cos(theta) / DEG;
        return { lon: lon, lat: lat };
      },
    };

    /** @type {Record<string, Projection>} */
    var registry = {};
    registry[plateCarree.id] = plateCarree;
    registry[equalEarth.id] = equalEarth;

    /**
     * Look a projection up by identifier.
     * @param {string} id Projection identifier, e.g. "equal-earth".
     * @returns {Projection} The registered projection.
     * @throws {Error} When no projection is registered under that identifier.
     */
    function get(id) {
      if (!Object.hasOwn(registry, id)) {
        throw new Error("unknown projection: " + id);
      }
      return registry[id];
    }

    /**
     * Compute the projected bounding box of the whole graticule.
     *
     * Sampled rather than assumed, so a newly registered projection reports
     * correct bounds without additional bookkeeping.
     * @param {Projection} proj Geographic projection to sample.
     * @param {number} [step] Positive sampling step in degrees; omitted or zero uses one degree.
     * @returns {{minX: number, minY: number, maxX: number, maxY: number}} Bounds.
     */
    function bounds(proj, step) {
      var s = step || 1;
      var minX = Infinity;
      var minY = Infinity;
      var maxX = -Infinity;
      var maxY = -Infinity;
      for (var lat = -90; lat <= 90; lat += s) {
        for (var lon = -180; lon <= 180; lon += s) {
          var p = proj.forward(lon, lat);
          if (p.x < minX) minX = p.x;
          if (p.x > maxX) maxX = p.x;
          if (p.y < minY) minY = p.y;
          if (p.y > maxY) maxY = p.y;
        }
      }
      return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
    }

    return {
      plateCarree: plateCarree,
      equalEarth: equalEarth,
      get: get,
      bounds: bounds,
      /**
       * Enumerate the registered projections in insertion order.
       * @returns {Projection[]} Both registered coordinate transforms.
       */
      list: function () {
        return Object.keys(registry).map(
          /**
           * Resolve a key enumerated directly from the projection registry.
           * @param {string} k Registered projection identifier.
           * @returns {Projection} Projection stored at the enumerated key.
           */
          function (k) {
            return registry[k];
          },
        );
      },
    };
  },
);
