// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — point quadtree for viewport culling and hit testing.

/**
 * Planar coordinates required for spatial indexing; payload fields remain on the original object.
 * @typedef {{x: number, y: number}} PlanarPoint
 */

/**
 * Axis-aligned planar extent with distinct minimum and maximum coordinates.
 * @typedef {{minX: number, minY: number, maxX: number, maxY: number}} Rectangle
 */

/**
 * Host for the classic-script spatial index constructor.
 * @typedef {object} QuadtreeGlobal
 * @property {{Quadtree?: typeof import("./quadtree.js")}} [AtlasMap] Browser map namespace.
 */

/**
 * Publish the same spatial-index constructor to Node or the classic-script namespace.
 * @param {QuadtreeGlobal} root Namespace host when CommonJS is unavailable.
 * @param {() => typeof import("./quadtree.js")} factory Spatial-index constructor builder.
 * @returns {void}
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.Quadtree = factory();
  }
})(
  /** @type {QuadtreeGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Build a payload-preserving spatial index with bounded subdivision depth.
   * @returns {QuadtreeConstructor} Quadtree constructor with its bulk-build entry point.
   */
  function () {
    "use strict";

    /**
     * Constructor type derived from the actual generic index declared in this factory.
     * @typedef {typeof Quadtree} QuadtreeConstructor
     */
    var DEFAULT_CAPACITY = 16;
    var MAX_DEPTH = 24;

    /**
     * Axis-aligned quadtree over planar points.
     *
     * Linear scans are adequate for a few hundred points but not for the
     * thirteen thousand the atlas carries: culling and hover hit-testing both
     * run on every animation frame, so both need to be sublinear.
     * @template {PlanarPoint} [Point=PlanarPoint]
     * @param {Rectangle|null} bounds
     *   The region the tree covers.
     * @param {number} [capacity] Points held in a node before it subdivides.
     * @param {number} [depth] Internal recursion depth.
     * @class
     */
    function Quadtree(bounds, capacity, depth) {
      if (
        !bounds ||
        !(bounds.maxX > bounds.minX) ||
        !(bounds.maxY > bounds.minY)
      ) {
        throw new Error("quadtree: bounds must be a non-degenerate rectangle");
      }
      this.bounds = bounds;
      this.capacity = capacity || DEFAULT_CAPACITY;
      this.depth = depth || 0;
      /** @type {Point[]} */
      this.points = [];
      /** @type {Quadtree<Point>[]|null} */
      this.children = null;
      this.size = 0;
    }

    /**
     * Split this node into four quadrants and redistribute its points.
     * @returns {void}
     */
    Quadtree.prototype.subdivide = function () {
      var b = this.bounds;
      var midX = (b.minX + b.maxX) / 2;
      var midY = (b.minY + b.maxY) / 2;
      var next = this.depth + 1;
      this.children = [
        new Quadtree(
          { minX: b.minX, minY: midY, maxX: midX, maxY: b.maxY },
          this.capacity,
          next,
        ),
        new Quadtree(
          { minX: midX, minY: midY, maxX: b.maxX, maxY: b.maxY },
          this.capacity,
          next,
        ),
        new Quadtree(
          { minX: b.minX, minY: b.minY, maxX: midX, maxY: midY },
          this.capacity,
          next,
        ),
        new Quadtree(
          { minX: midX, minY: b.minY, maxX: b.maxX, maxY: midY },
          this.capacity,
          next,
        ),
      ];
      var held = this.points;
      this.points = [];
      for (var i = 0; i < held.length; i += 1) {
        this.insertIntoChild(held[i]);
      }
    };

    /**
     * Place a point into whichever child quadrant contains it.
     * @param {this["points"][number]} point Original point and payload retained by the child.
     * @returns {boolean} True when a child accepted the point.
     * @throws {TypeError} When called before this node has been subdivided.
     */
    Quadtree.prototype.insertIntoChild = function (point) {
      for (
        var i = 0;
        i <
        /** @type {NonNullable<typeof this.children>} */ (this.children).length;
        i += 1
      ) {
        if (
          /** @type {NonNullable<typeof this.children>} */ (this.children)[
            i
          ].insert(point)
        ) {
          return true;
        }
      }
      // Retain a point here if no child accepts it, preserving its payload
      // even when the caller supplies coordinates outside the quadrants.
      this.points.push(point);
      return true;
    };

    /**
     * Test whether a point falls inside this node's bounds.
     * @param {PlanarPoint} point Planar coordinates to compare with inclusive node bounds.
     * @returns {boolean} True when contained.
     */
    Quadtree.prototype.contains = function (point) {
      var b = this.bounds;
      return (
        point.x >= b.minX &&
        point.x <= b.maxX &&
        point.y >= b.minY &&
        point.y <= b.maxY
      );
    };

    /**
     * Insert a point.
     * @param {this["points"][number]} point Original planar point carrying its preserved payload.
     * @returns {boolean} True when the point was stored.
     */
    Quadtree.prototype.insert = function (point) {
      if (!this.contains(point)) {
        return false;
      }
      this.size += 1;
      if (this.children === null) {
        if (this.points.length < this.capacity || this.depth >= MAX_DEPTH) {
          this.points.push(point);
          return true;
        }
        this.subdivide();
      }
      return this.insertIntoChild(point);
    };

    /**
     * Collect every point inside a rectangle.
     * @param {Rectangle} range
     *   The query rectangle.
     * @param {this["points"]} [into] Optional matching-point array to append into.
     * @returns {this["points"]} Matching original point objects with their payloads.
     */
    Quadtree.prototype.query = function (range, into) {
      /** @type {typeof this.points} */
      var found = into || [];
      var b = this.bounds;
      if (
        range.minX > b.maxX ||
        range.maxX < b.minX ||
        range.minY > b.maxY ||
        range.maxY < b.minY
      ) {
        return found;
      }
      for (var i = 0; i < this.points.length; i += 1) {
        var p = this.points[i];
        if (
          p.x >= range.minX &&
          p.x <= range.maxX &&
          p.y >= range.minY &&
          p.y <= range.maxY
        ) {
          found.push(p);
        }
      }
      if (this.children !== null) {
        for (var c = 0; c < this.children.length; c += 1) {
          this.children[c].query(range, found);
        }
      }
      return found;
    };

    /**
     * Find the point nearest to a location within a search radius.
     * @param {number} x Query x.
     * @param {number} y Query y.
     * @param {number} radius Maximum distance to consider.
     * @returns {this["points"][number]|null} Nearest original point, or null when none is in range.
     */
    Quadtree.prototype.nearest = function (x, y, radius) {
      var candidates = this.query({
        minX: x - radius,
        minY: y - radius,
        maxX: x + radius,
        maxY: y + radius,
      });
      var best = null;
      var bestDistance = radius * radius;
      for (var i = 0; i < candidates.length; i += 1) {
        var dx = candidates[i].x - x;
        var dy = candidates[i].y - y;
        var d2 = dx * dx + dy * dy;
        if (d2 <= bestDistance) {
          bestDistance = d2;
          best = candidates[i];
        }
      }
      return best;
    };

    /**
     * Build a quadtree from points, sizing the root to fit them.
     * @template {PlanarPoint} [Point=PlanarPoint]
     * @param {Point[]|null} points Original points to index; null or empty input creates an empty tree.
     * @param {number} [capacity] Node capacity.
     * @returns {Quadtree<Point>} Populated index retaining the original point payload type.
     */
    Quadtree.build = function (points, capacity) {
      if (!points || points.length === 0) {
        return new Quadtree({ minX: -1, minY: -1, maxX: 1, maxY: 1 }, capacity);
      }
      var minX = Infinity;
      var minY = Infinity;
      var maxX = -Infinity;
      var maxY = -Infinity;
      for (var i = 0; i < points.length; i += 1) {
        if (points[i].x < minX) minX = points[i].x;
        if (points[i].x > maxX) maxX = points[i].x;
        if (points[i].y < minY) minY = points[i].y;
        if (points[i].y > maxY) maxY = points[i].y;
      }
      // A collection sharing one coordinate would produce a degenerate root.
      var padX = (maxX - minX) * 0.01 || 1;
      var padY = (maxY - minY) * 0.01 || 1;
      /** @type {Quadtree<Point>} */
      var tree = new Quadtree(
        {
          minX: minX - padX,
          minY: minY - padY,
          maxX: maxX + padX,
          maxY: maxY + padY,
        },
        capacity,
      );
      for (var j = 0; j < points.length; j += 1) {
        tree.insert(points[j]);
      }
      return tree;
    };

    return Quadtree;
  },
);
