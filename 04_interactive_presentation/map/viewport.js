// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — viewport transform, zoom and pan state for the map canvas.

/**
 * Nondegenerate projected world extent used by fit, clamping and visible-region transforms.
 * @typedef {{minX: number, minY: number, maxX: number, maxY: number}} ViewportBounds
 */

/**
 * Canvas dimensions, projected bounds and supported zoom interval.
 * @typedef {object} ViewportOptions
 * @property {number} [width] Canvas width in device-independent pixels.
 * @property {number} [height] Canvas height in device-independent pixels.
 * @property {ViewportBounds} [world] Projected world rectangle.
 * @property {number} [minZoom] Minimum configured zoom; defaults to one.
 * @property {number} [maxZoom] Maximum configured zoom; defaults to sixty-four.
 */

/**
 * Host for the classic-script viewport constructor.
 * @typedef {object} ViewportGlobal
 * @property {{Viewport?: typeof import("./viewport.js")}} [AtlasMap] Browser map namespace.
 */

/**
 * Publish the same world/screen viewport constructor to Node or the browser namespace.
 * @param {ViewportGlobal} root Namespace host when CommonJS is unavailable.
 * @param {() => typeof import("./viewport.js")} factory Viewport constructor builder.
 * @returns {void}
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.Viewport = factory();
  }
})(
  /** @type {ViewportGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Build the viewport constructor with fit, coordinate, pan, zoom and clamping operations.
   * @returns {ViewportConstructor} Constructor for the projected-world viewport.
   */
  function () {
    "use strict";

    /**
     * Constructor type derived from the actual viewport declared in this factory.
     * @typedef {typeof Viewport} ViewportConstructor
     */

    /**
     * Two-dimensional viewport mapping projected world units to screen pixels.
     * @param {ViewportOptions|null} [options] Canvas dimensions, world bounds and zoom limits.
     * @class
     */
    function Viewport(options) {
      var opts = options || {};
      this.width = opts.width || 1;
      this.height = opts.height || 1;
      this.world = opts.world || { minX: -1, minY: -1, maxX: 1, maxY: 1 };
      this.minZoom = opts.minZoom || 1;
      this.maxZoom = opts.maxZoom || 64;
      this.zoom = Math.min(this.maxZoom, Math.max(this.minZoom, 1));
      this.centreX = (this.world.minX + this.world.maxX) / 2;
      this.centreY = (this.world.minY + this.world.maxY) / 2;
      this.baseScale = 1;
      this.resize(this.width, this.height);
    }

    /**
     * Recompute the fit-to-world scale for a new canvas size.
     * @param {number} width Canvas width in device-independent pixels.
     * @param {number} height Canvas height in device-independent pixels.
     * @returns {void}
     */
    Viewport.prototype.resize = function (width, height) {
      this.width = Math.max(1, width);
      this.height = Math.max(1, height);
      var worldWidth = this.world.maxX - this.world.minX;
      var worldHeight = this.world.maxY - this.world.minY;
      // Fit the whole world, preserving aspect ratio: the smaller of the two
      // ratios leaves letterboxing rather than cropping the map.
      this.baseScale = Math.min(
        this.width / worldWidth,
        this.height / worldHeight,
      );
      this.clampCentre();
    };

    /**
     * Current world-to-screen scale factor.
     * @returns {number} Pixels per world unit.
     */
    Viewport.prototype.scale = function () {
      return this.baseScale * this.zoom;
    };

    /**
     * Convert world coordinates to screen pixels.
     * @param {number} x World x.
     * @param {number} y World y, increasing northward.
     * @returns {{x: number, y: number}} Screen position, y increasing downward.
     */
    Viewport.prototype.toScreen = function (x, y) {
      var s = this.scale();
      return {
        x: (x - this.centreX) * s + this.width / 2,
        y: (this.centreY - y) * s + this.height / 2,
      };
    };

    /**
     * Convert screen pixels back to world coordinates.
     * @param {number} px Screen x.
     * @param {number} py Screen y.
     * @returns {{x: number, y: number}} World position.
     */
    Viewport.prototype.toWorld = function (px, py) {
      var s = this.scale();
      return {
        x: (px - this.width / 2) / s + this.centreX,
        y: this.centreY - (py - this.height / 2) / s,
      };
    };

    /**
     * The world rectangle currently visible, expanded by a margin.
     * @param {number} [marginPx] Extra margin in pixels, to avoid pop-in.
     * @returns {{minX: number, minY: number, maxX: number, maxY: number}} Bounds.
     */
    Viewport.prototype.visibleWorld = function (marginPx) {
      var m = marginPx || 0;
      var topLeft = this.toWorld(-m, -m);
      var bottomRight = this.toWorld(this.width + m, this.height + m);
      return {
        minX: Math.min(topLeft.x, bottomRight.x),
        maxX: Math.max(topLeft.x, bottomRight.x),
        minY: Math.min(topLeft.y, bottomRight.y),
        maxY: Math.max(topLeft.y, bottomRight.y),
      };
    };

    /**
     * Keep the centre such that the map cannot be panned off screen.
     * @returns {void}
     */
    Viewport.prototype.clampCentre = function () {
      var s = this.scale();
      var halfWorldW = this.width / 2 / s;
      var halfWorldH = this.height / 2 / s;
      var worldW = this.world.maxX - this.world.minX;
      var worldH = this.world.maxY - this.world.minY;
      if (halfWorldW * 2 >= worldW) {
        this.centreX = (this.world.minX + this.world.maxX) / 2;
      } else {
        this.centreX = Math.min(
          Math.max(this.centreX, this.world.minX + halfWorldW),
          this.world.maxX - halfWorldW,
        );
      }
      if (halfWorldH * 2 >= worldH) {
        this.centreY = (this.world.minY + this.world.maxY) / 2;
      } else {
        this.centreY = Math.min(
          Math.max(this.centreY, this.world.minY + halfWorldH),
          this.world.maxY - halfWorldH,
        );
      }
    };

    /**
     * Pan by a screen-space delta.
     * @param {number} dxPx Horizontal movement in pixels.
     * @param {number} dyPx Vertical movement in pixels.
     * @returns {void}
     */
    Viewport.prototype.panBy = function (dxPx, dyPx) {
      var s = this.scale();
      this.centreX -= dxPx / s;
      this.centreY += dyPx / s;
      this.clampCentre();
    };

    /**
     * Zoom about a fixed screen point before clamping the visible world extent.
     * @param {number} factor Multiplicative zoom change.
     * @param {number} px Screen x to hold fixed.
     * @param {number} py Screen y to hold fixed.
     * @returns {void}
     */
    Viewport.prototype.zoomAbout = function (factor, px, py) {
      var before = this.toWorld(px, py);
      this.zoom = Math.min(
        this.maxZoom,
        Math.max(this.minZoom, this.zoom * factor),
      );
      var after = this.toWorld(px, py);
      this.centreX += before.x - after.x;
      this.centreY += before.y - after.y;
      this.clampCentre();
    };

    /**
     * Reset to the full-world view.
     * @returns {void}
     */
    Viewport.prototype.reset = function () {
      this.zoom = this.minZoom;
      this.centreX = (this.world.minX + this.world.maxX) / 2;
      this.centreY = (this.world.minY + this.world.maxY) / 2;
      this.clampCentre();
    };

    /**
     * Centre the view on a world position at a given zoom.
     * @param {number} x World x.
     * @param {number} y World y.
     * @param {number} [zoom] Desired zoom level.
     * @returns {void}
     */
    Viewport.prototype.centreOn = function (x, y, zoom) {
      if (zoom !== undefined) {
        this.zoom = Math.min(this.maxZoom, Math.max(this.minZoom, zoom));
      }
      this.centreX = x;
      this.centreY = y;
      this.clampCentre();
    };

    return Viewport;
  },
);
