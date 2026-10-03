// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — 04_interactive_presentation/app.js
"use strict";
// Dataset documents wrap their records in an object, because the Tier-0
// scaffold profile requires an object at the top level of every repository
// JSON file. Unwrap once here so the rest of the application works with plain
// arrays and no call site has to know about the wrapper.
for (const name of [
  "REACTOR_FACILITIES",
  "FUSION_COMPANIES",
  "REACTOR_TAXONOMY",
  "REACTOR_TAXONOMY_AUDIT",
  "ANULUM_REACTOR_REPOS",
]) {
  const value = window[name];
  if (value && !Array.isArray(value) && Array.isArray(value.records)) {
    window[name] = value.records;
  }
}

const R = (
  name,
  domain,
  family,
  maturity,
  evidence,
  principle,
  strength,
  challenge,
  temp,
  mode,
  scale,
  control,
) => ({
  name,
  domain,
  family,
  maturity,
  evidence,
  principle,
  strength,
  challenge,
  temp,
  mode,
  scale,
  control,
});
const fallbackReactors = [
  R(
    "PWR",
    "fission",
    "Light-water fission",
    "deployed",
    "established",
    "Pressurised water moderates neutrons and removes heat without boiling in the primary loop.",
    "Large operating base",
    "Pressure system, waste, capital",
    "~300 °C",
    "continuous",
    5,
    4,
  ),
  R(
    "BWR",
    "fission",
    "Light-water fission",
    "deployed",
    "established",
    "Water boils in the core and steam drives the turbine directly.",
    "Simpler steam cycle",
    "Radioactive steam path",
    "~285 °C",
    "continuous",
    5,
    4,
  ),
  R(
    "PHWR / CANDU",
    "fission",
    "Heavy-water fission",
    "deployed",
    "established",
    "Heavy water gives strong neutron economy in pressure tubes.",
    "Fuel flexibility",
    "Heavy-water and tritium management",
    "~310 °C",
    "continuous",
    5,
    4,
  ),
  R(
    "HTGR / VHTR",
    "fission",
    "Gas-cooled fission",
    "demonstrated",
    "demonstrated",
    "Graphite moderates while helium removes high-temperature heat from ceramic fuel.",
    "High outlet temperature",
    "Fuel and materials qualification",
    "750–950 °C",
    "continuous",
    4,
    4,
  ),
  R(
    "Sodium fast reactor",
    "fission",
    "Fast-spectrum fission",
    "demonstrated",
    "demonstrated",
    "Fast neutrons and liquid sodium support advanced fuel-cycle options.",
    "Actinide utilisation",
    "Sodium chemistry and economics",
    "~500 °C",
    "continuous",
    4,
    4,
  ),
  R(
    "Lead fast reactor",
    "fission",
    "Fast-spectrum fission",
    "research",
    "research",
    "Liquid lead or lead-bismuth removes heat at low pressure.",
    "High boiling point",
    "Corrosion and coolant chemistry",
    "400–600 °C",
    "continuous",
    3,
    3,
  ),
  R(
    "Molten-salt reactor",
    "fission",
    "Molten-salt fission",
    "research",
    "research",
    "Salt is coolant; in some designs it also carries fuel.",
    "Low pressure, high temperature",
    "Salt chemistry and materials",
    "600–750 °C",
    "continuous",
    3,
    3,
  ),
  R(
    "SMR / microreactor",
    "fission",
    "Scale and delivery class",
    "research",
    "research",
    "Smaller power and modular production alter deployment, not necessarily core physics.",
    "Modularity and siting",
    "Series economics and licensing",
    "design-dependent",
    "continuous",
    3,
    4,
  ),
  R(
    "Tokamak",
    "fusion",
    "Magnetic confinement",
    "research",
    "demonstrated",
    "Toroidal and poloidal magnetic fields confine a current-carrying plasma.",
    "Most-developed magnetic branch",
    "Disruptions, materials, tritium",
    "plasma >100 MK",
    "pulsed / continuous goal",
    4,
    5,
  ),
  R(
    "Stellarator",
    "fusion",
    "Magnetic confinement",
    "research",
    "demonstrated",
    "Three-dimensional external coils create confinement without a large plasma current.",
    "Natural steady-state potential",
    "3-D optimisation and manufacture",
    "plasma >100 MK",
    "continuous goal",
    4,
    4,
  ),
  R(
    "Magnetic mirror",
    "fusion",
    "Open magnetic confinement",
    "research",
    "research",
    "Stronger fields at the ends reflect part of the charged-particle population.",
    "Simpler geometry",
    "End losses",
    "keV plasma",
    "continuous goal",
    3,
    4,
  ),
  R(
    "FRC",
    "fusion",
    "Compact toroid",
    "research",
    "research",
    "A high-beta field-reversed plasma forms a compact toroidal configuration.",
    "Compactness and high beta",
    "Stability and confinement",
    "keV plasma",
    "usually pulsed",
    3,
    5,
  ),
  R(
    "Spheromak",
    "fusion",
    "Compact toroid",
    "research",
    "research",
    "A self-organised plasma carries both toroidal and poloidal field.",
    "Simpler coil geometry",
    "Relaxation modes and transport",
    "keV plasma",
    "pulsed",
    2,
    4,
  ),
  R(
    "Z-pinch",
    "fusion",
    "Current confinement",
    "research",
    "research",
    "Axial current creates an azimuthal field that compresses the plasma column.",
    "Direct, compact principle",
    "MHD instability",
    "impulsive plasma",
    "pulsed",
    3,
    5,
  ),
  R(
    "Laser ICF",
    "fusion",
    "Inertial confinement",
    "demonstrated",
    "demonstrated",
    "A laser pulse implodes a fuel capsule before it disassembles.",
    "Target ignition demonstrated",
    "System gain, repetition, targets",
    "extreme pulse",
    "pulsed",
    4,
    5,
  ),
  R(
    "MagLIF",
    "fusion",
    "Magneto-inertial fusion",
    "research",
    "research",
    "A metal liner compresses preheated, magnetised fuel.",
    "Combines insulation and compression",
    "Symmetry, repetition, targets",
    "impulsive",
    "pulsed",
    3,
    5,
  ),
  R(
    "IEC / Polywell",
    "fusion",
    "Electrostatic fusion",
    "research",
    "research",
    "Electric fields accelerate and focus ions; recirculating losses usually dominate energy balance.",
    "Compact neutron source",
    "Losses and grid heating",
    "non-equilibrium ions",
    "mixed",
    2,
    3,
  ),
  R(
    "Batch reactor",
    "chemical",
    "Ideal chemical reactor",
    "deployed",
    "established",
    "A charge reacts without continuous inlet and outlet during the campaign.",
    "Flexibility",
    "Batch variability and heat removal",
    "process-specific",
    "batch",
    3,
    3,
  ),
  R(
    "CSTR",
    "chemical",
    "Ideal chemical reactor",
    "deployed",
    "established",
    "A perfectly mixed volume has the same composition as its outlet.",
    "Control and uniformity",
    "Lower conversion per volume",
    "process-specific",
    "continuous",
    4,
    4,
  ),
  R(
    "PFR / tubular",
    "chemical",
    "Ideal chemical reactor",
    "deployed",
    "established",
    "Material advances along a tube with minimal axial back-mixing.",
    "High conversion per volume",
    "Hot spots and pressure drop",
    "process-specific",
    "continuous",
    4,
    3,
  ),
  R(
    "Fixed bed",
    "chemical",
    "Heterogeneous catalytic",
    "deployed",
    "established",
    "Fluid passes through a stationary bed of catalyst particles.",
    "High catalyst area",
    "Pressure drop and gradients",
    "process-specific",
    "continuous",
    4,
    3,
  ),
  R(
    "Fluidised bed",
    "chemical",
    "Multiphase reactor",
    "deployed",
    "established",
    "Fluid suspends solids and enhances mixing and heat transfer.",
    "Heat and mass transfer",
    "Erosion and separation",
    "process-specific",
    "continuous",
    5,
    4,
  ),
  R(
    "Membrane reactor",
    "chemical",
    "Intensified reactor",
    "demonstrated",
    "demonstrated",
    "A selective membrane removes a reactant or product during reaction.",
    "Equilibrium shift and integration",
    "Fouling and membrane stability",
    "process-specific",
    "continuous",
    3,
    4,
  ),
  R(
    "Microreactor",
    "chemical",
    "Flow chemistry",
    "deployed",
    "established",
    "Small channels give high surface-to-volume ratio and short transport times.",
    "Transfer and low inventory",
    "Clogging and scale-out",
    "process-specific",
    "continuous",
    2,
    4,
  ),
  R(
    "Electrolyser",
    "chemical",
    "Electrochemical reactor",
    "deployed",
    "established",
    "Voltage drives separated redox reactions at electrodes.",
    "Direct electricity coupling",
    "Materials, catalysts, efficiency",
    "20–850 °C",
    "continuous",
    4,
    4,
  ),
  R(
    "Anaerobic digester",
    "chemical",
    "Biochemical reactor",
    "deployed",
    "established",
    "A microbial ecosystem converts organic matter to biogas without oxygen.",
    "Waste-to-energy",
    "Biological stability and feed quality",
    "~35 / 55 °C",
    "mixed",
    4,
    3,
  ),
  R(
    "Fusion–fission hybrid",
    "hybrid",
    "Nuclear hybrid",
    "concept",
    "research",
    "Fusion neutrons drive multiplication or transmutation in a subcritical blanket.",
    "Neutron synergy",
    "Combines two complex systems",
    "multi-regime",
    "source-dependent",
    2,
    5,
  ),
  R(
    "ADS",
    "hybrid",
    "Accelerator-driven system",
    "research",
    "demonstrated",
    "An accelerator and spallation target sustain a subcritical fission system.",
    "Subcriticality and transmutation",
    "Beam and target availability",
    "reactor regime",
    "continuous",
    3,
    5,
  ),
  R(
    "Muon-catalysed fusion",
    "hybrid",
    "Catalysed fusion",
    "demonstrated",
    "demonstrated",
    "A muon replaces an electron and brings hydrogen-isotope nuclei closer.",
    "Fusion at low temperature",
    "Muon production and finite cycling",
    "low bulk temperature",
    "experimental",
    1,
    3,
  ),
  R(
    "Lattice-confinement fusion",
    "hybrid",
    "Externally driven fusion",
    "research",
    "research",
    "A deuterated lattice changes conditions for nuclear reactions driven by a beam or radiation.",
    "Measurable products in some experiments",
    "Not chemistry-only net energy",
    "cold host",
    "experimental",
    1,
    3,
  ),
  R(
    "LENR / cold fusion",
    "hybrid",
    "Contested claim",
    "contested",
    "contested",
    "Claims of excess heat or nuclear products in metal–hydrogen systems under chemical conditions.",
    "A subject for rigorous testing",
    "Replication, calorimetry, product ratios",
    "low",
    "unproven",
    1,
    1,
  ),
];
const taxonomyAuditById = Object.fromEntries(
  (window.REACTOR_TAXONOMY_AUDIT || []).map((row) => [row.id, row]),
);
const reactors = (window.REACTOR_TAXONOMY?.length
  ? window.REACTOR_TAXONOMY
  : fallbackReactors
).map((row) => ({ ...row, taxonomy_audit: taxonomyAuditById[row.id] }));
const domainLabels = {
  all: "All",
  fission: "Nuclear fission",
  fusion: "Plasma fusion",
  chemical: "Chemical / bio",
  hybrid: "Hybrid / emerging",
};
const maturityLabels = {
  deployed: "industrial deployment",
  demonstrated: "experimental demonstration",
  research: "active research",
  contested: "contested",
  concept: "concept",
};
const evidenceLabels = {
  established: "established",
  demonstrated: "demonstrated",
  research: "research",
  contested: "contested",
  concept: "concept",
};
const $ = (s) => document.querySelector(s),
  $$ = (s) => [...document.querySelectorAll(s)],
  esc = (s) =>
    String(s).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
