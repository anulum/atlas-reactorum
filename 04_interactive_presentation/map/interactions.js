// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — interactions.js

/**
 * Interaction methods and native canvas consumed without constructing a replacement map.
 * @template Point
 * @typedef {object} InteractionHost
 * @property {import("./engine.js").EngineCanvas} canvas Actual mounted canvas.
 * @property {InstanceType<typeof import("./viewport.js")>} viewport Actual current viewport.
 * @property {Point|null} focus Actual indexed focus, or absence.
 * @property {()=>void} requestDraw Native scheduling entry point.
 * @property {(px:number,py:number)=>void} setFocusFromScreen Actual hover lookup.
 * @property {(px:number,py:number)=>void} activateAt Actual aggregate/record activation.
 * @property {(event:import("./engine.js").MapKeyEvent)=>void} handleKey Public keyboard entry point.
 * @property {(point:Point)=>void} emitSelection Original-point emission.
 */
/**
 * Publish the same owning API to classic scripts and native CommonJS callers.
 * @param {{AtlasMap?:{interactions?:ReturnType<typeof factory>}}} root Actual browser namespace host.
 * @param {typeof factory} factory Owning implementation constructor.
 * @returns {void} The owning API is loaded before its engine consumer.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.interactions = factory();
  }
})(typeof self !== "undefined" ? self : globalThis, factory);
/**
 * Build the shared actual owning implementation.
 * @returns {{attach:typeof attach,handleKey:typeof handleKey}} Public native methods used by the map engine.
 */
function factory() {
  "use strict";
  /**
   * Wire pointer, wheel and keyboard interaction; movement beyond four CSS pixels suppresses release-click activation.
   * @template Point
   * @param {InteractionHost<Point>} engine Actual native map and its original-point methods.
   * @returns {void}
   */
  function attach(engine) {
    var self = engine;
    var dragging = false;
    var suppressClick = false;
    var startX = 0;
    var startY = 0;
    var lastX = 0;
    var lastY = 0;

    engine.canvas.addEventListener(
      "pointerdown",
      /**
       * Start a captured drag at the actual pointer position.
       * @param {import("./engine.js").MapEvents["pointerdown"]} event Native event fields consumed by this handler.
       * @returns {void}
       */
      function (event) {
        dragging = true;
        suppressClick = false;
        startX = lastX = event.clientX;
        startY = lastY = event.clientY;
        if (self.canvas.setPointerCapture) {
          self.canvas.setPointerCapture(event.pointerId);
        }
      },
    );

    engine.canvas.addEventListener(
      "pointermove",
      /**
       * Pan while dragging; otherwise update the actual hover focus.
       * @param {import("./engine.js").MapEvents["pointermove"]} event Native event fields consumed by this handler.
       * @returns {void}
       */
      function (event) {
        var rect = self.canvas.getBoundingClientRect();
        if (dragging) {
          var dx = event.clientX - startX;
          var dy = event.clientY - startY;
          if (dx * dx + dy * dy > 4 * 4) suppressClick = true;
          self.viewport.panBy(event.clientX - lastX, event.clientY - lastY);
          lastX = event.clientX;
          lastY = event.clientY;
          self.requestDraw();
          return;
        }
        self.setFocusFromScreen(
          event.clientX - rect.left,
          event.clientY - rect.top,
        );
      },
    );

    engine.canvas.addEventListener(
      "pointerup",
      /**
       * Finish the current drag.
       * @returns {void}
       */
      function () {
        dragging = false;
      },
    );
    engine.canvas.addEventListener(
      "pointercancel",
      /**
       * Cancel the drag and suppress any compatibility click from the cancelled gesture.
       * @returns {void}
       */
      function () {
        dragging = false;
        suppressClick = true;
      },
    );

    engine.canvas.addEventListener(
      "click",
      /**
       * Activate a deliberate click; consume the native click following a drag without opening or zooming a glyph.
       * @param {import("./engine.js").MapEvents["click"]} event Native event fields consumed by this handler.
       * @returns {void}
       */
      function (event) {
        if (suppressClick) {
          suppressClick = false;
          return;
        }
        var rect = self.canvas.getBoundingClientRect();
        self.activateAt(event.clientX - rect.left, event.clientY - rect.top);
      },
    );

    engine.canvas.addEventListener(
      "wheel",
      /**
       * Cancel page scrolling and zoom around the actual pointer anchor.
       * @param {import("./engine.js").MapEvents["wheel"]} event Wheel delta and client coordinates.
       * @returns {void}
       */
      function (event) {
        event.preventDefault();
        var rect = self.canvas.getBoundingClientRect();
        var factor = Math.exp(-event.deltaY * 0.0015);
        self.viewport.zoomAbout(
          factor,
          event.clientX - rect.left,
          event.clientY - rect.top,
        );
        self.requestDraw();
      },
      { passive: false },
    );

    engine.canvas.addEventListener(
      "keydown",
      /**
       * Dispatch keyboard navigation through the public key handler.
       * @param {import("./engine.js").MapEvents["keydown"]} event Native event fields consumed by this handler.
       * @returns {void}
       */
      function (event) {
        self.handleKey(event);
      },
    );
  }
  /**
   * Handle keyboard panning, zooming and record activation.
   * @template Point
   * @param {InteractionHost<Point>} engine Actual native map and original-point selection.
   * @param {import("./engine.js").MapKeyEvent} event Key, optional shift modifier and default-scroll cancellation.
   * @returns {void}
   */
  function handleKey(engine, event) {
    var step = event.shiftKey ? 120 : 40;
    var handled = true;
    switch (event.key) {
      case "ArrowLeft":
        engine.viewport.panBy(step, 0);
        break;
      case "ArrowRight":
        engine.viewport.panBy(-step, 0);
        break;
      case "ArrowUp":
        engine.viewport.panBy(0, step);
        break;
      case "ArrowDown":
        engine.viewport.panBy(0, -step);
        break;
      case "+":
      case "=":
        engine.viewport.zoomAbout(
          1.4,
          engine.viewport.width / 2,
          engine.viewport.height / 2,
        );
        break;
      case "-":
      case "_":
        engine.viewport.zoomAbout(
          1 / 1.4,
          engine.viewport.width / 2,
          engine.viewport.height / 2,
        );
        break;
      case "0":
        engine.viewport.reset();
        break;
      case "Enter":
      case " ":
        if (engine.focus) {
          engine.emitSelection(engine.focus);
        }
        break;
      default:
        handled = false;
    }
    if (handled) {
      event.preventDefault();
      engine.requestDraw();
    }
  }
  return Object.freeze({ attach, handleKey });
}
