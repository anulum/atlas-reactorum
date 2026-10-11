// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — author assessment admission method contracts.

/** Actual wire checks narrow unknown source metadata before semantic admission. */
export interface AuthorReviewValues {
  /** Require exactly the declared own keys while keeping cells unknown. */
  object(
    value: unknown,
    keys: readonly string[],
  ): asserts value is Record<string, unknown>;
  /** Admit actual arrays before their individual members are checked. */
  array(value: unknown): asserts value is unknown[];
  /** Admit original nonempty single-line text without source whitespace changes. */
  text(value: unknown): asserts value is string;
  /** Admit complete distinct string-reference arrays without reordering. */
  strings(value: unknown): asserts value is string[];
  /** Admit stable lowercase alphanumeric and hyphenated identities. */
  identity(value: unknown): asserts value is string;
  /** Admit real Gregorian calendar dates without overflow normalization. */
  day(value: unknown): asserts value is string;
  /** Return inclusive declared date bounds without inventing unknown precision. */
  dateBounds(value: unknown): [string, string] | null;
  /** Admit complete original source custody without a new publisher rights grant. */
  source(
    value: unknown,
  ): import("./scripts/taxonomy_citations.cjs").CitationSource;
}
