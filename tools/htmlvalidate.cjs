// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — maintained HTML source semantics and formatting convention.
"use strict";
module.exports = {
  root: true,
  extends: ["html-validate:recommended"],
  rules: {
    "void-style": ["error", { style: "selfclose" }],
    "doctype-style": ["error", { style: "lowercase" }],
  },
};
