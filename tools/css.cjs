// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — native CSS grammar and resolved custom-property contracts.
"use strict";
const css = require("css-tree");

/**
 * Expand declared custom-property values and fallbacks before native property matching.
 * All declared alternatives are checked, including values supplied under a conditional selector.
 * @param {string} source Original declaration value to parse without modifying its file.
 * @param {Map<string,string[]>} definitions Every declared custom-property value in this stylesheet.
 * @param {string[]} [stack] Dependency chain used to refuse circular definitions.
 * @returns {string[]} Finite resolved alternatives checked by the native lexer.
 * @throws {Error} For malformed, missing, circular or excessively expanding variables.
 */
function values(source, definitions, stack = []) {
  const ast = css.parse(source, { context: "value", positions: true });
  const variable = /** @type {import("css-tree").FunctionNode|null} */ (
    css.find(
      ast,
      (node) => node.type === "Function" && node.name.toLowerCase() === "var",
    )
  );
  if (!variable) return [source];
  const location = /** @type {import("css-tree").CssLocation} */ (variable.loc);
  const children = variable.children.toArray(),
    name = /** @type {import("css-tree").Identifier} */ (children[0]);
  if (!name.name.startsWith("--"))
    throw Error("CSS variable requires a custom-property name");
  if (stack.includes(name.name))
    throw Error("CSS variable cycle: " + [...stack, name.name].join(" -> "));
  const fallback = children.length > 1;
  const alternatives = [
    ...(definitions.get(name.name) || []),
    ...(fallback
      ? [
          children
            .slice(2)
            .map((node) => css.generate(node))
            .join(" "),
        ]
      : []),
  ];
  if (!alternatives.length)
    throw Error("CSS variable has no declaration or fallback: " + name.name);
  const output = [];
  for (const alternative of alternatives) {
    for (const expanded of values(alternative, definitions, [
      ...stack,
      name.name,
    ])) {
      const replaced =
        source.slice(0, location.start.offset) +
        " " +
        expanded +
        " " +
        source.slice(location.end.offset);
      output.push(...values(replaced, definitions, stack));
      if (output.length > 64)
        throw Error("CSS variable alternatives exceed 64");
    }
  }
  return output;
}

/**
 * Validate complete stylesheet syntax, at-rules and each resolved declaration value.
 * @param {string} source Complete original stylesheet; parse recovery is refused.
 * @returns {void} Every declaration and custom-property dependency is checked.
 * @throws {Error} For native grammar errors or unresolved custom-property contracts.
 */
function validate(source) {
  const ast = css.parse(source, {
    parseCustomProperty: true,
    /**
     * Refuse the native parser's recovery rather than accept discarded CSS.
     * @param {import("css-tree").SyntaxParseError} error Original native parse failure.
     * @returns {never} The failed source is reported to the caller.
     */
    onParseError(error) {
      throw error;
    },
  });
  /** @type {Map<string,string[]>} */
  const definitions = new Map();
  css.walk(ast, (node) => {
    if (node.type === "Declaration" && node.property.startsWith("--")) {
      const alternatives = definitions.get(node.property) || [];
      alternatives.push(css.generate(node.value));
      definitions.set(node.property, alternatives);
    }
  });
  for (const [name, alternatives] of definitions)
    for (const alternative of alternatives)
      values(alternative, definitions, [name]);
  css.walk(ast, (node) => {
    if (node.type === "Atrule") {
      if (!css.lexer.getAtrule(node.name))
        throw Error("unknown CSS at-rule: " + node.name);
      if (node.prelude) {
        const result = css.lexer.matchAtrulePrelude(node.name, node.prelude);
        if (result.error) throw result.error;
      }
    }
    if (node.type !== "Declaration" || node.property.startsWith("--")) return;
    for (const value of values(css.generate(node.value), definitions)) {
      const result = css.lexer.matchProperty(node.property, value);
      if (result.error)
        throw Error(node.property + ": " + result.error.message);
    }
  });
}
module.exports = { validate };
