// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — primary field detail contract conformance
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const file = path.resolve(
  __dirname,
  "../04_interactive_presentation/research-primary-assertions.js",
);
const api = require("../04_interactive_presentation/research-primary-assertions.js");
const refusal =
  '<p role="status">Primary research decisions are unavailable.</p>';
const empty = {
  stable_id: "wikidata-contract-fixture",
  field: "purpose",
  value: "",
  selection: "unknown",
  source_id: "",
  source_title: "",
  source_url: "",
  source_sha256: "",
  source_class: "",
  source_document_date: "",
  source_capture_date: "",
  locator: "",
  scope: "Contract scope <&>\"'",
  rights: "",
  date_precision: "",
  assertion_basis: "Fixture checks software, not scientific acceptance.",
  related_evidence: "",
};
const selected = {
  ...empty,
  selection: "selected",
  value: "Exact fixture purpose <&>\"'",
  source_id: "fixture",
  source_title: "Original source syntax fixture",
  source_url: "https://example.org/source",
  source_sha256: "a".repeat(64),
  source_class: "native_original_html",
  source_document_date: "2025-06",
  source_capture_date: "2026-10-03",
  locator: "Fixture section",
  rights: "No publisher reuse licence conferred",
};
/** @type {import("../04_interactive_presentation/research-primary-assertions.js").RelatedResearchCitation} */
const related = {
  source_id: "related fixture",
  original_url: "https://example.org/related",
  sha256: "b".repeat(64),
};

test("every actual primary decision preserves its facility, source digest and disposition", () => {
  const filename = path.resolve(
    __dirname,
    "../04_interactive_presentation/data/global_reactors.sample.json",
  );
  const bytes = fs.readFileSync(filename);
  /** @type {unknown} */
  const document = JSON.parse(bytes.toString("utf8"));
  assert.ok(
    document &&
      typeof document === "object" &&
      "records" in document &&
      Array.isArray(document.records),
  );
  const candidates = /** @type {unknown[]} */ (document.records);
  let count = 0;
  const observed = new Set();
  for (const candidate of candidates) {
    assert.ok(candidate && typeof candidate === "object");
    if (!("research_primary_assertions" in candidate)) continue;
    assert.ok("id" in candidate && typeof candidate.id === "string");
    assert.ok(Array.isArray(candidate.research_primary_assertions));
    const html = api.render(candidate.research_primary_assertions);
    assert.notEqual(html, refusal);
    const decisions =
      /** @type {import("../04_interactive_presentation/research-primary-assertions.js").ResearchPrimaryDecision[]} */ (
        candidate.research_primary_assertions
      );
    for (const decision of decisions) {
      assert.equal(decision.stable_id, candidate.id);
      observed.add(decision.selection);
      if (decision.source_id) {
        assert.ok(html.includes(decision.source_sha256));
        assert.ok(html.includes(decision.source_url.replaceAll("&", "&amp;")));
      }
      count += 1;
    }
  }
  assert.equal(count, 358);
  assert.deepEqual([...observed].sort(), [
    "composite",
    "held",
    "never_critical",
    "not_applicable",
    "planned",
    "selected",
    "unknown",
  ]);
  assert.deepEqual(fs.readFileSync(filename), bytes);
});

test("selected, held and individual no-fill dispositions preserve their meaning", () => {
  for (const selection of [
    "unknown",
    "not_applicable",
    "never_critical",
    "planned",
    "composite",
    "held",
  ]) {
    const html = api.render([{ ...empty, selection }]);
    assert.notEqual(html, refusal);
    assert.ok(html.includes("No admissible original source"));
    assert.ok(html.includes("&lt;&amp;&gt;&quot;&#39;"));
  }
  for (const source_class of [
    "native_original_pdf",
    "native_original_html",
    "native_original_facsimile",
  ]) {
    const html = api.render([{ ...selected, source_class }]);
    assert.ok(html.includes("Selected value"));
    assert.ok(html.includes(selected.source_sha256));
    assert.ok(html.includes(selected.rights));
    assert.ok(html.includes("document 2025-06 · retrieved 2026-10-03"));
    assert.ok(html.includes("&lt;&amp;&gt;&quot;&#39;"));
  }
  for (const source_class of [
    "tool_rendered_author_page_lead",
    "native_discovery_registry_json",
  ]) {
    assert.ok(
      api
        .render([{ ...selected, selection: "held", source_class }])
        .includes("Unresolved claim"),
    );
    assert.equal(api.render([{ ...selected, source_class }]), refusal);
  }
  assert.ok(
    api
      .render([
        { ...selected, source_document_date: "", source_capture_date: "" },
      ])
      .includes("document date unknown · retrieved date unknown"),
  );
});

