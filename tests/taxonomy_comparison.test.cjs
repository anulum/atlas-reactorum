// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound comparison and share-link contracts
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const { createHash } = require("node:crypto");
require("../04_interactive_presentation/taxonomy-claim-sources.js");
require("../04_interactive_presentation/taxonomy-evidence-profile.js");
require("../04_interactive_presentation/taxonomy-comparison.js");
const api = globalThis.AtlasTaxonomyComparison;
const { loadProfileFixture } = require("./evidence_profile_fixture.cjs");
const { findRequired } = require("./taxonomy_citation_fixture.cjs");
const { document } = loadProfileFixture(path.resolve(__dirname, ".."));
const page = "https://example.org/atlas/index.html?language=en#taxonomy";
const ids = ["pwr", "tokamak"];

/**
 * Bind a numeric rendering control to an actual original profile claim.
 * @param {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceProfile} profile Original validated profile.
 * @param {number} [value] Explicit test value, zero by default.
 * @returns {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasKnownParameter} Source-bound numerical-context control.
 */
function known(profile, value = 0) {
  return {
    id: "temperature",
    state: "known",
    value,
    unit: "K",
    conditions: "Declared test conditions",
    system_boundary: "Declared test boundary",
    conversion_method: "identity",
    claim_ids: [profile.claims[0].claim_id],
    original_text: "Source-bound parameter rendering control",
  };
}

/**
 * Select the original non-numeric parameter before changing its explanation.
 * @param {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasEvidenceProfile} profile Actual fixture profile.
 * @returns {import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasMissingParameter} Existing missing-value record.
 */
function missingParameter(profile) {
  const parameter = profile.parameters[0];
  assert.ok(parameter.state !== "known");
  return parameter;
}

test("whole profile snapshot equals independently hashed complete UTF-8 content", async () => {
  assert.equal(
    await api.snapshot(document),
    createHash("sha256").update(JSON.stringify(document)).digest("hex"),
  );
  const edited = structuredClone(document);
  missingParameter(edited.records[edited.records.length - 1]).reason +=
    " An added reason";
  assert.notEqual(await api.snapshot(edited), await api.snapshot(document));
  assert.deepEqual(edited.inputs, document.inputs);
});

test("every actual entry participates in an ordered export retaining exact claims, sources and rights", async () => {
  const snapshot = await api.snapshot(document);
  let checked = 0;
  for (const record of document.records) {
    const selected = [
      record.entry_id,
      record.entry_id === ids[0] ? ids[1] : ids[0],
    ];
    const bundle = await api.createComparison(document, snapshot, selected);
    assert.equal(bundle.schema_version, "atlas-comparison-1.0.0");
    assert.deepEqual(bundle.selection.entry_ids, selected);
    assert.deepEqual(
      bundle.profiles,
      selected.map((id) =>
        document.records.find((profile) => profile.entry_id === id),
      ),
    );
    const used = new Set(
      bundle.profiles.flatMap((profile) =>
        profile.claims.map((claim) => claim.citation.source_id),
      ),
    );
    assert.deepEqual(
      bundle.sources,
      document.sources.filter((source) => used.has(source.id)),
    );
    assert.deepEqual(bundle.snapshot, {
      profile_sha256: snapshot,
      inputs: document.inputs,
    });
    assert.equal(bundle.metadata_license, "AGPL-3.0-or-later");
    assert.equal(
      bundle.source_rights,
      "catalogue-only; original not redistributed",
    );
    assert.equal(bundle.parameter_comparisons[0].state, "not_comparable");
    assert.ok(
      bundle.profiles.every(
        (profile) => !profile.review_disposition.complete_entry_review,
      ),
    );
    checked++;
  }
  assert.equal(checked, 135);
  assert.deepEqual(
    await api.createComparison(document, snapshot, ["tokamak", "pwr", "bwr"]),
    await api.createComparison(document, snapshot, ["tokamak", "pwr", "bwr"]),
  );
});

for (const selected of [
  null,
  {},
  [],
  ["pwr"],
  ["pwr", "tokamak", "bwr", "phwr"],
  ["pwr", "pwr"],
  ["pwr", ""],
  ["pwr", " "],
  ["pwr", 3],
]) {
  test(`invalid selections are refused without silently dropping entries: ${JSON.stringify(selected)}`, async () => {
    await assert.rejects(
      api.createComparison(document, await api.snapshot(document), selected),
    );
    assert.throws(() => api.shareUrl(page, "a".repeat(64), selected));
  });
}

for (const damaged of [null, {}, { records: {} }, { records: [] }]) {
  test(`snapshot refuses unavailable catalogue ${JSON.stringify(damaged)}`, async () => {
    await assert.rejects(
      () => Reflect.apply(api.snapshot, api, [damaged]),
      /unavailable/,
    );
  });
}

