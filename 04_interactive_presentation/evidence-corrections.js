// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound pending corrections and explicit curator records
"use strict";

/**
 * Explicit contributor wording and source evidence, without publication effects.
 * @typedef {object} AtlasCorrectionInput
 * @property {string} proposed_statement Proposed replacement wording.
 * @property {string} source_url Anonymous HTTPS evidence locator.
 * @property {string} locator Exact source section or page.
 * @property {string} reason Source-bound rationale.
 * @property {string} submitted_by Recorded contributor name, not an authenticated signature.
 * @property {string} proposed_at Explicit UTC proposal observation.
 */

/**
 * Explicit curator decision authorising consideration, never a source edit.
 * @typedef {object} AtlasCuratorReview
 * @property {"accepted-for-editing"|"rejected"} decision Recorded curator disposition.
 * @property {string} reviewed_by Recorded curator identity.
 * @property {string} reviewed_at Explicit UTC review observation.
 * @property {string} reason Source-bound review rationale.
 * @property {string} source_url Anonymous HTTPS review evidence.
 * @property {string} locator Exact source section or page.
 */

/**
 * Content-bound original proposal retaining the exact original claim revision.
 * @typedef {object} AtlasCorrectionProposal
 * @property {string} proposal_sha256 Complete original pending-body digest.
 * @property {string} schema_version Explicit proposal schema.
 * @property {string} state Pending or explicitly recorded curator disposition.
 * @property {string} metadata_license Original metadata licence.
 * @property {string} source_rights Original catalogue-only source boundary.
 * @property {string} history_sha256 Explicit whole-journal identity.
 * @property {string} entry_id Stable original entry.
 * @property {string} claim_id Stable original claim.
 * @property {import("./evidence-history.js").AtlasClaimRevision} original_revision Unchanged original dated revision.
 * @property {AtlasCorrectionInput} proposal Explicit checked contributor input.
 * @property {AtlasCuratorReview|null} review Pending absence or explicit source-bound review.
 * @property {string} publication_effect Original no-publication boundary.
 */

/**
 * Reviewed artefact retaining both pending proposal and curator evidence hashes.
 * @typedef {AtlasCorrectionProposal & {review: AtlasCuratorReview, pending_proposal_sha256: string, review_sha256: string}} AtlasReviewedCorrection
 */

