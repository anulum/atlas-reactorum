// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — canvas map engine orchestration and interaction.

/**
 * DOM-node operations used while building and clearing accessible content.
 * @typedef {{textContent: string|null, firstChild: EngineNode|null, appendChild(child: EngineNode): EngineNode, removeChild(child: EngineNode): EngineNode}} EngineNode
 */
/**
 * Element operations exposed by the built map and its accessible list.
 * @typedef {EngineNode & {className: string, tagName: string, children: {length:number,[index:number]:EngineElement}, ownerDocument: EngineDocument|null, setAttribute(name:string,value:string):void, getAttribute(name:string):string|null|undefined}} EngineElement
 */
/**
 * Keyboard fields consumed by the map.
 * @typedef {{key:string, shiftKey?:boolean, preventDefault():void}} MapKeyEvent
 */
/**
 * Listener event shapes matched to actual canvas event names.
 * @typedef {{pointerdown: Pick<PointerEvent,"clientX"|"clientY"|"pointerId">, pointermove: Pick<PointerEvent,"clientX"|"clientY">, pointerup: Event, pointercancel: Event, click: Pick<MouseEvent,"clientX"|"clientY">, wheel: Pick<WheelEvent,"clientX"|"clientY"|"deltaY"|"preventDefault">, keydown: MapKeyEvent}} MapEvents
 */
/**
 * Canvas subset consumed by interaction and painting.
 * @typedef {EngineElement & {style:{width?:string,height?:string}, width?:number, height?:number, getBoundingClientRect():{width:number,height:number,left:number,top:number}, getContext?:(kind:"2d")=>CanvasRenderingContext2D|null, setPointerCapture?:(id:number)=>void, addEventListener:HTMLCanvasElement["addEventListener"]}} EngineCanvas
 */
/**
 * A button needs only the callback-based activation and type field beyond an element.
 * @typedef {EngineElement & {type:string,addEventListener(name:"click",listener:()=>void):void}} EngineButton
 */
/**
 * Native Document operations needed by construction, sizing and frame scheduling.
 * @typedef {{createElement(name:"canvas"):EngineCanvas,createElement(name:"button"):EngineButton,createElement(name:string):EngineElement,defaultView:{devicePixelRatio?:number,requestAnimationFrame?:((callback:()=>void)=>number)|null}|null}} EngineDocument
 */
/**
 * Container operations used for mounting and CSS-pixel size measurement.
 * @typedef {EngineNode & {ownerDocument: EngineDocument|null, getBoundingClientRect?:()=>{width:number,height:number}}} EngineContainer
 */

/**
 * Source coordinates may be absent or require validation; display fields are never inferred.
 * @typedef {{lon?:unknown,lat?:unknown,id?:string,name?:string|null,country?:string|null,domain?:string|null}} FacilityRow
 */

/**
 * Projected point retaining the exact original source object.
 * @template {FacilityRow} Row
 * @typedef {{x:number,y:number,lon:number,lat:number,domain:string,row:Row}} FacilityPoint
 */

/**
 * Report of the just-painted view, in CSS pixels and record counts.
 * @typedef {{zoom:number,visible:number,clusters:number,mapped:number}} ViewReport
 */

/**
 * Constructor options for a native DOM host and its original-row callbacks.
 * @template {FacilityRow} Row
 * @typedef {{container?:EngineContainer,document?:EngineDocument,projection?:string,rings?:[number,number][][],borders?:import("./renderer.js").CountryBorder[],maxZoom?:number,reducedMotion?:boolean,onSelect?:(row:Row,point:FacilityPoint<Row>)=>void,onViewChange?:(view:ViewReport)=>void}} EngineOptions
 */

/**
 * Loaded module namespace; browser callers load the eight dependencies before engine.js.
 * @typedef {{projection:typeof import("./projection.js"),coastline:typeof import("./coastline.js"),Quadtree:typeof import("./quadtree.js"),cluster:typeof import("./cluster.js"),Viewport:typeof import("./viewport.js"),renderer:typeof import("./renderer.js"),interactions:typeof import("./interactions.js"),accessibility:typeof import("./accessibility.js"),MapEngine?:typeof import("./engine.js")}} EngineNamespace
 */

/**
 * Browser host whose map dependencies have already been loaded.
 * @typedef {{AtlasMap?:Partial<EngineNamespace>}} EngineGlobal
 */

