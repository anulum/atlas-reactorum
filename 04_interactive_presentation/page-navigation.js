// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — actual page navigation, mobile controls and dialog dismissal.
"use strict";

/** Actual page-navigation facade; every control is admitted before binding. */
var AtlasPageNavigation = (() => {
  /**
   * Bind original section movement, scroll state, keyboard and dialog controls.
   * @param {Document} owner Actual maintained page document.
   * @returns {{goTo:(index:number)=>void, update:()=>void}} Original page movement and current-position refresh.
   * @throws {Error} Window, actual required controls or section targets are unavailable.
   */
  function start(owner) {
    const candidate = owner.defaultView;
    if (!candidate) throw new Error("Atlas navigation window is unavailable");
    const view = candidate;
    const controls = globalThis.AtlasBrowserElements;
    const mobile = controls.requireElement(owner, "mobileNav", "nav");
    const menu = controls.requireElement(owner, "menuToggle", "button");
    const previous = controls.requireElement(owner, "prevSlide", "button");
    const next = controls.requireElement(owner, "nextSlide", "button");
    const status = controls.requireElement(owner, "slideStatus", "span");
    const progress = controls.requireElement(owner, "progressBar", "span");
    const dialog = controls.requireElement(owner, "reactorDialog", "dialog");
    const close = controls.requireSelector(
      owner,
      "button.dialog-close",
      "button",
    );
    const buttons = [...owner.querySelectorAll("button.nav-dot")];
    let current = 0;

    /**
     * Retain the actual direct main-section order without synthetic slide identities.
     * @returns {Element[]} Original section nodes in page order.
     */
    function sections() {
      return [...owner.querySelectorAll("main > section")];
    }
    /**
     * Move to the requested original section with the original boundary clamp.
     * @param {number} index Integer section position requested by a real control.
     * @returns {void} The original section scrolls into view smoothly.
     * @throws {Error} A requested position is not an integer or no section exists.
     */
    function goTo(index) {
      const actual = sections();
      if (!Number.isInteger(index) || !actual.length)
        throw new Error("Atlas section target is unavailable");
      current = Math.max(0, Math.min(actual.length - 1, index));
      actual[current].scrollIntoView({ behavior: "smooth" });
    }
    /**
     * Retain original nearest-section selection, active buttons and scroll progress.
     * @returns {void} Actual page position is reflected in the original controls.
     */
    function update() {
      const actual = sections();
      let best = 0;
      let min = Infinity;
      actual.forEach((section, index) => {
        const distance = Math.abs(section.getBoundingClientRect().top - 72);
        if (distance < min) {
          min = distance;
          best = index;
        }
      });
      current = best;
      status.textContent = `${String(current + 1).padStart(2, "0")} / ${String(actual.length).padStart(2, "0")}`;
      buttons.forEach((button, index) =>
        button.classList.toggle("active", index === current),
      );
      const max = owner.documentElement.scrollHeight - view.innerHeight;
      progress.style.width = `${max ? (view.scrollY / max) * 100 : 0}%`;
    }
    buttons.forEach((button, index) => {
      button.addEventListener("click", () => goTo(index));
      const clone = button.cloneNode(true);
      clone.addEventListener("click", () => {
        goTo(index);
        mobile.hidden = true;
        menu.setAttribute("aria-expanded", "false");
      });
      mobile.append(clone);
    });
    menu.addEventListener("click", () => {
      const open = menu.getAttribute("aria-expanded") === "true";
      menu.setAttribute("aria-expanded", String(!open));
      mobile.hidden = open;
    });
    previous.addEventListener("click", () => goTo(current - 1));
    next.addEventListener("click", () => goTo(current + 1));
    owner.querySelectorAll("[data-jump]").forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.getAttribute("data-jump");
        if (!target) throw new Error("Atlas section target is unavailable");
        controls
          .requireElement(owner, target, "section")
          .scrollIntoView({ behavior: "smooth" });
      });
    });
    view.addEventListener("scroll", update, { passive: true });
    view.addEventListener("keydown", (event) => {
      const active = owner.activeElement;
      if (active && ["INPUT", "SELECT", "TEXTAREA"].includes(active.tagName))
        return;
      if (
        [
          "ArrowRight",
          "PageDown",
          "ArrowLeft",
          "PageUp",
          "Home",
          "End",
        ].includes(event.key)
      )
        event.preventDefault();
      if (["ArrowRight", "PageDown"].includes(event.key)) goTo(current + 1);
      if (["ArrowLeft", "PageUp"].includes(event.key)) goTo(current - 1);
      if (event.key === "Home") goTo(0);
      if (event.key === "End") goTo(sections().length - 1);
    });
    close.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    update();
    return Object.freeze({ goTo, update });
  }
  return Object.freeze({ start });
})();

globalThis.AtlasPageNavigation = AtlasPageNavigation;
