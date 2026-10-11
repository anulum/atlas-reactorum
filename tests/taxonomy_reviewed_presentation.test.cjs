// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — genuine source/current profile presentation and downloads.
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const vm = require("node:vm");
const { createHash } = require("node:crypto");
const { loadAuthorReviewFixture } = require("./author_review_fixture.cjs");
const {
  exportTaxonomy,
} = require("../04_interactive_presentation/scripts/export_taxonomy.cjs");
require("../04_interactive_presentation/presentation-text.js");
const view = require("../04_interactive_presentation/taxonomy-reviewed-presentation.js");
const reader = require("../04_interactive_presentation/taxonomy-reviewed-profiles.js");
const root = path.resolve(__dirname, "..");
const fixture = loadAuthorReviewFixture(root);
const authorInput =
  process.env.ATLAS_AUTHOR_REVIEW_INPUT ||
  path.join(root, "metadata/evidence_profiles/author_reviews.json");
const inputs = {
  ...fixture.baseline.inputs,
  original_profiles_sha256: createHash("sha256")
    .update(
      fs.readFileSync(
        path.join(root, "metadata/evidence_profiles/profiles.json"),
      ),
    )
    .digest("hex"),
  author_reviews_sha256: createHash("sha256")
    .update(fs.readFileSync(authorInput))
    .digest("hex"),
};
const document = reader.read(
  JSON.parse(
    fs.readFileSync(
      path.join(
        root,
        "04_interactive_presentation/data/taxonomy-reviewed-profiles.json",
      ),
      "utf8",
    ),
  ),
  inputs,
  fixture.baseline,
);

test("every genuine selected download retains all original/current relationships and supporting sources", () => {
  const before = JSON.stringify(document);
  for (const [index, row] of document.records.entries()) {
    const exported =
      /** @type {ReturnType<typeof reader.readProfile> & {schema_version:string,selected_entry_id:string,inputs:typeof inputs,source_rights:string,author_review_context:{author:string,reviewed_on:string},sources:import("../04_interactive_presentation/scripts/taxonomy_citations.cjs").CitationSource[]}} */ (
        JSON.parse(
          view.exportProfile(document, inputs, fixture.baseline, row.id),
        )
      );
    assert.equal(exported.schema_version, "atlas-entry-reviewed-profile-2.1.0");
    assert.equal(exported.selected_entry_id, row.id);
    assert.deepEqual(exported.taxonomy_record, row);
    assert.deepEqual(
      exported.original_profile,
      fixture.baseline.records[index],
    );
    assert.deepEqual(exported.author_review, fixture.review.records[index]);
    assert.deepEqual(exported.author_review_context, {
      author: fixture.review.author,
      reviewed_on: fixture.review.reviewed_on,
    });
    assert.deepEqual(exported.inputs, inputs);
    assert.equal(
      exported.source_rights,
      "catalogue-only; original not redistributed",
    );
    const needed = new Set([
      ...fixture.baseline.records[index].claims.map(
        (claim) => claim.citation.source_id,
      ),
      ...Object.values(fixture.review.records[index].fields).flatMap(
        (field) => field.source_ids,
      ),
      ...fixture.review.records[index].observations.map(
        (observation) => observation.source_id,
      ),
    ]);
    assert.deepEqual(
      new Set(exported.sources.map((source) => source.id)),
      needed,
    );
    const html = view.render(document, inputs, fixture.baseline, row.id);
    assert.match(html, /All 21 field assessments/);
    assert.match(
      html,
      /Author review covers all original fields and selected sources/,
    );
    assert.match(html, /Current activity is unknown/);
    assert.match(html, /Independent entry acceptance has not been recorded/);
    assert.match(html, /class="reviewed-profile-download"/);
  }
  assert.equal(JSON.stringify(document), before);
});