let activeDomain = "all";
let atlasMap = null;
function initFilters() {
  let maturityLabel = $("#maturityFilter").closest("label");
  maturityLabel.insertAdjacentHTML(
    "beforebegin",
    '<label class="select-wrap">Entry kind<select id="kindFilter"><option value="all">All kinds</option></select></label>',
  );
  [...new Set(reactors.map((r) => r.kind).filter(Boolean))]
    .sort()
    .forEach((v) =>
      $("#kindFilter").insertAdjacentHTML(
        "beforeend",
        `<option>${esc(v)}</option>`,
      ),
    );
  Object.entries(domainLabels).forEach(([key, label]) => {
    let b = document.createElement("button");
    b.className = "chip" + (key === "all" ? " active" : "");
    b.textContent = label;
    b.onclick = () => {
      $$("#domainFilters .chip").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      activeDomain = key;
      updateFamilies();
      renderReactors();
    };
    $("#domainFilters").append(b);
  });
  $("#reactorSearch").oninput = renderReactors;
  $("#maturityFilter").onchange = renderReactors;
  $("#familyFilter").onchange = renderReactors;
  $("#kindFilter").onchange = renderReactors;
  updateFamilies();
  renderReactors();
}
function updateFamilies() {
  let options = [
    ...new Set(
      reactors
        .filter((r) => activeDomain === "all" || r.domain === activeDomain)
        .map((r) => r.family),
    ),
  ].sort();
  $("#familyFilter").innerHTML =
    '<option value="all">All families</option>' +
    options.map((v) => `<option>${esc(v)}</option>`).join("");
}
function safeUrl(value) {
  try {
    let u = new URL(value);
    return ["https:", "http:"].includes(u.protocol) ? esc(u.href) : "#";
  } catch {
    return "#";
  }
}
function sourceLinks(values) {
  return [...new Set((values || []).filter(Boolean))]
    .map((s, i) => {
      let u = typeof s === "string" ? s : s.url;
      return `<a href="${safeUrl(u)}" target="_blank" rel="noopener noreferrer">${esc(typeof s === "string" ? s : s.title || u)} ↗</a>`;
    })
    .join("");
}
function renderReactors() {
  let q = $("#reactorSearch").value.toLowerCase(),
    m = $("#maturityFilter").value,
    f = $("#familyFilter").value,
    k = $("#kindFilter").value,
    rows = reactors.filter(
      (r) =>
        (activeDomain === "all" || r.domain === activeDomain) &&
        (m === "all" || r.maturity === m) &&
        (f === "all" || r.family === f) &&
        (k === "all" || r.kind === k) &&
        `${r.name} ${r.family} ${r.parent || ""} ${r.kind || ""} ${r.principle} ${r.taxonomy_audit?.classification_ok || ""}`
          .toLowerCase()
          .includes(q),
    );
  $("#resultCount").textContent = rows.length;
  $("#activeFilterText").textContent =
    `of ${reactors.length} taxonomy entries · ${activeDomain === "all" ? "all domains" : domainLabels[activeDomain]}`;
  $("#reactorGrid").innerHTML =
    rows
      .map(
        (r) =>
          `<button class="reactor-card" data-name="${esc(r.name)}"><span class="domain"><i class="dot ${esc(r.domain)}"></i>${esc(domainLabels[r.domain] || r.domain)} · ${esc(r.family)}</span><h3>${esc(r.name)}</h3><p>${esc(r.principle)}</p><footer><span class="maturity">${esc(r.kind || "entry")} · ${esc(maturityLabels[r.maturity] || r.maturity)}</span><span>↗</span></footer></button>`,
      )
      .join("") || "<p>No matching systems.</p>";
  $$(".reactor-card").forEach(
    (b) => (b.onclick = () => openReactor(b.dataset.name)),
  );
}
function openReactor(n) {
  let r = reactors.find((x) => x.name === n);
  if (!r) return;
  let parent =
    reactors.find((x) => x.id === r.parent)?.name || r.parent || r.family;
  $("#dialogBody").innerHTML =
    `<div class="dialog-body"><span class="kicker">${esc(domainLabels[r.domain] || r.domain)} / ${esc(r.family)}</span><h2 id="dialogTitle">${esc(r.name)}</h2><p class="hierarchy">${esc(parent)} → ${esc(r.name)}${r.kind ? " · " + esc(r.kind) : ""}</p><div class="dialog-meta"><span>${esc(maturityLabels[r.maturity] || r.maturity)}</span><span>evidence: ${esc(evidenceLabels[r.evidence] || r.evidence)}</span></div><p class="principle">${esc(r.principle)}</p><dl>${[
      ["Strength", r.strength],
      ["Critical challenge", r.challenge],
      ["Temperature", r.temp],
      ["Operating mode", r.mode],
      [
        "Evidence scope",
        r.evidence_scope || "See source material for the scope of each claim.",
      ],
      [
        "Taxonomy audit",
        r.taxonomy_audit
          ? `${r.taxonomy_audit.classification_ok}. ${r.taxonomy_audit.source_directness}`
          : "Not yet audited.",
      ],
      ["Audit issue", r.taxonomy_audit?.issue],
      ["Recommended action", r.taxonomy_audit?.recommended_action],
    ]
      .map(
        ([k, v]) =>
          `<div><dt>${esc(k)}</dt><dd>${esc(v || "Not specified")}</dd></div>`,
      )
      .join(
        "",
      )}</dl>${AtlasTaxonomyCitations.render(r.taxonomy_audit?.claim_citations || [])}<h3>Sources</h3><div class="detail-sources">${sourceLinks(r.source_urls || r.sources) || "Source mapping pending."}</div></div>`;
  $("#reactorDialog").showModal();
}
function initCompare() {
  let opts = reactors.map((r) => `<option>${esc(r.name)}</option>`).join("");
  $("#compareA").innerHTML = opts;
  $("#compareB").innerHTML = opts;
  $("#compareC").insertAdjacentHTML("beforeend", opts);
  let fission =
      reactors.find((r) => r.name === "PWR") ||
      reactors.find((r) => r.domain === "fission") ||
      reactors[0],
    fusion =
      reactors.find((r) => r.name === "Tokamak") ||
      reactors.find((r) => r.domain === "fusion") ||
      reactors[1] ||
      reactors[0];
  $("#compareA").value = fission.name;
  $("#compareB").value = fusion.name;
  ["compareA", "compareB", "compareC"].forEach(
    (id) => ($("#" + id).onchange = renderCompare),
  );
  renderCompare();
}
function renderCompare() {
  let rows = [$("#compareA").value, $("#compareB").value, $("#compareC").value]
    .filter(Boolean)
    .map((n) => reactors.find((r) => r.name === n))
    .filter(Boolean);
  let line = (label, key, fn = (v) => v) =>
    `<tr><th scope="row">${esc(label)}</th>${rows.map((r) => `<td>${esc(fn(r[key]) || "Not specified")}</td>`).join("")}</tr>`;
  $("#compareView").innerHTML =
    `<table class="comparison"><thead><tr><th>Dimension</th>${rows.map((r) => `<th>${esc(r.name)}</th>`).join("")}</tr></thead><tbody>${line("Domain", "domain", (v) => domainLabels[v])}${line("Family", "family")}${line("Maturity", "maturity", (v) => maturityLabels[v] || v)}${line("Evidence scope", "evidence_scope")}${line("Strength", "strength")}${line("Critical challenge", "challenge")}${line("Temperature", "temp")}${line("Mode", "mode")}</tbody></table>`;
}
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
function renderFusion(k) {
  let d = fusionDetails[k];
  $("#fusionDetail").innerHTML =
    `<h3>${d[0]}</h3><div><p>${d[1]}</p><ul>${d[2].map((x) => `<li>${x}</li>`).join("")}</ul></div>`;
}
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
function renderFlow(k) {
  let d = flows[k],
    viz =
      k === "pfr"
        ? '<div class="tube"></div>'
        : `<div class="vessel ${d[1]}"></div>`;
  $("#flowDemo").innerHTML =
    `<div class="flow-viz">${viz}</div><div class="flow-copy"><h3>${d[0]}</h3><p>${d[2]}</p><dl><div><dt>Flow</dt><dd>${d[3]}</dd></div><div><dt>Typical use</dt><dd>${d[4]}</dd></div><div><dt>Watch</dt><dd>${d[5]}</dd></div></dl></div>`;
}
function renderRepos() {
  let q = $("#repoSearch").value.toLowerCase(),
    repos = window.ANULUM_REACTOR_REPOS || [];
  $("#repoGrid").innerHTML = repos
    .filter((r) =>
      [r.name, r.description, r.category, r.topics]
        .flat()
        .join(" ")
        .toLowerCase()
        .includes(q),
    )
    .map(
      (r) =>
        `<a class="repo-card" href="${safeUrl(r.url)}" target="_blank" rel="noopener"><span>${esc(r.category)}</span><h4>${esc(r.name)}</h4><p>${esc(r.description)}</p><small>Updated ${esc(r.updated_at.slice(0, 10))} · ${esc(r.license)}</small></a>`,
    )
    .join("") || "<p>No matching reactor-system repositories.</p>";
}
function facilityDatasetLabel(path) {
  const labels = {
    "05_global_reactor_map/data/reactors.tsv": "WRI historical plant layer",
    "04_interactive_presentation/data/facilities-supplemental.json":
      "Supplemental context records",
    "05_global_reactor_map/imports/fusion/ffdb/fusion_facilities.tsv":
      "IAEA FFDB catalogue (2 October 2026)",
    "05_global_reactor_map/imports/fusion/fusion_facilities.tsv":
      "Fusion device base layer",
    "05_global_reactor_map/imports/fusion/enrichment/new_facilities.tsv":
      "Fusion official-source additions",
    "05_global_reactor_map/imports/research_reactors/research_reactors.tsv":
      "Research reactors",
    "05_global_reactor_map/imports/power_units/power_reactor_units.tsv":
      "GEM power-reactor units",
    "05_global_reactor_map/imports/industrial_facilities/industrial_facilities.tsv":
      "EEA and U.S. industrial sites",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round2/industrial_facilities_round2.tsv":
      "Canada and Australia industrial sites",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round3/industrial_facilities_round3.tsv":
      "United Kingdom industrial sites",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round4/industrial_facilities_round4.tsv":
      "Switzerland industrial sites",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round5/industrial_facilities_round5.tsv":
      "UK anaerobic digestion and France hydrogen sites",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round6/industrial_facilities_round6.tsv":
      "Brazil biofuels and U.S. landfill-gas projects",
    "05_global_reactor_map/imports/industrial_facilities/expansion_round7/industrial_facilities_round7.tsv":
      "Swiss and Italian biogas sites",
  };
  return labels[path] || path || "Unlabelled dataset";
}
function initFacilityMap() {
  let rows = window.REACTOR_FACILITIES || [],
    statusLabel = $("#facilityStatus").closest("label");
  if (!$("#facilityKind")) {
    statusLabel.insertAdjacentHTML(
      "beforebegin",
      '<label>Layer<select id="facilityKind"><option value="all">All record layers</option></select></label><label>Dataset<select id="facilityDataset"><option value="all">All source datasets</option></select></label><label>Country<select id="facilityCountry"><option value="all">All countries</option></select></label>',
    );
  }
  if (!$("#facilityExportCsv")) {
    $("#facilityCompleteness").insertAdjacentHTML(
      "beforebegin",
      '<button id="facilityExportCsv" class="data-export" type="button">Export filtered CSV</button><button id="facilityExportJson" class="data-export" type="button">Export filtered JSON</button>',
    );
    $("#facilityCompleteness").insertAdjacentHTML(
      "afterend",
      '<span id="facilityLayerSummary" class="layer-summary"></span>',
    );
    $("#facilityExportCsv").onclick = () => downloadFacilityData("csv");
    $("#facilityExportJson").onclick = () => downloadFacilityData("json");
  }
  [
    ["facilityDomain", "domain"],
    ["facilityKind", "record_kind"],
    ["facilityCountry", "country"],
    ["facilityStatus", "status"],
  ].forEach(([id, k]) =>
    [...new Set(rows.map((x) => x[k]).filter(Boolean))]
      .sort()
      .forEach((v) =>
        $("#" + id).insertAdjacentHTML(
          "beforeend",
          `<option>${esc(v)}</option>`,
        ),
      ),
  );
  [...new Set(rows.map((x) => x.dataset_source).filter(Boolean))]
    .sort((a, b) => facilityDatasetLabel(a).localeCompare(facilityDatasetLabel(b)))
    .forEach((value) =>
      $("#facilityDataset").insertAdjacentHTML(
        "beforeend",
        `<option value="${esc(value)}">${esc(facilityDatasetLabel(value))}</option>`,
      ),
    );
  [
    "facilityDomain",
    "facilityKind",
    "facilityDataset",
    "facilityCountry",
    "facilityStatus",
    "facilitySearch",
  ].forEach((id) =>
    $("#" + id).addEventListener(
      id === "facilitySearch" ? "input" : "change",
      renderFacilities,
    ),
  );
  $("#global-map .section-head p").textContent =
    "Explore sourced power-reactor units, research reactors, fusion devices, anaerobic digesters and reported chemical/food industrial sites. A site record does not prove an individual reactor vessel; inspect each record's caveat.";
  initMapEngine();
  renderFacilities();
}
/**
 * Create the canvas map engine, replacing the former SVG point layer.
 *
 * The coastline is recovered from the bundled basemap path, so switching
 * projection needs no additional geometry and introduces no new data licence.
 */
