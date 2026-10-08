// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-curated learning questions
"use strict";

/**
 * Authored reading route bound to original example and answer identities.
 * @typedef {object} AtlasLearningPath
 * @property {string} id Stable route identity.
 * @property {string} title Original question title.
 * @property {string} objective Original learning objective.
 * @property {string} prompt Original source-reading prompt.
 * @property {string[]} entry_ids Original examples in authored display order.
 * @property {string} question Original source-bound question.
 * @property {string} answer_entry_id Original supporting example identity.
 * @property {string} answer_claim_id Original supporting claim identity.
 * @property {string} answer_statement Exact original supporting statement.
 * @property {string} limitation Explicit original evidence boundary.
 */

/**
 * Complete authored learning definitions; the digest binds every original cell.
 * @typedef {object} AtlasLearningCatalogueDocument
 * @property {string} schema_version Original learning-definition schema.
 * @property {{term: string, meaning: string}[]} glossary Original displayed terms.
 * @property {AtlasLearningPath[]} paths Complete original reading routes.
 */

/** @type {Readonly<AtlasLearningCatalogueDocument>} */
var AtlasLearningCatalogue = Object.freeze({
  schema_version: "atlas-learning-paths-1.0.0",
  glossary: [
    {
      term: "Principle",
      meaning:
        "The original catalogue statement describing the process or configuration.",
    },
    {
      term: "Claim",
      meaning:
        "An exact statement linked to a source and its stated support boundary.",
    },
    {
      term: "Source locator",
      meaning:
        "The cited section or page where the supporting material can be inspected.",
    },
    {
      term: "Evidence scope",
      meaning:
        "What the record establishes and what its evidence leaves unresolved.",
    },
    {
      term: "Missing value",
      meaning:
        "An explicitly absent or unreviewed parameter, with its reason retained.",
    },
    {
      term: "System boundary",
      meaning:
        "The declared extent of a reported quantity; incompatible contexts cannot be merged.",
    },
  ],
  paths: [
    {
      id: "water-loops",
      title: "Where does the steam come from?",
      objective:
        "Distinguish the two original light-water reactor principle descriptions.",
      prompt:
        "Read both principles, then trace the selected statement to its source.",
      entry_ids: ["pwr", "bwr"],
      question: "Which cited principle says that coolant boils in the core?",
      answer_entry_id: "bwr",
      answer_claim_id: "bwr:principle:1",
      answer_statement:
        "Coolant boils in the core and supplies steam directly to the turbine.",
      limitation:
        "A reactor-type description does not qualify an individual plant or its performance.",
    },
    {
      id: "magnetic-confinement",
      title: "What supplies the confining field?",
      objective:
        "Identify the stated distinction between tokamak and stellarator configurations.",
      prompt:
        "Compare the original magnetic-field descriptions and retain their experimental scope.",
      entry_ids: ["tokamak", "stellarator"],
      question:
        "Which cited principle does not require a large toroidal plasma current?",
      answer_entry_id: "stellarator",
      answer_claim_id: "stellarator:principle:1",
      answer_statement:
        "Three-dimensional external magnetic fields confine plasma without requiring large toroidal plasma current.",
      limitation:
        "Confinement descriptions do not establish an integrated commercial power plant.",
    },
    {
      id: "chemical-flow",
      title: "Does material pass through continuously?",
      objective:
        "Separate the batch principle from the two ideal continuous-flow descriptions.",
      prompt:
        "Inspect all three original principles; an ideal model is not a measured vessel.",
      entry_ids: [
        "batch-reactor",
        "continuous-stirred-tank-reactor-cstr",
        "plug-flow-tubular-reactor",
      ],
      question:
        "Which cited principle explicitly has no continuous material throughput?",
      answer_entry_id: "batch-reactor",
      answer_claim_id: "batch-reactor:principle:1",
      answer_statement:
        "Reactants are charged and react without continuous material throughput.",
      limitation:
        "These descriptions do not supply a residence time or a measured mixing distribution.",
    },
    {
      id: "wastewater-configurations",
      title: "How are treatment phases organised?",
      objective:
        "Distinguish a timed treatment cycle from the stated upflow biomass-retention configuration.",
      prompt:
        "Read the source-bound sequence and bed descriptions without inferring treatment efficiency.",
      entry_ids: [
        "sequencing-batch-reactor",
        "upflow-anaerobic-sludge-blanket-reactor",
      ],
      question:
        "Which cited principle lists fill, react, settle, draw and idle phases?",
      answer_entry_id: "sequencing-batch-reactor",
      answer_claim_id: "sequencing-batch-reactor:principle:1",
      answer_statement:
        "A wastewater-treatment basin cycles through fill, react, settle, draw and idle phases.",
      limitation:
        "The named process configuration does not establish a specific facility's current operation.",
    },
    {
      id: "electrochemical-processes",
      title: "What process does the membrane support?",
      objective:
        "Read the distinction between the two original membrane-based process descriptions.",
      prompt:
        "Trace water splitting and fuel oxidation to their own source statements.",
      entry_ids: ["pem-water-electrolyser", "pem-fuel-cell"],
      question: "Which cited principle names water-splitting electrodes?",
      answer_entry_id: "pem-water-electrolyser",
      answer_claim_id: "pem-water-electrolyser:principle:1",
      answer_statement:
        "A proton-exchange membrane transports ions between water-splitting electrodes.",
      limitation:
        "A shared membrane term does not make the two processes or their efficiencies interchangeable.",
    },
    {
      id: "neutrons-and-energy",
      title: "What does a neutron-source description establish?",
      objective:
        "Distinguish the cited device category from a whole-plant energy claim.",
      prompt:
        "Inspect the classification statement, the original evidence scope and the missing parameters.",
      entry_ids: [
        "accelerator-beam-target-fusion-neutron-generator",
        "laser-indirect-drive-icf",
      ],
      question:
        "Which cited classification explicitly identifies neutron-source devices?",
      answer_entry_id: "accelerator-beam-target-fusion-neutron-generator",
      answer_claim_id:
        "accelerator-beam-target-fusion-neutron-generator:classification:1",
      answer_statement:
        "Accelerator beam-target fusion neutron generators are neutron-source devices.",
      limitation:
        "The neutron-source record makes no net-energy, gain or power claim. Missing parameters remain unresolved.",
    },
  ],
});

globalThis.AtlasLearningCatalogue = AtlasLearningCatalogue;
