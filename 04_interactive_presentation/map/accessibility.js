// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — accessibility.js

/**
 * Original source-point display and activation state supplied by the actual engine.
 * @template {{row:{name?:string|null,country?:string|null}}} Point
 * @typedef {object} AccessibleHost
 * @property {import("./engine.js").EngineDocument} document Actual owning document.
 * @property {import("./engine.js").EngineElement|null|undefined} srList Actual accessible list, or explicit absence.
 * @property {Point[]} points Actual current projected source points.
 * @property {(point:Point)=>void} focusPoint Actual source-point focus method.
 * @property {(point:Point)=>void} emitSelection Original-row selection method.
 */
/**
 * Publish the same owning API to classic scripts and native CommonJS callers.
 * @param {{AtlasMap?:{accessibility?:ReturnType<typeof factory>}}} root Actual browser namespace host.
 * @param {typeof factory} factory Owning implementation constructor.
 * @returns {void} The owning API is loaded before its engine consumer.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.AtlasMap = root.AtlasMap || {};
    root.AtlasMap.accessibility = factory();
  }
})(typeof self !== "undefined" ? self : globalThis, factory);
/**
 * Build the shared actual owning implementation.
 * @returns {{render:typeof render,announce:typeof announce,LIST_LIMIT:number}} Public native methods used by the map engine.
 */
function factory() {
  "use strict";
  const LIST_LIMIT = 200;
  /**
   * Rebuild up to 200 original-row buttons and an explicit remaining-count note.
   * @template {{row:{name?:string|null,country?:string|null}}} Point
   * @param {AccessibleHost<Point>} engine Actual list owner and unchanged source points.
   * @returns {void}
   */
  function render(engine) {
    if (!engine.srList) return;
    var doc = engine.document;
    var self = engine;
    while (engine.srList.firstChild) {
      engine.srList.removeChild(engine.srList.firstChild);
    }
    var limit = Math.min(engine.points.length, LIST_LIMIT);
    for (var i = 0; i < limit; i += 1) {
      var point = engine.points[i];
      var item = doc.createElement("li");
      var button = doc.createElement("button");
      button.type = "button";
      button.textContent =
        (point.row.name || "Unnamed record") +
        " — " +
        (point.row.country || "location not supplied");
      button.addEventListener(
        "click",
        /**
         * Retain this original point for the accessible button's activation.
         * @param {typeof self.points[number]} p Original projected point.
         * @returns {()=>void} Callback that focuses and emits the same point.
         */
        (function (p) {
          return (
            /**
             * Focus the bound source point and emit its unchanged original row.
             * @returns {void}
             */
            function () {
              self.focusPoint(p);
              self.emitSelection(p);
            }
          );
        })(point),
      );
      item.appendChild(button);
      engine.srList.appendChild(item);
    }
    if (engine.points.length > limit) {
      var note = doc.createElement("li");
      note.textContent =
        "A further " +
        (engine.points.length - limit) +
        " records match. Narrow the filters to bring them into this list.";
      engine.srList.appendChild(note);
    }
  }
  /**
   * Announce a message to assistive technology.
   * @param {{status?:import("./engine.js").EngineElement|null}} engine Actual live-region owner or explicit absence.
   * @param {string} message The message.
   * @returns {void}
   */
  function announce(engine, message) {
    if (engine.status) {
      engine.status.textContent = message;
    }
  }
  return Object.freeze({ render, announce, LIST_LIMIT });
}
