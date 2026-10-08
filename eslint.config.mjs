// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native JavaScript contracts and lint rules.

import js from "@eslint/js";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";
import declarationParser from "@typescript-eslint/parser";

export default [
  {
    files: ["**/*.d.ts"],
    languageOptions: {
      parser: declarationParser,
      sourceType: "module",
    },
    linterOptions: {
      noInlineConfig: true,
      reportUnusedDisableDirectives: "error",
    },
    plugins: { jsdoc },
    rules: {
      ...jsdoc.configs["flat/recommended-typescript-error"].rules,
      "jsdoc/require-jsdoc": [
        "error",
        {
          contexts: [
            "TSInterfaceDeclaration",
            "TSTypeAliasDeclaration",
            "TSPropertySignature",
            "TSMethodSignature",
            "TSDeclareFunction",
            "VariableDeclaration",
          ],
          exemptEmptyFunctions: false,
          exemptEmptyConstructors: false,
        },
      ],
      "jsdoc/require-description": ["error", { contexts: ["any"] }],
    },
  },
  {
    files: ["**/*.{js,cjs,mjs}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: { ...globals.browser, ...globals.node },
    },
    linterOptions: {
      noInlineConfig: true,
      reportUnusedDisableDirectives: "error",
    },
    plugins: { jsdoc },
    rules: {
      ...js.configs.recommended.rules,
      "no-restricted-modules": [
        "error",
        {
          paths: ["ffi-napi", "ref-napi", "koffi", "node:ffi"],
        },
      ],
      "no-restricted-imports": [
        "error",
        {
          paths: ["ffi-napi", "ref-napi", "koffi", "node:ffi"],
        },
      ],
      "no-restricted-properties": [
        "error",
        {
          object: "process",
          property: "dlopen",
          message: "Native FFI loading requires complete owning qualification.",
        },
      ],
      ...jsdoc.configs["flat/recommended-error"].rules,
      "jsdoc/require-jsdoc": [
        "error",
        {
          contexts: [
            "FunctionDeclaration",
            "FunctionExpression",
            "ArrowFunctionExpression",
            "MethodDefinition",
          ],
          exemptEmptyFunctions: false,
          exemptEmptyConstructors: false,
        },
      ],
    },
  },
  {
    files: ["**/*.cjs", "**/*.test.js"],
    languageOptions: { sourceType: "commonjs" },
  },
  {
    files: ["**/*.mjs"],
    languageOptions: { sourceType: "module" },
  },
];
