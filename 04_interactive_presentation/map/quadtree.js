// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — point quadtree for viewport culling and hit testing.

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.Quadtree = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var DEFAULT_CAPACITY = 16;
  var MAX_DEPTH = 24;

  /**
   * Axis-aligned quadtree over planar points.
   *
   * Linear scans are adequate for a few hundred points but not for the
   * thirteen thousand the atlas carries: culling and hover hit-testing both
   * run on every animation frame, so both need to be sublinear.
   *
   * @param {{minX: number, minY: number, maxX: number, maxY: number}} bounds
   *   The region the tree covers.
   * @param {number} [capacity] Points held in a node before it subdivides.
   * @param {number} [depth] Internal recursion depth.
   * @constructor
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
    this.points = [];
    this.children = null;
    this.size = 0;
  }

  /**
   * Split this node into four quadrants and redistribute its points.
   *
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
   *
   * @param {{x: number, y: number}} point The point to place.
   * @returns {boolean} True when a child accepted the point.
   */
  Quadtree.prototype.insertIntoChild = function (point) {
    for (var i = 0; i < this.children.length; i += 1) {
      if (this.children[i].insert(point)) {
        return true;
      }
    }
    // Points exactly on an internal boundary can fail every child's
    // half-open containment test; keeping them here rather than dropping
    // them guarantees insertion never loses data.
    this.points.push(point);
    return true;
  };

  /**
   * Test whether a point falls inside this node's bounds.
   *
   * @param {{x: number, y: number}} point The point to test.
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
   *
   * @param {{x: number, y: number}} point A point carrying any extra payload.
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
   *
   * @param {{minX: number, minY: number, maxX: number, maxY: number}} range
   *   The query rectangle.
   * @param {Array} [into] Optional array to append into.
   * @returns {Array} The matching points.
   */
  Quadtree.prototype.query = function (range, into) {
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
   *
   * @param {number} x Query x.
   * @param {number} y Query y.
   * @param {number} radius Maximum distance to consider.
   * @returns {object|null} The nearest point, or null when none is in range.
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
   *
   * @param {Array<{x: number, y: number}>} points The points to index.
   * @param {number} [capacity] Node capacity.
   * @returns {Quadtree} The populated tree.
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
});
