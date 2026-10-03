// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — canvas map engine orchestration and interaction.

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory(
      require("./projection.js"),
      require("./coastline.js"),
      require("./quadtree.js"),
      require("./cluster.js"),
      require("./viewport.js"),
      require("./renderer.js"),
    );
  } else {
    var ns = (root.AtlasMap = root.AtlasMap || {});
    ns.MapEngine = factory(
      ns.projection,
      ns.coastline,
      ns.Quadtree,
      ns.cluster,
      ns.Viewport,
      ns.renderer,
    );
  }
})(typeof self !== "undefined" ? self : this, function (
  projection,
  coastline,
  Quadtree,
  cluster,
  Viewport,
  renderer,
) {
  "use strict";

  var CLUSTER_CELL_PX = 30;
  // Glyphs must stay inside their own cell, or neighbouring clusters overlap
  // and their count labels render on top of one another.
  var CLUSTER_MAX_RADIUS_PX = CLUSTER_CELL_PX * 0.48;
  var POINT_RADIUS_PX = 3.4;
  var HIT_RADIUS_PX = 14;
  var KEYBOARD_LIST_LIMIT = 200;

  /**
   * Parse a facility row into a projectable record.
   *
   * Rows missing usable coordinates are rejected here rather than being
   * drawn at latitude zero, which would invent a location the source never
   * supplied.
   *
   * @param {object} row A facility record.
   * @returns {{lon: number, lat: number}|null} Coordinates, or null.
   */
  function coordinatesOf(row) {
    if (row.lon === null || row.lon === undefined || row.lon === "") return null;
    if (row.lat === null || row.lat === undefined || row.lat === "") return null;
    var lon = Number(row.lon);
    var lat = Number(row.lat);
    if (!Number.isFinite(lon) || !Number.isFinite(lat)) return null;
    if (lon < -180 || lon > 180 || lat < -90 || lat > 90) return null;
    return { lon: lon, lat: lat };
  }

  /**
   * Canvas-backed facility map.
   *
   * @param {object} options Container, coastline rings and callbacks.
   * @constructor
   */
  function MapEngine(options) {
    var opts = options || {};
    this.radiusFor = function (count) {
      return cluster.radiusFor(count, POINT_RADIUS_PX, CLUSTER_MAX_RADIUS_PX);
    };
    if (!opts.container) {
      throw new Error("map engine: a container element is required");
    }
    this.container = opts.container;
    this.document = opts.document || (opts.container.ownerDocument || null);
    this.onSelect = opts.onSelect || function () {};
    this.onViewChange = opts.onViewChange || function () {};
    this.projection = projection.get(opts.projection || "equal-earth");
    this.rings = opts.rings || [];
    this.rows = [];
    this.points = [];
    this.tree = null;
    this.clusters = [];
    this.focus = null;
    this.frame = null;
    this.reducedMotion = Boolean(opts.reducedMotion);
    this.world = projection.bounds(this.projection, 4);
    this.viewport = new Viewport({
      width: 1,
      height: 1,
      world: this.world,
      maxZoom: opts.maxZoom || 48,
    });
    this.build();
  }

  /**
   * Create the canvas and the parallel accessible list.
   *
   * @returns {void}
   */
  MapEngine.prototype.build = function () {
    var doc = this.document;
    this.canvas = doc.createElement("canvas");
    this.canvas.className = "atlas-map-canvas";
    this.canvas.setAttribute("role", "application");
    this.canvas.setAttribute("tabindex", "0");
    this.canvas.setAttribute(
      "aria-label",
      "Interactive map of reactor sites. Use arrow keys to pan, plus and minus to zoom, " +
        "Tab to move through records, and Enter to open the focused record.",
    );
    this.container.appendChild(this.canvas);

    // A canvas is opaque to assistive technology, so every record is also
    // exposed as a real focusable button in a visually hidden list. This is
    // the path the previous implementation removed above 500 records.
    this.srList = doc.createElement("ul");
    this.srList.className = "atlas-map-sr-list sr-only";
    this.container.appendChild(this.srList);

    this.status = doc.createElement("p");
    this.status.className = "atlas-map-status";
    this.status.setAttribute("aria-live", "polite");
    this.container.appendChild(this.status);

    this.ctx = this.canvas.getContext ? this.canvas.getContext("2d") : null;
    this.attachEvents();
  };

  /**
   * Wire pointer, wheel and keyboard interaction.
   *
   * @returns {void}
   */
  MapEngine.prototype.attachEvents = function () {
    var self = this;
    var dragging = false;
    var lastX = 0;
    var lastY = 0;

    this.canvas.addEventListener("pointerdown", function (event) {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      if (self.canvas.setPointerCapture) {
        self.canvas.setPointerCapture(event.pointerId);
      }
    });

    this.canvas.addEventListener("pointermove", function (event) {
      var rect = self.canvas.getBoundingClientRect();
      if (dragging) {
        self.viewport.panBy(event.clientX - lastX, event.clientY - lastY);
        lastX = event.clientX;
        lastY = event.clientY;
        self.requestDraw();
        return;
      }
      self.setFocusFromScreen(event.clientX - rect.left, event.clientY - rect.top);
    });

    this.canvas.addEventListener("pointerup", function () {
      dragging = false;
    });
    this.canvas.addEventListener("pointercancel", function () {
      dragging = false;
    });

    this.canvas.addEventListener("click", function (event) {
      var rect = self.canvas.getBoundingClientRect();
      self.activateAt(event.clientX - rect.left, event.clientY - rect.top);
    });

    this.canvas.addEventListener(
      "wheel",
      function (event) {
        event.preventDefault();
        var rect = self.canvas.getBoundingClientRect();
        var factor = Math.exp(-event.deltaY * 0.0015);
        self.viewport.zoomAbout(factor, event.clientX - rect.left, event.clientY - rect.top);
        self.requestDraw();
      },
      { passive: false },
    );

    this.canvas.addEventListener("keydown", function (event) {
      self.handleKey(event);
    });
  };

  /**
   * Handle keyboard panning, zooming and record activation.
   *
   * @param {KeyboardEvent} event The key event.
   * @returns {void}
   */
  MapEngine.prototype.handleKey = function (event) {
    var step = event.shiftKey ? 120 : 40;
    var handled = true;
    switch (event.key) {
      case "ArrowLeft":
        this.viewport.panBy(step, 0);
        break;
      case "ArrowRight":
        this.viewport.panBy(-step, 0);
        break;
      case "ArrowUp":
        this.viewport.panBy(0, step);
        break;
      case "ArrowDown":
        this.viewport.panBy(0, -step);
        break;
      case "+":
      case "=":
        this.viewport.zoomAbout(1.4, this.viewport.width / 2, this.viewport.height / 2);
        break;
      case "-":
      case "_":
        this.viewport.zoomAbout(1 / 1.4, this.viewport.width / 2, this.viewport.height / 2);
        break;
      case "0":
        this.viewport.reset();
        break;
      case "Enter":
      case " ":
        if (this.focus) {
          this.emitSelection(this.focus);
        }
        break;
      default:
        handled = false;
    }
    if (handled) {
      event.preventDefault();
      this.requestDraw();
    }
  };

  /**
   * Replace the rendered dataset.
   *
   * @param {Array<object>} rows Facility records.
   * @returns {void}
   */
  MapEngine.prototype.setData = function (rows) {
    this.rows = rows || [];
    this.reproject();
  };

  /**
   * Switch projection and rebuild projected geometry.
   *
   * @param {string} id Projection identifier.
   * @returns {void}
   */
  MapEngine.prototype.setProjection = function (id) {
    this.projection = projection.get(id);
    this.world = projection.bounds(this.projection, 4);
    this.viewport.world = this.world;
    this.viewport.resize(this.viewport.width, this.viewport.height);
    this.viewport.reset();
    this.reproject();
  };

  /**
   * Project every row and rebuild the spatial index.
   *
   * @returns {void}
   */
  MapEngine.prototype.reproject = function () {
    var points = [];
    for (var i = 0; i < this.rows.length; i += 1) {
      var row = this.rows[i];
      var coords = coordinatesOf(row);
      if (coords === null) continue;
      var xy = this.projection.forward(coords.lon, coords.lat);
      points.push({
        x: xy.x,
        y: xy.y,
        lon: coords.lon,
        lat: coords.lat,
        domain: row.domain || "unknown",
        row: row,
      });
    }
    this.points = points;
    this.tree = Quadtree.build(points);
    this.mapped = points.length;
    this.renderAccessibleList();
    this.requestDraw();
  };

  /**
   * Rebuild the visually hidden, fully focusable record list.
   *
   * @returns {void}
   */
  MapEngine.prototype.renderAccessibleList = function () {
    if (!this.srList) return;
    var doc = this.document;
    var self = this;
    while (this.srList.firstChild) {
      this.srList.removeChild(this.srList.firstChild);
    }
    var limit = Math.min(this.points.length, KEYBOARD_LIST_LIMIT);
    for (var i = 0; i < limit; i += 1) {
      var point = this.points[i];
      var item = doc.createElement("li");
      var button = doc.createElement("button");
      button.type = "button";
      button.textContent =
        (point.row.name || "Unnamed record") +
        " — " +
        (point.row.country || "location not supplied");
      button.addEventListener(
        "click",
        (function (p) {
          return function () {
            self.focusPoint(p);
            self.emitSelection(p);
          };
        })(point),
      );
      item.appendChild(button);
      this.srList.appendChild(item);
    }
    if (this.points.length > limit) {
      var note = doc.createElement("li");
      note.textContent =
        "A further " +
        (this.points.length - limit) +
        " records match. Narrow the filters to bring them into this list.";
      this.srList.appendChild(note);
    }
  };

  /**
   * Resize the drawing surface to its container, honouring device pixels.
   *
   * @returns {void}
   */
  MapEngine.prototype.resize = function () {
    var rect = this.container.getBoundingClientRect
      ? this.container.getBoundingClientRect()
      : { width: 960, height: 480 };
    var dpr = (this.document && this.document.defaultView && this.document.defaultView.devicePixelRatio) || 1;
    var width = Math.max(1, Math.round(rect.width));
    var height = Math.max(1, Math.round(rect.height || width * 0.5));
    this.canvas.width = Math.round(width * dpr);
    this.canvas.height = Math.round(height * dpr);
    this.canvas.style.width = width + "px";
    this.canvas.style.height = height + "px";
    this.dpr = dpr;
    this.viewport.resize(width, height);
    this.requestDraw();
  };

  /**
   * Schedule a repaint on the next animation frame.
   *
   * @returns {void}
   */
  MapEngine.prototype.requestDraw = function () {
    var self = this;
    var view = this.document && this.document.defaultView;
    if (!view || !view.requestAnimationFrame) {
      this.draw();
      return;
    }
    if (this.frame !== null) return;
    this.frame = view.requestAnimationFrame(function () {
      self.frame = null;
      self.draw();
    });
  };

  /**
   * Paint one frame.
   *
   * @returns {void}
   */
  MapEngine.prototype.draw = function () {
    if (!this.ctx) return;
    var ctx = this.ctx;
    ctx.setTransform(this.dpr || 1, 0, 0, this.dpr || 1, 0, 0);
    renderer.drawBackground(ctx, this.viewport);
    renderer.drawGraticule(ctx, this.viewport, this.projection);
    renderer.drawLand(ctx, this.viewport, this.projection, this.rings);

    var visible = this.tree
      ? this.tree.query(this.viewport.visibleWorld(40))
      : [];
    this.clusters = cluster.aggregate(visible, this.viewport, CLUSTER_CELL_PX);
    renderer.drawClusters(ctx, this.clusters, { radiusFor: this.radiusFor });
    renderer.drawClusterLabels(ctx, this.clusters, this.radiusFor);
    renderer.drawFocus(ctx, this.focus ? this.focusScreenEntry() : null, this.radiusFor);
    this.onViewChange({
      zoom: this.viewport.zoom,
      visible: visible.length,
      clusters: this.clusters.length,
      mapped: this.mapped || 0,
    });
  };

  /**
   * The focused point expressed in screen space for the focus ring.
   *
   * @returns {object|null} A screen-space entry.
   */
  MapEngine.prototype.focusScreenEntry = function () {
    if (!this.focus) return null;
    var s = this.viewport.toScreen(this.focus.x, this.focus.y);
    return { x: s.x, y: s.y, count: 1 };
  };

  /**
   * Set the hover focus from a screen position.
   *
   * @param {number} px Screen x.
   * @param {number} py Screen y.
   * @returns {void}
   */
  MapEngine.prototype.setFocusFromScreen = function (px, py) {
    var found = this.pointAt(px, py);
    if (found === this.focus) return;
    this.focus = found;
    if (found) {
      this.announce(
        (found.row.name || "Unnamed record") +
          ", " +
          (found.row.country || "location not supplied"),
      );
    }
    this.requestDraw();
  };

  /**
   * Hit-test a screen position against the indexed points.
   *
   * @param {number} px Screen x.
   * @param {number} py Screen y.
   * @returns {object|null} The point under the cursor.
   */
  MapEngine.prototype.pointAt = function (px, py) {
    if (!this.tree) return null;
    var world = this.viewport.toWorld(px, py);
    var radius = HIT_RADIUS_PX / this.viewport.scale();
    return this.tree.nearest(world.x, world.y, radius);
  };

  /**
   * Activate whatever sits at a screen position.
   *
   * A cluster zooms in; a single record opens. Zooming rather than opening an
   * arbitrary member is what makes a dense region explorable.
   *
   * @param {number} px Screen x.
   * @param {number} py Screen y.
   * @returns {void}
   */
  MapEngine.prototype.activateAt = function (px, py) {
    var point = this.pointAt(px, py);
    if (point) {
      this.emitSelection(point);
      return;
    }
    var entry = this.clusterAt(px, py);
    if (entry && entry.count > 1) {
      var world = this.viewport.toWorld(entry.x, entry.y);
      this.viewport.centreOn(world.x, world.y, this.viewport.zoom * 2.5);
      this.requestDraw();
    }
  };

  /**
   * Find the drawn cluster nearest a screen position.
   *
   * @param {number} px Screen x.
   * @param {number} py Screen y.
   * @returns {object|null} The cluster.
   */
  MapEngine.prototype.clusterAt = function (px, py) {
    var best = null;
    var bestDistance = Infinity;
    for (var i = 0; i < this.clusters.length; i += 1) {
      var entry = this.clusters[i];
      var radius = this.radiusFor(entry.count) + 4;
      var dx = entry.x - px;
      var dy = entry.y - py;
      var d2 = dx * dx + dy * dy;
      if (d2 <= radius * radius && d2 < bestDistance) {
        bestDistance = d2;
        best = entry;
      }
    }
    return best;
  };

  /**
   * Move focus to a specific point and centre it.
   *
   * @param {object} point The point to focus.
   * @returns {void}
   */
  MapEngine.prototype.focusPoint = function (point) {
    this.focus = point;
    this.viewport.centreOn(point.x, point.y, Math.max(this.viewport.zoom, 6));
    this.requestDraw();
  };

  /**
   * Announce a message to assistive technology.
   *
   * @param {string} message The message.
   * @returns {void}
   */
  MapEngine.prototype.announce = function (message) {
    if (this.status) {
      this.status.textContent = message;
    }
  };

  /**
   * Notify the host that a record was chosen.
   *
   * @param {object} point The selected point.
   * @returns {void}
   */
  MapEngine.prototype.emitSelection = function (point) {
    this.onSelect(point.row, point);
  };

  MapEngine.coordinatesOf = coordinatesOf;
  MapEngine.CLUSTER_CELL_PX = CLUSTER_CELL_PX;
  MapEngine.CLUSTER_MAX_RADIUS_PX = CLUSTER_MAX_RADIUS_PX;
  MapEngine.HIT_RADIUS_PX = HIT_RADIUS_PX;
  MapEngine.KEYBOARD_LIST_LIMIT = KEYBOARD_LIST_LIMIT;

  return MapEngine;
});
