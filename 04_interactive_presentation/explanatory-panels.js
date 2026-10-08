// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — authored fusion and flow explanations.
"use strict";

/** Actual authored panel renderer shared by browser and native DOM callers. */
var AtlasExplanatoryPanels = (() => {
  /** @type {Partial<Record<string, [string, string, string[]]>>} */
  const fusionDetails = {
    magnetic: [
      "Magnetic confinement",
      "Tokamaks, stellarators, mirrors, FRCs and compact toroids use magnetic topology to constrain charged particles. Geometry changes stability, transport, pulsed operation and construction.",
      [
        "tokamak",
        "stellarator",
        "mirror",
        "FRC / spheromak",
        "RFP",
        "cusp / dipole",
      ],
    ],
    inertial: [
      "Inertial confinement",
      "A laser, particle beam or projectile compresses a small target before it disassembles. Target ignition does not by itself solve driver efficiency, target production or repetition rate.",
      [
        "direct drive",
        "indirect drive",
        "fast ignition",
        "heavy-ion ICF",
        "impact ICF",
        "Z-pinch ICF",
      ],
    ],
    magneto: [
      "Magneto-inertial fusion",
      "Magnetisation reduces thermal losses while a mechanical, electromagnetic or plasma liner supplies compression. The middle ground still requires precise pulsed symmetry.",
      [
        "MagLIF",
        "plasma-jet liner",
        "liquid liner",
        "mechanical liner",
        "FRC compression",
        "magnetised target",
      ],
    ],
    alternative: [
      "Alternative reaction paths",
      "IEC, dense plasma focus, beam-target, muon and lattice experiments may produce nuclear reactions without positive energy balance. That boundary is essential.",
      [
        "IEC / Polywell",
        "dense plasma focus",
        "beam-target",
        "muon catalysis",
        "lattice fusion",
        "pyroelectric fusion",
      ],
    ],
  };
  /**
   * Render one original authored fusion explanation in the actual page control.
   * @param {Document} owner Actual maintained page document.
   * @param {string|undefined} k Authored topic identity from its actual control.
   * @returns {void} Original title, description and example list were rendered.
   * @throws {Error} The topic or required HTML control is unavailable.
   */
  function renderFusion(owner, k) {
    const choice = k || "";
    const d = fusionDetails[choice];
    if (!d || !Object.hasOwn(fusionDetails, choice))
      throw new Error("Authored fusion topic is unavailable");
    globalThis.AtlasBrowserElements.requireElement(
      owner,
      "fusionDetail",
      "div",
    ).innerHTML =
      `<h3>${d[0]}</h3><div><p>${d[1]}</p><ul>${d[2].map((x) => `<li>${x}</li>`).join("")}</ul></div>`;
  }
  /** @type {Partial<Record<string, [string, string, string, string, string, string]>>} */
  const flows = {
    batch: [
      "Batch reactor",
      "batch",
      "A closed charge evolves in time. It is flexible for multiple products and smaller campaigns.",
      "time-varying",
      "pharma, specialties",
      "heat accumulation",
    ],
    cstr: [
      "Continuous stirred tank",
      "cstr",
      "Inlet, perfectly mixed volume and outlet create a steady state; outlet equals vessel composition.",
      "perfectly mixed",
      "liquid processes",
      "loss of stability",
    ],
    pfr: [
      "Tubular / PFR",
      "pfr",
      "Each fluid element ages along the axis; the ideal model has no axial back-mixing.",
      "radial, not axial",
      "bulk production",
      "hot spots",
    ],
    bio: [
      "Bioreactor",
      "bio",
      "Living cells or enzymes transform substrate; sterility, pH, oxygen and shear become state variables.",
      "culture-sensitive",
      "fermentation, medicines",
      "contamination / collapse",
    ],
  };
  /**
   * Render one original authored flow diagram and explanation in the actual page.
   * @param {Document} owner Actual maintained page document.
   * @param {string|undefined} k Authored flow identity from its actual control.
   * @returns {void} Original diagram, description and context were rendered.
   * @throws {Error} The flow or required HTML control is unavailable.
   */
  function renderFlow(owner, k) {
    const choice = k || "";
    const d = flows[choice];
    if (!d || !Object.hasOwn(flows, choice))
      throw new Error("Authored flow is unavailable");
    const viz =
      k === "pfr"
        ? '<div class="tube"></div>'
        : `<div class="vessel ${d[1]}"></div>`;
    globalThis.AtlasBrowserElements.requireElement(
      owner,
      "flowDemo",
      "div",
    ).innerHTML =
      `<div class="flow-viz">${viz}</div><div class="flow-copy"><h3>${d[0]}</h3><p>${d[2]}</p><dl><div><dt>Flow</dt><dd>${d[3]}</dd></div><div><dt>Typical use</dt><dd>${d[4]}</dd></div><div><dt>Watch</dt><dd>${d[5]}</dd></div></dl></div>`;
  }
  return Object.freeze({ renderFusion, renderFlow });
})();

globalThis.AtlasExplanatoryPanels = AtlasExplanatoryPanels;