test("event precision, calendar validity and source dates remain separate", () => {
  for (const [value, date_precision] of [
    ["1957", "year"],
    ["1957-08", "month"],
    ["1957-08-27", "day"],
    ["2000-02-29", "day"],
  ]) {
    const html = api.render([
      { ...selected, field: "first_criticality", value, date_precision },
    ]);
    assert.ok(html.includes(`Event precision: ${date_precision}`));
    assert.ok(html.includes(value));
  }
  assert.ok(
    api
      .render([
        {
          ...selected,
          field: "first_criticality",
          value: "2028",
          date_precision: "year",
          selection: "held",
        },
      ])
      .includes("Unresolved claim"),
  );
  assert.notEqual(
    api.render([
      {
        ...selected,
        field: "first_criticality",
        value: "1957",
        date_precision: "year",
        source_capture_date: "",
      },
    ]),
    refusal,
  );
  for (const value of [
    "0000",
    "1957-13",
    "1957-00",
    "1957-02-30",
    "1900-02-29",
    "1957-08-00",
    "1957/08",
    "2028",
  ]) {
    assert.equal(
      api.render([
        {
          ...selected,
          field: "first_criticality",
          value,
          date_precision:
            value.length === 4 ? "year" : value.length === 7 ? "month" : "day",
        },
      ]),
      refusal,
    );
  }
  assert.equal(
    api.render([
      {
        ...selected,
        field: "first_criticality",
        value: "1957",
        date_precision: "day",
      },
    ]),
    refusal,
  );
  assert.equal(
    api.render([{ ...selected, source_document_date: "2025-02-30" }]),
    refusal,
  );
  assert.equal(
    api.render([{ ...selected, source_capture_date: "2025-02-30" }]),
    refusal,
  );
});

test("related citations retain alternate values and cannot inject unsafe links", () => {
  for (const citation of [
    related,
    {
      ...related,
      locator: "Page 4",
      admissibility: "Earlier claim <&>",
      reported_value: "1957",
    },
  ]) {
    const html = api.render([
      { ...selected, related_evidence: JSON.stringify([citation]) },
    ]);
    assert.ok(html.includes(citation.sha256));
    assert.ok(html.includes(citation.original_url));
    assert.ok(
      html.includes(
        citation.reported_value ? "reported 1957" : "location not supplied",
      ),
    );
  }
  for (const related_evidence of [
    "{",
    "null",
    "{}",
    "[null]",
    "[true]",
    "[[]]",
    JSON.stringify([{ ...related, extra: "unbound" }]),
    JSON.stringify([{ ...related, locator: 1 }]),
    JSON.stringify([{ ...related, locator: "line\nbreak" }]),
    JSON.stringify([{ ...related, source_id: "" }]),
    JSON.stringify([{ source_id: related.source_id, sha256: related.sha256 }]),
    JSON.stringify([
      { source_id: related.source_id, original_url: related.original_url },
    ]),
    JSON.stringify([{ ...related, original_url: "http://example.org" }]),
    JSON.stringify([{ ...related, sha256: "bad" }]),
  ]) {
    assert.equal(api.render([{ ...selected, related_evidence }]), refusal);
  }
  assert.notEqual(
    api.render([{ ...selected, related_evidence: "[]" }]),
    refusal,
  );
});

test("malformed and unsupported rows refuse once without parser diagnostics", () => {
  assert.equal(api.render([]), "");
  for (const rows of [
    null,
    {},
    "invalid",
    [null],
    [true],
    [{ ...selected, extra: "unbound" }],
    [selected, selected],
    [selected, { ...empty, field: "operator", stable_id: "other" }],
  ])
    assert.equal(api.render(rows), refusal);
  for (const key of Object.keys(selected)) {
    assert.equal(api.render([{ ...selected, [key]: null }]), refusal);
    assert.equal(api.render([{ ...selected, [key]: "line\nbreak" }]), refusal);
  }
  for (const change of [
    { stable_id: "" },
    { field: "unbound" },
    { selection: "unreviewed" },
    { scope: "" },
    { assertion_basis: "" },
    { source_title: "" },
    { source_url: "" },
    { source_sha256: "changed" },
    { source_class: "guess" },
    { locator: "" },
    { rights: "" },
    { value: "" },
    { source_id: "" },
    { date_precision: "year" },
  ])
    assert.equal(api.render([{ ...selected, ...change }]), refusal);
  assert.equal(
    api.render([{ ...empty, selection: "selected", value: "unbound" }]),
    refusal,
  );
  assert.equal(
    api.render([{ ...empty, selection: "held", value: "unbound" }]),
    refusal,
  );
  assert.equal(api.render([{ ...empty, value: "unbound" }]), refusal);
  for (const key of [
    "source_title",
    "source_url",
    "source_sha256",
    "source_class",
    "locator",
    "rights",
  ])
    assert.equal(
      api.render([{ ...empty, [key]: "partial citation" }]),
      refusal,
    );
  for (const source_url of [
    "javascript:alert(1)",
    "http://example.org/",
    "https:///no-host",
    "https://user@example.org/",
    "https://user:secret@example.org/",
    "https://example.org:0",
    "https://example.org:65536",
    "https://[broken",
    "https://example.org\\escape",
    "https://example.org/space here",
  ])
    assert.equal(api.render([{ ...selected, source_url }]), refusal);
});

test("the actual browser script exports the same renderer without CommonJS", () => {
  const context = {
    URL,
    PrimaryResearchAssertions: /** @type {typeof api|undefined} */ (undefined),
  };
  vm.runInNewContext(fs.readFileSync(file, "utf8"), context, {
    filename: file,
  });
  assert.ok(context.PrimaryResearchAssertions);
  assert.equal(
    context.PrimaryResearchAssertions.render([selected]),
    api.render([selected]),
  );
  assert.ok(
    api
      .render([selected, { ...empty, field: "operator" }])
      .includes("Operator"),
  );
});