test("unsupported, missing and altered profile data refuse explicit snapshot restoration", async () => {
  const snapshot = await api.snapshot(document);
  for (const changedHash of ["", "INVALID", "A".repeat(64), "0".repeat(64)]) {
    await assert.rejects(
      api.createComparison(document, changedHash, ids),
      /snapshot/,
    );
    if (changedHash !== "0".repeat(64))
      assert.throws(() => api.shareUrl(page, changedHash, ids));
  }
  await assert.rejects(
    api.createComparison(document, snapshot, ["pwr", "unknown"]),
    /does not exist/,
  );
  const edited = structuredClone(document);
  missingParameter(edited.records[edited.records.length - 1]).reason +=
    " Updated";
  await assert.rejects(
    api.createComparison(edited, snapshot, ids),
    /not substituted/,
  );
  Reflect.set(edited, "schema_version", "future");
  await assert.rejects(api.snapshot(edited));
});

test("actual in-flight source edit cannot pair an older digest with newer exported content", async () => {
  const editable = structuredClone(document);
  const before = structuredClone(editable);
  const snapshot = await api.snapshot(editable);
  const comparison = api.createComparison(editable, snapshot, ids);
  editable.sources[0].title = "A later source title";
  missingParameter(editable.records[0]).reason = "A later reason";
  const exported = await comparison;
  const expected = await api.createComparison(before, snapshot, ids);
  assert.deepEqual(exported, expected);
  assert.notDeepEqual(exported.profiles[0], editable.records[0]);
});

for (const url of [
  page,
  "http://localhost:8080/index.html",
  "file:///atlas/index.html",
]) {
  test(`share links preserve ordered stable IDs and the static document URL: ${url}`, async () => {
    const snapshot = await api.snapshot(document);
    const shared = api.shareUrl(url, snapshot, ["tokamak", "pwr", "bwr"]);
    assert.deepEqual(api.readUrl(shared), {
      snapshot,
      entryIds: ["tokamak", "pwr", "bwr"],
    });
    assert.equal(new URL(shared).pathname, new URL(url).pathname);
    assert.equal(new URL(shared).search, new URL(url).search);
    assert.equal(
      api.shareUrl(shared, snapshot, ["tokamak", "pwr", "bwr"]),
      shared,
    );
  });
}

/**
 * Require the parsed selection carried by an actual comparison share URL.
 * @param {string} url Actual generated share link.
 * @returns {{snapshot: string, entryIds: string[]}} Existing comparison state.
 */
function assertedSelection(url) {
  const selection = api.readUrl(url);
  assert.ok(selection !== null);
  return selection;
}

test("URL escaping preserves identities and never changes their display order", () => {
  const identities = ["single&encoded", "apostrophe'<tag>"];
  const shared = api.shareUrl(page, "a".repeat(64), identities);
  assert.deepEqual(assertedSelection(shared).entryIds, identities);
  assert.equal(api.readUrl(page), null);
  assert.equal(api.readUrl("https://example.org/index.html#compare"), null);
});

for (const url of [
  "data:text/html,example",
  "javascript:void(0)",
  "https://user:password@example.org/index.html",
  "not an absolute url",
]) {
  test(`unsupported page URLs cannot become share links: ${url}`, () => {
    assert.throws(() => api.shareUrl(url, "a".repeat(64), ids));
  });
}

for (const query of [
  "",
  "version=2",
  "version=1&version=1",
  "version=1&snapshot=bad",
  `version=1&snapshot=${"a".repeat(64)}&snapshot=${"a".repeat(64)}`,
  `version=1&snapshot=${"a".repeat(64)}&unknown=true`,
  `version=1&snapshot=${"a".repeat(64)}&entry=pwr`,
  `version=1&snapshot=${"a".repeat(64)}&entry=pwr&entry=pwr`,
]) {
  test(`malformed share state visibly refuses instead of selecting defaults: ${query}`, () => {
    assert.throws(() =>
      api.readUrl("https://example.org/index.html#compare?" + query),
    );
  });
}

test("real comparison renders original text, source locators and missing parameter reasons", async () => {
  const snapshot = await api.snapshot(document);
  const rendered = await api.renderComparison(document, snapshot, ids);
  assert.deepEqual(
    rendered.bundle,
    await api.createComparison(document, snapshot, ids),
  );
  assert.match(rendered.html, /classification labels remain open/);
  assert.match(rendered.html, /not comparable/);
  for (const profile of rendered.bundle.profiles) {
    assert.ok(rendered.html.includes(profile.taxonomy_record.name));
    assert.ok(rendered.html.includes(missingParameter(profile).reason));
    for (const claim of profile.claims) {
      const source = findRequired(
        document.sources,
        (source) => source.id === claim.citation.source_id,
      );
      assert.ok(rendered.html.includes(source.url.replaceAll("&", "&amp;")));
    }
  }
});