function initMapEngine() {
  let host = $("#mapHost");
  if (!host || !window.AtlasMap || atlasMap) return;
  let rings = [];
  try {
    rings = window.AtlasMap.coastline.fromDocument(document, "#worldMap path.land");
  } catch (error) {
    // A missing basemap must not take the rest of the section down with it.
    host.textContent = "Basemap geometry unavailable; records remain listed below.";
    return;
  }
  atlasMap = new window.AtlasMap.MapEngine({
    container: host,
    document: document,
    rings: rings,
    projection: "equal-earth",
    onSelect: (row) => openFacility(row.id),
    onViewChange: (view) => {
      let el = $("#mapViewSummary");
      if (el) {
        el.textContent =
          view.mapped.toLocaleString("en-GB") +
          " mapped · " +
          view.clusters.toLocaleString("en-GB") +
          " groups in view · zoom " +
          view.zoom.toFixed(1) +
          "×";
      }
    },
  });
  atlasMap.resize();
  window.addEventListener("resize", () => atlasMap.resize());
}
function filteredFacilities() {
  let all = window.REACTOR_FACILITIES || [],
    d = $("#facilityDomain").value,
    k = $("#facilityKind").value,
    dataset = $("#facilityDataset").value,
    c = $("#facilityCountry").value,
    s = $("#facilityStatus").value,
    q = $("#facilitySearch").value.toLowerCase();
  return all.filter(
    (x) =>
      (d === "all" || x.domain === d) &&
      (k === "all" || x.record_kind === k) &&
      (dataset === "all" || x.dataset_source === dataset) &&
      (c === "all" || x.country === c) &&
      (s === "all" || x.status === s) &&
      `${x.name} ${x.country} ${x.type} ${x.operator || x.organization || ""} ${x.purpose || ""} ${x.process_or_activity || ""} ${x.fuel_or_feed || ""}`
        .toLowerCase()
        .includes(q),
  );
}
function downloadFacilityData(format) {
  let rows = filteredFacilities(),
    fields = [
      "id",
      "name",
      "country",
      "domain",
      "record_kind",
      "type",
      "status",
      "lat",
      "lon",
      "operator",
      "organization",
      "purpose",
      "process_or_activity",
      "fuel_or_feed",
      "field_observations",
      "source_url",
      "dataset_source",
      "data_caveat",
    ],
    csvCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`,
    payload =
      format === "json"
        ? JSON.stringify(rows, null, 2)
        : [fields.join(","), ...rows.map((row) => fields.map((field) => csvCell(field === "field_observations" ? JSON.stringify(row[field] || []) : row[field])).join(","))].join("\n"),
    blob = new Blob([payload + "\n"], {
      type: format === "json" ? "application/json" : "text/csv",
    }),
    link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `reactor-atlas-filtered-${new Date().toISOString().slice(0, 10)}.${format}`;
  link.click();
  URL.revokeObjectURL(link.href);
}
function renderFacilities() {
  let all = window.REACTOR_FACILITIES || [],
    rows = filteredFacilities(),
    visible = rows.slice(0, 250);
  if (atlasMap) {
    atlasMap.setData(rows);
  }
  $("#facilityList").innerHTML =
    (rows.length > 250
      ? '<p class="list-limit">Showing the first 250 matching records. Refine the filters or search to inspect the remainder.</p>'
      : "") +
      visible
      .map(
        (x) =>
          `<article><span>${esc(x.country)} · ${esc(x.status)} · ${esc(x.record_kind || "facility")}</span><h3><button class="facility-open" data-id="${esc(x.id)}">${esc(x.name)}</button></h3><p>${esc(x.type)}</p><a href="${safeUrl(x.source_url)}" target="_blank" rel="noopener">source ↗</a></article>`,
      )
      .join("") || "<p>No matching facilities.</p>";
  $$("[data-id]").forEach((el) => {
    el.onclick = () => openFacility(el.dataset.id);
    if (el.tagName.toLowerCase() === "circle")
      el.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openFacility(el.dataset.id);
        }
      };
  });
  let mapped = rows.filter(
    (x) => x.lon !== null && x.lon !== "" && x.lat !== null && x.lat !== "",
  ).length;
  $("#facilityCompleteness").textContent =
    `${rows.length} of ${all.length} records · ${mapped} mapped · list capped at 250 · current status may be unverified`;
  let domainCounts = Object.entries(
    rows.reduce((counts, row) => {
      counts[row.domain] = (counts[row.domain] || 0) + 1;
      return counts;
    }, {}),
  );
  $("#facilityLayerSummary").textContent = domainCounts
    .map(([domain, count]) => `${domain}: ${count}`)
    .join(" · ");
}
function openFacility(id) {
  let x = (window.REACTOR_FACILITIES || []).find((x) => x.id === id);
  if (!x) return;
  let location =
      x.lat !== null &&
      x.lon !== null &&
      Number.isFinite(Number(x.lat)) &&
      Number.isFinite(Number(x.lon))
        ? x.lat + ", " + x.lon
        : "Coordinates unavailable",
    fields = [
      ["Country", x.country],
      ["Plant / parent site", x.plant_name],
      ["Type", x.type],
      ["Sector", x.sector],
      ["Process / activity", x.process_or_activity],
      ["Status", x.status],
      ["Location", location],
      ["Electrical capacity (MW)", x.capacity_mw],
      ["Source nameplate capacity (MW)", x.nameplate_mw],
      ["Net electrical power (MWe)", x.net_mwe],
      ["Gross electrical power (MWe)", x.gross_mwe],
      ["Thermal power (MW)", x.thermal_power_mw || x.thermal_mw],
      ["Industrial capacity", x.capacity],
      ["Published purpose / use", x.purpose],
      ["Published fuel / feed classification", x.fuel_or_feed],
      ["Product / reporting context", x.pollutant_or_product_context],
      ["Operator / organisation", x.operator || x.organization],
      ["Owner", x.owner],
      ["Construction start", x.construction_start],
      [
        "First operation / criticality",
        x.first_criticality || x.first_operation,
      ],
      ["Grid connection", x.grid_connection],
      ["Commercial operation", x.commercial_operation],
      [
        "Last operation / shutdown",
        x.permanent_shutdown || x.shutdown_date || x.last_operation,
      ],
      ["Data coverage", x.completeness],
      ["Dataset", x.dataset || x.dataset_source || x.source_dataset],
      ["Source date", x.source_date || x.source_checked || x.retrieved_at],
      ["Quality flag", x.data_quality_flag],
      ["Coverage caveat", x.data_caveat],
      ["Notes", x.notes || x.verification_notes],
    ];
  $("#dialogBody").innerHTML =
    `<div class="dialog-body"><span class="kicker">Facility / ${esc(x.domain)}</span><h2 id="dialogTitle">${esc(x.name)}</h2><dl>${fields
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`)
      .join(
        "",
      )}</dl>${facilityFieldSources(x)}<div class="detail-sources">${sourceLinks(x.source_urls || [x.source_url])}</div></div>`;
  $("#reactorDialog").showModal();
}
/** Render each original field assertion with its source meaning and capture date. */
function facilityFieldSources(record) {
  const meanings = {
    "published-end-use": "Published end use",
    "published-feedstock": "Published feedstock",
    "fuel-classification": "Publisher fuel classification",
    "primary-fuel-classification": "Primary whole-plant fuel category",
    "secondary-fuel-classification": "Secondary whole-plant fuel category",
  };
  const observations = record.field_observations || [];
  if (!observations.length) return "";
  return `<section class="field-sources"><h3>Source field assertions</h3><p>Plant classifications do not establish reactor fuel composition or current physical operation.</p>${observations.map((row) => `<p><strong>${esc(meanings[row.basis])}</strong>: ${esc(row.value)} · original field ${esc(row.source_field)} · captured ${esc(row.checked)} · ${esc(row.license)} <a href="${safeUrl(row.source_url)}" target="_blank" rel="noopener">source ↗</a></p>`).join("")}</section>`;
}

function initCompanies() {
  let rows = window.FUSION_COMPANIES || [];
  [
    ["companyApproach", "approach"],
    ["companyCountry", "country"],
    ["companyEvidence", "evidence"],
    ["companyStatus", "status"],
  ].forEach(([id, k]) =>
    [...new Set(rows.map((x) => x[k]).filter(Boolean))]
      .sort()
      .forEach((v) =>
        $("#" + id).insertAdjacentHTML(
          "beforeend",
          `<option>${esc(v)}</option>`,
        ),
      ),
  );
  [
    "companyApproach",
    "companyCountry",
    "companyEvidence",
    "companyStatus",
  ].forEach((id) => ($("#" + id).onchange = renderCompanies));
  $("#companySearch").oninput = renderCompanies;
  renderCompanies();
}
function renderCompanies() {
  let a = $("#companyApproach").value,
    c = $("#companyCountry").value,
    e = $("#companyEvidence").value,
    s = $("#companyStatus").value,
    q = $("#companySearch").value.toLowerCase(),
    all = window.FUSION_COMPANIES || [],
    rows = all.filter(
      (x) =>
        (a === "all" || x.approach === a) &&
        (c === "all" || x.country === c) &&
        (e === "all" || x.evidence === e) &&
        (s === "all" || x.status === s) &&
        [
          x.name,
          x.country,
          x.approach,
          x.identity_class,
          x.public_devices_projects,
          x.company_claim,
          x.independent_evidence,
          x.unsupported_or_ambiguous_claims,
          x.notes,
        ]
          .join(" ")
          .toLowerCase()
          .includes(q),
    );
  $("#companyCount").textContent =
    `${rows.length} of ${all.length} audited company/project records`;
  $("#companyGrid").innerHTML =
    rows
      .map(
        (x) =>
          `<article><span class="badge">${esc(x.evidence)}</span><h3>${esc(x.name)}</h3><p class="company-meta">${esc(x.country)} · ${esc(x.approach)} · ${esc(x.status)}</p><dl>${x.identity_class ? `<dt>Identity class</dt><dd>${esc(x.identity_class)}</dd>` : ""}${x.public_devices_projects ? `<dt>Public devices / projects</dt><dd>${esc(x.public_devices_projects)}</dd>` : ""}<dt>Company claim</dt><dd>${esc(x.company_claim || "Not catalogued")}</dd><dt>Highest independently supported milestone</dt><dd>${esc(x.independent_evidence || "Not assessed")}</dd>${x.evidence_tier ? `<dt>Evidence tier</dt><dd>${esc(x.evidence_tier)}</dd>` : ""}${x.status_detail ? `<dt>Status detail</dt><dd>${esc(x.status_detail)}</dd>` : ""}${x.confidence ? `<dt>Audit confidence</dt><dd>${esc(x.confidence)}</dd>` : ""}${x.data_caveat ? `<dt>Unsupported / ambiguous claims</dt><dd>${esc(x.data_caveat)}</dd>` : ""}${x.evidence_maturity ? `<dt>Candidate evidence notes</dt><dd>${esc(x.evidence_maturity)}</dd>` : ""}${x.notes ? `<dt>Registry notes</dt><dd>${esc(x.notes)}</dd>` : ""}</dl><div class="detail-sources">${sourceLinks(x.source_urls || [x.source_url, x.independent_source_url])}</div></article>`,
      )
      .join("") || "<p>No matching companies.</p>";
}
const sections = () => $$("main>section");
let current = 0;
function goTo(i) {
  let ss = sections();
  current = Math.max(0, Math.min(ss.length - 1, i));
  ss[current].scrollIntoView({ behavior: "smooth" });
}
function updateSection() {
  let ss = sections(),
    best = 0,
    min = Infinity;
  ss.forEach((s, i) => {
    let d = Math.abs(s.getBoundingClientRect().top - 72);
    if (d < min) {
      min = d;
      best = i;
    }
  });
  current = best;
  $("#slideStatus").textContent =
    `${String(current + 1).padStart(2, "0")} / ${String(ss.length).padStart(2, "0")}`;
  $$(".nav-dot").forEach((b, i) => b.classList.toggle("active", i === current));
  let max = document.documentElement.scrollHeight - innerHeight;
  $("#progressBar").style.width = `${max ? (scrollY / max) * 100 : 0}%`;
}
function initNav() {
  let mobile = $("#mobileNav");
  $$(".nav-dot").forEach((b, i) => {
    b.onclick = () => goTo(i);
    let c = b.cloneNode(true);
    c.onclick = () => {
      goTo(i);
      mobile.hidden = true;
      $("#menuToggle").setAttribute("aria-expanded", "false");
    };
    mobile.append(c);
  });
  $("#menuToggle").onclick = (e) => {
    let open = e.currentTarget.getAttribute("aria-expanded") === "true";
    e.currentTarget.setAttribute("aria-expanded", String(!open));
    mobile.hidden = open;
  };
  $("#prevSlide").onclick = () => goTo(current - 1);
  $("#nextSlide").onclick = () => goTo(current + 1);
  $$("[data-jump]").forEach(
    (b) =>
      (b.onclick = () =>
        $("#" + b.dataset.jump).scrollIntoView({ behavior: "smooth" })),
  );
  addEventListener("scroll", updateSection, { passive: true });
  addEventListener("keydown", (e) => {
    if (
      ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)
    )
      return;
    if (["ArrowRight", "PageDown"].includes(e.key)) goTo(current + 1);
    if (["ArrowLeft", "PageUp"].includes(e.key)) goTo(current - 1);
    if (e.key === "Home") goTo(0);
    if (e.key === "End") goTo(sections().length - 1);
  });
  updateSection();
}
document.addEventListener("DOMContentLoaded", () => {
  $("#typeCount").textContent = reactors.length;
  initFilters();
  initCompare();
  renderFusion("magnetic");
  renderFlow("batch");
  renderRepos();
  initFacilityMap();
  initCompanies();
  initNav();
  $(".dialog-close").onclick = () => $("#reactorDialog").close();
  $("#reactorDialog").onclick = (e) => {
    if (e.target === $("#reactorDialog")) e.target.close();
  };
  $$(".family-tab").forEach(
    (b) =>
      (b.onclick = () => {
        $$(".family-tab").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        renderFusion(b.dataset.fusion);
      }),
  );
  $$(".flow-selector button").forEach(
    (b) =>
      (b.onclick = () => {
        $$(".flow-selector button").forEach((x) =>
          x.setAttribute("aria-selected", "false"),
        );
        b.setAttribute("aria-selected", "true");
        renderFlow(b.dataset.flow);
      }),
  );
  $("#repoSearch").oninput = renderRepos;
});
