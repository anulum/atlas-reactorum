// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native complete CSS source and variable refusal contracts.
"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path");
const { validate } = require("../tools/css.cjs");
const source = fs.readFileSync(
  path.join(__dirname, "../04_interactive_presentation/styles.css"),
  "utf8",
);
test("the complete actual stylesheet qualifies without modifying its bytes", () => {
  validate(source);
  validate(source + ":root{--empty: ;}");
  assert.equal(
    fs.readFileSync(
      path.join(__dirname, "../04_interactive_presentation/styles.css"),
      "utf8",
    ),
    source,
  );
});
test("declared alternatives, aliases, nested fallback functions and whitespace preserve valid native types", () => {
  validate(
    source +
      "\n:root{--measure:1px;--alias:var(--measure)}@media print{:root{--measure:2px}}.future{margin:var(--alias);color:var(--absent, rgb(0, 0, 0));background:linear-gradient(red 0, var(--acid) 100%)}@layer {} ",
  );
});
test("native declaration grammar rejects unknown properties, invalid static values and invalid resolved alternatives", () => {
  for (const suffix of [
    ".future{unknown-atlas-property:red}",
    ".future{color:invalid-atlas-color}",
    ":root{--measure:red}.future{margin:var(--measure)}",
    ":root{--measure:1px}@media print{:root{--measure:red}}.future{margin:var(--measure)}",
    ".future{color:var(--absent, 9px)}",
  ])
    assert.throws(() => validate(source + suffix), /Unknown property|Mismatch/);
});
test("conditional custom properties retain their fallback grammar outside the defining condition", () => {
  const declaration = "@media print{:root{--future-measure:1px}}";
  validate(source + declaration + ".future{margin:var(--future-measure,2px)}");
  assert.throws(
    () =>
      validate(
        source + declaration + ".future{margin:var(--future-measure,red)}",
      ),
    /Mismatch/,
  );
});
test("missing, malformed and circular CSS variable dependencies refuse", () => {
  for (const suffix of [
    ".future{color:var(--absent)}",
    ".future{color:var()}",
    ".future{color:var(ink)}",
    ".future{color:var(--ink red)}",
    ":root{--loop:var(--loop)}",
    ":root{--one:var(--two);--two:var(--one)}",
  ])
    assert.throws(() => validate(source + suffix), /CSS variable|is expected/);
});
test("native parser recovery and unregistered or malformed at-rules cannot qualify", () => {
  for (const suffix of [
    ".future{color:!}",
    ".future{???}",
    "@atlas-unregistered {}",
    "@charset 123;",
    ".future{color:var(--bad, invalid-atlas-color)}",
    "@media (width = red) {.future{color:red}}",
  ])
    assert.throws(() => validate(source + suffix));
});
test("finite alternative expansion refuses excessive conditional combinations", () => {
  let suffix = "";
  for (let n = 0; n < 65; n++) suffix += ":root{--alternatives:" + n + "px}";
  assert.throws(
    () => validate(source + suffix + ".future{margin:var(--alternatives)}"),
    /alternatives exceed 64/,
  );
});