test("zero and equal contexts remain metadata values, with no numerical merge or acceptance", async () => {
  const edited = structuredClone(document);
  for (const id of ids) {
    const profile = findRequired(
      edited.records,
      (profile) => profile.entry_id === id,
    );
    profile.parameters = [known(profile)];
  }
  const rendered = await api.renderComparison(
    edited,
    await api.snapshot(edited),
    ids,
  );
  assert.equal(
    rendered.bundle.parameter_comparisons[0].state,
    "same_declared_context",
  );
  assert.match(rendered.html, /0 K/);
  assert.match(rendered.html, /not scientific acceptance/);
  assert.match(rendered.html, /no numerical merging/);
});

for (const field of /** @type {("unit"|"conditions"|"system_boundary"|"conversion_method")[]} */ ([
  "unit",
  "conditions",
  "system_boundary",
  "conversion_method",
])) {
  test(`different ${field} refuses numeric comparability`, async () => {
    const edited = structuredClone(document);
    for (const id of ids) {
      const profile = findRequired(
        edited.records,
        (profile) => profile.entry_id === id,
      );
      profile.parameters = [known(profile, 1)];
    }
    const changed = findRequired(
      edited.records,
      (profile) => profile.entry_id === "tokamak",
    ).parameters[0];
    assert.ok(changed.state === "known");
    changed[field] += " different";
    const rendered = await api.renderComparison(
      edited,
      await api.snapshot(edited),
      ids,
    );
    assert.equal(
      rendered.bundle.parameter_comparisons[0].state,
      "not_comparable",
    );
    assert.ok(rendered.bundle.parameter_comparisons[0].reason.includes(field));
    assert.ok(rendered.html.includes("No numerical conversion or merging"));
  });
}

/** @type {[string, (parameter: import("../04_interactive_presentation/taxonomy-evidence-profile.js").AtlasKnownParameter) => void][]} */
const parameterMutations = [
  [
    "nonfinite",
    (parameter) => {
      parameter.value = Infinity;
    },
  ],
  [
    "empty unit",
    (parameter) => {
      parameter.unit = " ";
    },
  ],
  [
    "absent context",
    (parameter) => {
      Reflect.deleteProperty(parameter, "conditions");
    },
  ],
  [
    "nonarray claims",
    (parameter) => {
      Reflect.set(parameter, "claim_ids", null);
    },
  ],
  [
    "no claims",
    (parameter) => {
      parameter.claim_ids = [];
    },
  ],
  [
    "unknown claim",
    (parameter) => {
      parameter.claim_ids = ["unknown"];
    },
  ],
  [
    "unknown missing state",
    (parameter) => {
      Reflect.set(parameter, "state", "absent");
    },
  ],
  [
    "no missing reason",
    (parameter) => {
      Reflect.set(parameter, "state", "not_reviewed");
      Reflect.set(parameter, "reason", " ");
    },
  ],
  [
    "nontext reason",
    (parameter) => {
      Reflect.set(parameter, "state", "not_reviewed");
      Reflect.set(parameter, "reason", null);
    },
  ],
];
for (const [label, mutate] of parameterMutations) {
  test(`source context refuses ${label}`, async () => {
    const edited = structuredClone(document);
    const profile = edited.records[0];
    const parameter = known(profile);
    profile.parameters = [parameter];
    mutate(parameter);
    await assert.rejects(
      api.createComparison(edited, await api.snapshot(edited), ids),
    );
  });
}

test("absent parameter metadata and every explicit missing state stay visible", async () => {
  const edited = structuredClone(document);
  for (const state of [
    "not_reported",
    "not_reviewed",
    "not_applicable",
    "disputed",
  ]) {
    Reflect.set(edited.records[0].parameters[0], "state", state);
    findRequired(
      edited.records,
      (profile) => profile.entry_id === "tokamak",
    ).parameters = [];
    const rendered = await api.renderComparison(
      edited,
      await api.snapshot(edited),
      ids,
    );
    assert.match(rendered.html, /No parameter metadata in this profile/);
    assert.ok(rendered.html.includes(state.replaceAll("_", " ")));
    assert.equal(
      rendered.bundle.parameter_comparisons[0].state,
      "not_comparable",
    );
  }
});

test("source descriptions and original fields escape HTML rather than becoming controls", async () => {
  const edited = structuredClone(document);
  const profile = edited.records[0];
  profile.taxonomy_record.name = '<img src=x onerror="bad">&\'';
  missingParameter(profile).reason = "<script>bad</script>";
  const rendered = await api.renderComparison(
    edited,
    await api.snapshot(edited),
    ids,
  );
  assert.ok(
    rendered.html.includes(
      "&lt;img src=x onerror=&quot;bad&quot;&gt;&amp;&#39;",
    ),
  );
  assert.ok(rendered.html.includes("&lt;script&gt;bad&lt;/script&gt;"));
  assert.ok(!rendered.html.includes("<script>bad</script>"));
});
