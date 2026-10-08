// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual template control admission for browser controllers.
"use strict";

/**
 * Native DOM element tags from the owning TypeScript DOM library.
 * @typedef {import("./browser-contracts.js").AtlasElementTags} AtlasElementTags
 */

/** Actual DOM control reader shared by source-bound browser controllers. */
var AtlasBrowserElements = (() => {
  /**
   * Require an actual control with its declared HTML tag before binding it.
   * @template {keyof AtlasElementTags} K
   * @param {Document} owner Actual document containing the maintained template.
   * @param {string} id Required unique control identity.
   * @param {K} tag Required HTML element tag.
   * @returns {AtlasElementTags[K]} Original element after native DOM admission.
   * @throws {Error} The required control is missing or has a different tag.
   */
  function requireElement(owner, id, tag) {
    const element = owner.getElementById(id);
    if (
      !element ||
      element.namespaceURI !== "http://www.w3.org/1999/xhtml" ||
      element.localName !== tag
    ) {
      throw new Error("Required Atlas control is unavailable: " + id);
    }
    return /** @type {AtlasElementTags[K]} */ (element);
  }
  /**
   * Require one actual selector match with its declared HTML namespace and tag.
   * @template {keyof AtlasElementTags} K
   * @param {Document} owner Actual maintained template document.
   * @param {string} selector Original control selector.
   * @param {K} tag Required HTML element tag.
   * @returns {AtlasElementTags[K]} Original element after actual DOM admission.
   * @throws {Error} Selector syntax, control presence, namespace or tag is invalid.
   */
  function requireSelector(owner, selector, tag) {
    const element = owner.querySelector(selector);
    if (
      !element ||
      element.namespaceURI !== "http://www.w3.org/1999/xhtml" ||
      element.localName !== tag
    ) {
      throw new Error("Required Atlas control is unavailable: " + selector);
    }
    return /** @type {AtlasElementTags[K]} */ (element);
  }
  /**
   * Admit every actual selector match before binding repeated generated controls.
   * @template {keyof AtlasElementTags} K
   * @param {Document} owner Actual maintained template document.
   * @param {string} selector Original repeated-control selector.
   * @param {K} tag Required HTML element tag.
   * @returns {AtlasElementTags[K][]} Original nodes in DOM order; an empty result retains empty filter views.
   * @throws {Error} Selector syntax or a matched namespace/tag is invalid.
   */
  function requireElements(owner, selector, tag) {
    const elements = [...owner.querySelectorAll(selector)];
    for (const element of elements) {
      if (
        element.namespaceURI !== "http://www.w3.org/1999/xhtml" ||
        element.localName !== tag
      )
        throw new Error("Required Atlas control is unavailable: " + selector);
    }
    return /** @type {AtlasElementTags[K][]} */ (elements);
  }
  return Object.freeze({ requireElement, requireSelector, requireElements });
})();

globalThis.AtlasBrowserElements = AtlasBrowserElements;