test("actual dated observations preserve evidence scope, locators and unknown dates", () => {
  const identities = document.author_reviews.records
    .filter((row) => row.observations.length)
    .map((row) => row.entry_id)
    .concat(["phwr-candu"]);
  const html = identities
    .map((identity) =>
      view.render(document, inputs, fixture.baseline, identity),
    )
    .join("\n");
  assert.match(html, /PDF page\(s\)/);
  assert.match(html, /HTML\/XML section locator/);
  assert.match(html, /Publication: Unknown/);
  assert.match(html, /Original retrieval date unknown/);
  assert.match(html, /No attained stage has been assessed here/);
  assert.match(html, /No additional source-specific observations/);
  assert.match(html, /1956 \(year\)/);
});

test("a damaged final entry refuses both early-entry rendering and download", () => {
  const damaged = structuredClone(document);
  const last = damaged.records.at(-1);
  assert.ok(last);
  last.name = "unassessed final caption";
  assert.throws(
    () => view.render(damaged, inputs, fixture.baseline, "pwr"),
    /current rows differ/,
  );
  assert.throws(
    () => view.exportProfile(damaged, inputs, fixture.baseline, "pwr"),
    /current rows differ/,
  );
  assert.throws(
    () => view.render(document, inputs, fixture.baseline, "absent-entry"),
    /selection is absent/,
  );
  assert.throws(
    () =>
      view.exportProfile(
        document,
        { ...inputs, author_reviews_sha256: "0".repeat(64) },
        fixture.baseline,
        "pwr",
      ),
    /source hashes differ/,
  );
});

test("real author input is escaped after genuine native production, including the download", (context) => {
  const dir = fs.mkdtempSync(
    path.join(os.tmpdir(), "atlas-reviewed-presentation-"),
  );
  context.after(() => fs.rmSync(dir, { recursive: true }));
  for (const relative of [
    "04_interactive_presentation/data/taxonomy-expanded.js",
    "metadata/taxonomy_audit/claim_citations.json",
    "metadata/taxonomy_audit/audit.tsv",
    "metadata/evidence_profiles/profiles.json",
  ]) {
    const target = path.join(dir, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(root, relative), target);
  }
  const review = structuredClone(fixture.review);
  review.records[0].fields.principle.assessment +=
    " HTML encoding probe: <img src=x onerror='alert(1)'>&";
  const input = path.join(
    dir,
    "metadata/evidence_profiles/author_reviews.json",
  );
  fs.writeFileSync(input, JSON.stringify(review, null, 2) + "\n");
  exportTaxonomy(dir, input);
  const produced = JSON.parse(
    fs.readFileSync(
      path.join(
        dir,
        "04_interactive_presentation/data/taxonomy-reviewed-profiles.json",
      ),
      "utf8",
    ),
  );
  const expected = {
    ...inputs,
    author_reviews_sha256: createHash("sha256")
      .update(fs.readFileSync(input))
      .digest("hex"),
  };
  const html = view.render(produced, expected, fixture.baseline, "pwr");
  assert.match(html, /&lt;img src=x onerror=&#39;alert\(1\)&#39;&gt;&amp;/);
  assert.ok(!html.includes("<img"));
  assert.match(
    view.exportProfile(produced, expected, fixture.baseline, "pwr"),
    /HTML encoding probe/,
  );
});

test("the identical classic-script presentation uses actual admitted reader and text owners", () => {
  const filename = path.join(
    root,
    "04_interactive_presentation/taxonomy-reviewed-presentation.js",
  );
  const context = vm.createContext({
    AtlasTaxonomyReviewedProfiles: reader,
    AtlasPresentationText: globalThis.AtlasPresentationText,
  });
  vm.runInContext(fs.readFileSync(filename, "utf8"), context, { filename });
  assert.equal(
    context.AtlasTaxonomyReviewedPresentation.render(
      document,
      inputs,
      fixture.baseline,
      "phwr-candu",
    ),
    view.render(document, inputs, fixture.baseline, "phwr-candu"),
  );
  assert.equal(
    context.AtlasTaxonomyReviewedPresentation.exportProfile(
      document,
      inputs,
      fixture.baseline,
      "phwr-candu",
    ),
    view.exportProfile(document, inputs, fixture.baseline, "phwr-candu"),
  );
});