/**
 * Publish the same generic map constructor to Node or its classic-script namespace.
 * @param {EngineGlobal} root Browser namespace host.
 * @param {(projection:typeof import("./projection.js"),coastline:typeof import("./coastline.js"),Quadtree:typeof import("./quadtree.js"),cluster:typeof import("./cluster.js"),Viewport:typeof import("./viewport.js"),renderer:typeof import("./renderer.js"),interactions:typeof import("./interactions.js"),accessibility:typeof import("./accessibility.js"))=>typeof import("./engine.js")} factory Builder consuming the actual eight map modules.
 * @returns {void}
 * @throws {Error} If any required browser map module has not been loaded.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory(
      require("./projection.js"),
      require("./coastline.js"),
      require("./quadtree.js"),
      require("./cluster.js"),
      require("./viewport.js"),
      require("./renderer.js"),
      require("./interactions.js"),
      require("./accessibility.js"),
    );
  } else {
    /** @type {Partial<EngineNamespace>} */
    var ns = (root.AtlasMap = root.AtlasMap || {});
    if (
      !ns.projection ||
      !ns.coastline ||
      !ns.Quadtree ||
      !ns.cluster ||
      !ns.Viewport ||
      !ns.renderer ||
      !ns.interactions ||
      !ns.accessibility
    ) {
      throw new Error("map engine: load all map modules before engine.js");
    }
    ns.MapEngine = factory(
      ns.projection,
      ns.coastline,
      ns.Quadtree,
      ns.cluster,
      ns.Viewport,
      ns.renderer,
      ns.interactions,
      ns.accessibility,
    );
  }
})(
  /** @type {EngineGlobal} */ (typeof self !== "undefined" ? self : this),
  /**
   * Build the map constructor over its eight owning module implementations.
   * @param {typeof import("./projection.js")} projection Registered geographic projections.
   * @param {typeof import("./coastline.js")} coastline Loaded coastline module.
   * @param {typeof import("./quadtree.js")} Quadtree Original-point spatial index.
   * @param {typeof import("./cluster.js")} cluster Screen-space aggregation.
   * @param {typeof import("./viewport.js")} Viewport Pan, zoom and world transforms.
   * @param {typeof import("./renderer.js")} renderer Canvas painting.
   * @param {typeof import("./interactions.js")} interactions Actual pointer/keyboard owner.
   * @param {typeof import("./accessibility.js")} accessibility Actual original-point list/live-region owner.
   * @returns {MapEngineConstructor} Payload-preserving constructor and its coordinate parser.
   */
  function (
    projection,
    coastline,
    Quadtree,
    cluster,
    Viewport,
    renderer,
    interactions,
    accessibility,
  ) {
    "use strict";
    /**
     * Constructor type derived from the actual generic map declared in this factory.
     * @typedef {typeof MapEngine} MapEngineConstructor
     */
    var CLUSTER_CELL_PX = 30;
    // Glyphs must stay inside their own cell, or neighbouring clusters overlap
    // and their count labels render on top of one another.
    var CLUSTER_MAX_RADIUS_PX = CLUSTER_CELL_PX * 0.48;
    var POINT_RADIUS_PX = 3.4;
    var HIT_RADIUS_PX = 14;
    var KEYBOARD_LIST_LIMIT = accessibility.LIST_LIMIT;

    /**
     * Parse a facility row into a projectable record.
     *
     * Rows missing usable coordinates are rejected here rather than being
     * drawn at latitude zero, which would invent a location the source never
     * supplied.
     * @param {Pick<FacilityRow,"lon"|"lat">} row Source coordinate fields; numbers or nonblank numeric strings only.
     * @returns {{lon: number, lat: number}|null} Coordinates, or null.
     */
    function coordinatesOf(row) {
      if (typeof row.lon !== "number" && typeof row.lon !== "string")
        return null;
      if (typeof row.lat !== "number" && typeof row.lat !== "string")
        return null;
      if (typeof row.lon === "string" && row.lon.trim() === "") return null;
      if (typeof row.lat === "string" && row.lat.trim() === "") return null;
      var lon = Number(row.lon);
      var lat = Number(row.lat);
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) return null;
      if (lon < -180 || lon > 180 || lat < -90 || lat > 90) return null;
      return { lon: lon, lat: lat };
    }

    /**
     * Canvas-backed facility map.
     * @template {FacilityRow} [Row=FacilityRow]
     * @param {EngineOptions<Row>|null} [options] DOM host, geographic rings and original-row callbacks.
     * @class
     * @throws {Error} If a container or its document is absent, or the projection is unregistered.
     */
    function MapEngine(options) {
      var opts = options || {};
      /**
       * Size a count glyph while keeping its radius inside the configured screen cell.
       * @param {number} count Represented record count.
       * @returns {number} Radius in CSS pixels.
       */
      this.radiusFor = function (count) {
        return cluster.radiusFor(count, POINT_RADIUS_PX, CLUSTER_MAX_RADIUS_PX);
      };
      if (!opts.container) {
        throw new Error("map engine: a container element is required");
      }
      this.container = opts.container;
      var doc = opts.document || opts.container.ownerDocument;
      if (!doc) {
        throw new Error("map engine: a document is required");
      }
      this.document = doc;
      this.onSelect =
        opts.onSelect ||
        /**
         * Leave selection to the host when no callback was supplied.
         * @returns {void}
         */
        function () {};
      this.onViewChange =
        opts.onViewChange ||
        /**
         * Leave external view reporting unchanged when no callback was supplied.
         * @returns {void}
         */
        function () {};
      this.projection = projection.get(opts.projection || "equal-earth");
      this.rings = opts.rings || [];
      this.borders = opts.borders || [];
      /** @type {Row[]} */
      this.rows = [];
      /** @type {FacilityPoint<Row>[]} */
      this.points = [];
      /** @type {ReturnType<typeof Quadtree.build<FacilityPoint<Row>>>|null} */
      this.tree = null;
      /** @type {import("./cluster.js").ClusterEntry<FacilityPoint<Row>>[]} */
      this.clusters = [];
      /** @type {FacilityPoint<Row>|null} */
      this.focus = null;
      /** @type {number|null} */
      this.frame = null;
      this.reducedMotion = Boolean(opts.reducedMotion);
      this.world = projection.bounds(this.projection, 4);
      this.viewport = new Viewport({
        width: 1,
        height: 1,
        world: this.world,
        maxZoom: opts.maxZoom || 48,
      });
      var elements = this.build();
      this.canvas = elements.canvas;
      this.srList = elements.srList;
      this.status = elements.status;
    }

    /**
     * Create and mount the canvas, accessible list and live region.
     * @returns {{canvas:EngineCanvas,srList:EngineElement,status:EngineElement}} The initialized components retained on the engine.
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

      // The first 200 mapped records have focusable buttons; the remaining-count
      // note tells readers to narrow filters to bring other records into the list.
      this.srList = doc.createElement("ul");
      this.srList.className = "atlas-map-sr-list sr-only";
      this.container.appendChild(this.srList);

      this.status = doc.createElement("p");
      this.status.className = "atlas-map-status";
      this.status.setAttribute("aria-live", "polite");
      this.container.appendChild(this.status);

      this.ctx = this.canvas.getContext ? this.canvas.getContext("2d") : null;
      this.attachEvents();
      return { canvas: this.canvas, srList: this.srList, status: this.status };
    };

    /**
     * Wire pointer, wheel and keyboard interaction; movement beyond four CSS pixels suppresses release-click activation.
     * @returns {void}
     */
    MapEngine.prototype.attachEvents = function () {
      interactions.attach(this);
    };

    /**
     * Handle keyboard panning, zooming and record activation.
     * @param {MapKeyEvent} event Key, optional shift modifier and default-scroll cancellation.
     * @returns {void}
     */
    MapEngine.prototype.handleKey = function (event) {
      interactions.handleKey(this, event);
    };

    /**
     * Replace the rendered dataset.
     * @param {this["rows"]|null|undefined} rows Original source rows; absence clears the dataset.
     * @returns {void}
     */
    MapEngine.prototype.setData = function (rows) {
      this.rows = rows || [];
      this.reproject();
    };

    /**
     * Switch projection and rebuild projected geometry.
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
     * Reproject source rows, rebuild the spatial index and rebind focus only to a retained original row.
     * @returns {void}
     */
    MapEngine.prototype.reproject = function () {
      var focusedRow = this.focus ? this.focus.row : null;
      /** @type {typeof this.focus} */
      var focusedPoint = null;
      /** @type {typeof this.points} */
      var points = [];
      for (var i = 0; i < this.rows.length; i += 1) {
        var row = this.rows[i];
        var coords = coordinatesOf(row);
        if (coords === null) continue;
        var xy = this.projection.forward(coords.lon, coords.lat);
        var point = {
          x: xy.x,
          y: xy.y,
          lon: coords.lon,
          lat: coords.lat,
          domain: row.domain || "unknown",
          row: row,
        };
        points.push(point);
        if (row === focusedRow && focusedPoint === null) focusedPoint = point;
      }
      this.points = points;
      this.focus = focusedPoint;
      this.tree = Quadtree.build(points);
      this.mapped = points.length;
      this.renderAccessibleList();
      this.requestDraw();
    };

    /**
     * Rebuild up to 200 original-row buttons and an explicit remaining-count note.
     * @returns {void}
     */
    MapEngine.prototype.renderAccessibleList = function () {
      accessibility.render(this);
    };

    /**
     * Resize the drawing surface to its container, honouring device pixels.
     * @returns {void}
     */
    MapEngine.prototype.resize = function () {
      var rect = this.container.getBoundingClientRect
        ? this.container.getBoundingClientRect()
        : { width: 960, height: 480 };
      var dpr =
        (this.document &&
          this.document.defaultView &&
          this.document.defaultView.devicePixelRatio) ||
        1;
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
      this.frame = view.requestAnimationFrame(
        /**
         * Consume the pending frame token before repainting the current state.
         * @returns {void}
         */
        function () {
          self.frame = null;
          self.draw();
        },
      );
    };

    /**
     * Paint one frame.
     * @returns {void}
     */
    MapEngine.prototype.draw = function () {
      if (!this.ctx) return;
      var ctx = this.ctx;
      ctx.setTransform(this.dpr || 1, 0, 0, this.dpr || 1, 0, 0);
      renderer.drawBackground(ctx, this.viewport);
      renderer.drawGraticule(ctx, this.viewport, this.projection);
      renderer.drawLand(ctx, this.viewport, this.projection, this.rings);
      renderer.drawBorders(ctx, this.viewport, this.projection, this.borders);

      var visible = this.tree
        ? this.tree.query(this.viewport.visibleWorld(40))
        : [];
      this.clusters = cluster.aggregate(
        visible,
        this.viewport,
        CLUSTER_CELL_PX,
      );
      renderer.drawClusters(ctx, this.clusters, { radiusFor: this.radiusFor });
      renderer.drawClusterLabels(ctx, this.clusters, this.radiusFor);
      renderer.drawFocus(
        ctx,
        this.focus ? this.focusScreenEntry() : null,
        this.radiusFor,
      );
      this.onViewChange({
        zoom: this.viewport.zoom,
        visible: visible.length,
        clusters: this.clusters.length,
        mapped: this.mapped || 0,
      });
    };

    /**
     * The focused point expressed in screen space for the focus ring.
     * @returns {{x:number,y:number,count:number}|null} Focused glyph in CSS pixels, or null.
     */
    MapEngine.prototype.focusScreenEntry = function () {
      if (!this.focus) return null;
      var s = this.viewport.toScreen(this.focus.x, this.focus.y);
      return { x: s.x, y: s.y, count: 1 };
    };

    /**
     * Set the hover focus from a screen position.
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
     * @param {number} px Screen x.
     * @param {number} py Screen y.
     * @returns {this["points"][number]|null} Original indexed point in the hit radius, or null.
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
     * @param {number} px Screen x.
     * @param {number} py Screen y.
     * @returns {void}
     */
    MapEngine.prototype.activateAt = function (px, py) {
      var entry = this.clusterAt(px, py);
      if (entry && entry.count > 1) {
        var world = this.viewport.toWorld(entry.x, entry.y);
        this.viewport.centreOn(world.x, world.y, this.viewport.zoom * 2.5);
        this.requestDraw();
        return;
      }
      var point = this.pointAt(px, py);
      if (point) {
        this.emitSelection(point);
      }
    };

    /**
     * Find the drawn cluster nearest a screen position.
     * @param {number} px Screen x.
     * @param {number} py Screen y.
     * @returns {this["clusters"][number]|null} Nearest glyph containing the screen position, or null.
     */
    MapEngine.prototype.clusterAt = function (px, py) {
      /** @type {typeof this.clusters[number]|null} */
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
     * @param {this["points"][number]} point Original indexed point to focus and centre.
     * @returns {void}
     */
    MapEngine.prototype.focusPoint = function (point) {
      this.focus = point;
      this.viewport.centreOn(point.x, point.y, Math.max(this.viewport.zoom, 6));
      this.requestDraw();
    };

    /**
     * Announce a message to assistive technology.
     * @param {string} message The message.
     * @returns {void}
     */
    MapEngine.prototype.announce = function (message) {
      accessibility.announce(this, message);
    };

    /**
     * Notify the host that a record was chosen.
     * @param {this["points"][number]} point Indexed point whose original row is emitted without cloning.
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
  },
);