/** Source-bound correction facade for classic-script and native consumers. */
var AtlasEvidenceCorrections = (() => {
  const fields = [
    "proposed_statement",
    "source_url",
    "locator",
    "reason",
    "submitted_by",
    "proposed_at",
  ];
  /**
   * Require every original contributor field before interpreting source or date.
   * @param {unknown} input External contributor metadata before validation.
   * @returns {asserts input is AtlasCorrectionInput} Complete checked contributor fields.
   * @throws {Error} Fields, anonymous HTTPS or the explicit UTC observation are invalid.
   */
  function check(input) {
    if (!input || typeof input !== "object") {
      throw new Error(
        "A correction requires its statement, source, locator, reason, contributor and date",
      );
    }
    const cells = /** @type {Record<string, unknown>} */ (input);
    if (
      fields.some((field) => {
        const value = cells[field];
        return typeof value !== "string" || !value.trim();
      }) ||
      Object.keys(cells).some((field) => !fields.includes(field))
    ) {
      throw new Error(
        "A correction requires its statement, source, locator, reason, contributor and date",
      );
    }
    const checked = /** @type {AtlasCorrectionInput} */ (input);
    const url = new URL(checked.source_url);
    if (url.protocol !== "https:" || url.username || url.password)
      throw new Error("A correction source needs anonymous HTTPS");
    globalThis.AtlasEvidenceHistory.observation(checked.proposed_at);
  }

  /**
   * Prepare a pending correction bound to the exact original claim revision.
   * @param {import("./evidence-history.js").AtlasEvidenceJournal} history Complete source journal; never modified by a proposal.
   * @param {string} expectedDigest Explicit complete journal hash.
   * @param {string} entryId Stable original entry identity.
   * @param {string} claimId Stable original claim identity.
   * @param {string} revisionHash Selected claim revision hash, including its observation date.
   * @param {unknown} input External contributor fields, checked before use.
   * @returns {Promise<AtlasCorrectionProposal>} Content-hashed pending proposal for explicit local handoff.
   * @throws {Error} On unknown revisions, malformed proposal fields or unchanged wording.
   */
  async function propose(
    history,
    expectedDigest,
    entryId,
    claimId,
    revisionHash,
    input,
  ) {
    const originalInput = structuredClone(input);
    check(originalInput);
    const record = await globalThis.AtlasEvidenceHistory.readClaim(
      history,
      expectedDigest,
      entryId,
      claimId,
    );
    const original = record.revisions.find(
      (revision) => revision.revision_sha256 === revisionHash,
    );
    if (!original || original.claim === null)
      throw new Error("The proposed correction revision is unavailable");
    if (original.claim.original_statement === originalInput.proposed_statement)
      throw new Error("A correction must explain different proposed wording");
    const body = {
      schema_version: "atlas-correction-proposal-1.0.0",
      state: "pending",
      metadata_license: record.metadata_license,
      source_rights: record.source_rights,
      history_sha256: expectedDigest,
      entry_id: entryId,
      claim_id: claimId,
      original_revision: original,
      proposal: originalInput,
      review: null,
      publication_effect: "none; accepted source data remain unchanged",
    };
    return {
      proposal_sha256: await globalThis.AtlasEvidenceHistory.digest(body),
      ...body,
    };
  }

  /**
   * Record a curator decision without applying it to accepted source data.
   * @param {AtlasCorrectionProposal} proposal Exact original pending proposal, including its digest.
   * @param {unknown} review External curator fields, checked before use.
   * @returns {Promise<AtlasReviewedCorrection>} Reviewed proposal retaining all original pending content.
   * @throws {Error} On altered/non-pending proposals or missing decision evidence.
   */
  async function reviewProposal(proposal, review) {
    const content = structuredClone(proposal);
    const candidate = structuredClone(review);
    const { proposal_sha256: expected, ...body } = content;
    if (
      content.schema_version !== "atlas-correction-proposal-1.0.0" ||
      content.state !== "pending" ||
      content.review !== null ||
      (await globalThis.AtlasEvidenceHistory.digest(body)) !== expected
    ) {
      throw new Error("Only an unchanged pending proposal may be reviewed");
    }
    check(content.proposal);
    const required = [
      "decision",
      "reviewed_by",
      "reviewed_at",
      "reason",
      "source_url",
      "locator",
    ];
    if (!candidate || typeof candidate !== "object") {
      throw new Error(
        "A curator decision requires explicit source-bound review evidence",
      );
    }
    const cells = /** @type {Record<string, unknown>} */ (candidate);
    if (
      required.some((field) => {
        const value = cells[field];
        return typeof value !== "string" || !value.trim();
      }) ||
      Object.keys(cells).some((field) => !required.includes(field)) ||
      (cells.decision !== "accepted-for-editing" &&
        cells.decision !== "rejected")
    ) {
      throw new Error(
        "A curator decision requires explicit source-bound review evidence",
      );
    }
    const decision = /** @type {AtlasCuratorReview} */ (candidate);
    const url = new URL(decision.source_url);
    if (url.protocol !== "https:" || url.username || url.password)
      throw new Error("A review source needs anonymous HTTPS");
    globalThis.AtlasEvidenceHistory.observation(decision.reviewed_at);
    if (decision.reviewed_at < content.proposal.proposed_at)
      throw new Error("A review cannot precede its proposal");
    return {
      ...content,
      state: decision.decision,
      review: decision,
      pending_proposal_sha256: expected,
      review_sha256: await globalThis.AtlasEvidenceHistory.digest({
        pending_proposal_sha256: expected,
        review: decision,
      }),
    };
  }

  return Object.freeze({ propose, reviewProposal });
})();
globalThis.AtlasEvidenceCorrections = AtlasEvidenceCorrections;
