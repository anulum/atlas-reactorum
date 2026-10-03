// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// Atlas Reactorum — source-bound pending corrections and explicit curator records
"use strict";

(() => {
  const fields = ["proposed_statement", "source_url", "locator", "reason", "submitted_by", "proposed_at"];
  function check(input) {
    if (!input || fields.some(field => typeof input[field] !== "string" || !input[field].trim()) ||
        Object.keys(input).some(field => !fields.includes(field))) {
      throw new Error("A correction requires its statement, source, locator, reason, contributor and date");
    }
    const url = new URL(input.source_url);
    if (url.protocol !== "https:" || url.username || url.password) throw new Error("A correction source needs anonymous HTTPS");
    globalThis.AtlasEvidenceHistory.observation(input.proposed_at);
  }

  /**
   * Prepare a pending correction bound to the exact original claim revision.
   * @param {object} history Complete source journal; never modified by a proposal.
   * @param {string} expectedDigest Explicit complete journal hash.
   * @param {string} entryId Stable original entry identity.
   * @param {string} claimId Stable original claim identity.
   * @param {string} revisionHash Selected claim revision hash, including its observation date.
   * @param {object} input Proposed wording, source URL/locator/reason, contributor and UTC date.
   * @returns {Promise<object>} Content-hashed pending proposal for explicit local handoff.
   * @throws {Error} On unknown revisions, malformed proposal fields or unchanged wording.
   */
  async function propose(history, expectedDigest, entryId, claimId, revisionHash, input) {
    const originalInput = structuredClone(input);
    check(originalInput);
    const record = await globalThis.AtlasEvidenceHistory.readClaim(history, expectedDigest, entryId, claimId);
    const original = record.revisions.find(revision => revision.revision_sha256 === revisionHash);
    if (!original || original.claim === null) throw new Error("The proposed correction revision is unavailable");
    if (original.claim.original_statement === originalInput.proposed_statement) throw new Error("A correction must explain different proposed wording");
    const body = { schema_version: "atlas-correction-proposal-1.0.0", state: "pending",
      metadata_license: record.metadata_license, source_rights: record.source_rights,
      history_sha256: expectedDigest, entry_id: entryId, claim_id: claimId,
      original_revision: original, proposal: originalInput, review: null,
      publication_effect: "none; accepted source data remain unchanged" };
    return { proposal_sha256: await globalThis.AtlasEvidenceHistory.digest(body), ...body };
  }

  /**
   * Record a curator decision without applying it to accepted source data.
   * @param {object} proposal Exact original pending proposal, including its digest.
   * @param {object} review Explicit decision, curator, UTC review date and source-bound reason.
   * @returns {Promise<object>} Reviewed proposal retaining all original pending content.
   * @throws {Error} On altered/non-pending proposals or missing decision evidence.
   */
  async function reviewProposal(proposal, review) {
    const content = structuredClone(proposal);
    const decision = structuredClone(review);
    const { proposal_sha256: expected, ...body } = content;
    if (content.schema_version !== "atlas-correction-proposal-1.0.0" || content.state !== "pending" ||
        content.review !== null || await globalThis.AtlasEvidenceHistory.digest(body) !== expected) {
      throw new Error("Only an unchanged pending proposal may be reviewed");
    }
    check(content.proposal);
    const required = ["decision", "reviewed_by", "reviewed_at", "reason", "source_url", "locator"];
    if (!decision || required.some(field => typeof decision[field] !== "string" || !decision[field].trim()) ||
        Object.keys(decision).some(field => !required.includes(field)) ||
        !["accepted-for-editing", "rejected"].includes(decision.decision)) {
      throw new Error("A curator decision requires explicit source-bound review evidence");
    }
    const url = new URL(decision.source_url);
    if (url.protocol !== "https:" || url.username || url.password) throw new Error("A review source needs anonymous HTTPS");
    globalThis.AtlasEvidenceHistory.observation(decision.reviewed_at);
    if (decision.reviewed_at < content.proposal.proposed_at) throw new Error("A review cannot precede its proposal");
    return { ...content, state: decision.decision, review: decision,
      pending_proposal_sha256: expected,
      review_sha256: await globalThis.AtlasEvidenceHistory.digest({ pending_proposal_sha256: expected, review: decision }) };
  }

  globalThis.AtlasEvidenceCorrections = Object.freeze({ propose, reviewProposal });
})();
