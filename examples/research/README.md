<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
Atlas Reactorum — reproducible research example
-->

# Restore a research comparison

Open [comparison.ipynb](comparison.ipynb) in a Python 3.12+ Jupyter kernel.
Start Jupyter from the repository root or set `ATLAS_REPOSITORY` to the complete
accepted checkout. The kernel needs the project's locked build dependencies;
Node 24.21.0 must be on its PATH. The reader uses `/usr/bin/env` on the supported
Unix host. Jupyter is an optional notebook environment; the CLI does not require it.

The notebook restores the real [PWR/BWR comparison](pwr-bwr-comparison.json),
inspects original claims, source locators and missing temperature metadata, then
checks that a second read reproduces the same result. It writes no accepted
source or dataset. Save your research result separately if needed. Cite the
original supporting works alongside the explicit Atlas snapshot you used.

The separately retained [example manifest](comparison-manifest.json) pins both
the whole-profile snapshot and the exact original comparison file. Treat it as
trusted only after checking its provenance. A newly computed hash of an
untrusted import is not independent evidence that the import is authentic.
Retain the manifest, downloaded comparison and complete matching repository
snapshot together; current data do not replace an unavailable older version.

## Read a downloaded comparison

From the repository root, supply the two hashes from your trusted manifest:

```sh
python -m tools.research_comparison --root . \
  --bundle examples/research/pwr-bwr-comparison.json \
  --snapshot PROFILE_SHA256 --bundle-sha256 ORIGINAL_FILE_SHA256
```

`make research-example VENV=/absolute/development/environment` restores the
included example using its retained manifest. It prints the original comparison
and changes no files. The [browser guide](../../04_interactive_presentation/README.md#compare-cite-and-share)
explains how to select and download another two/three-entry comparison.

The public Python API is
`restore_comparison(root, bundle, profile_sha256, bundle_sha256)` in
[tools/research_comparison.py](../../tools/research_comparison.py).
It validates the whole original profile/taxonomy/citation binding before asking
the same native comparison model as the browser to reconstruct the export.
The native call has a 30-second deadline and a fixed command; request data travel
as JSON on stdin. Refusals expose a fixed message and return CLI status 2.

The native [research reader](../../04_interactive_presentation/scripts/research_comparison.cjs)
exports/restores through `AtlasTaxonomyComparison.createComparison`:

```sh
node 04_interactive_presentation/scripts/research_comparison.cjs \
  --export metadata/evidence_profiles/profiles.json PROFILE_SHA256 pwr bwr
node 04_interactive_presentation/scripts/research_comparison.cjs \
  --restore metadata/evidence_profiles/profiles.json PROFILE_SHA256 \
  examples/research/pwr-bwr-comparison.json ORIGINAL_FILE_SHA256
```

Both commands print JSON and write no source files. `run(args)` is the equivalent
native API; `restore(document, snapshot, originalText, originalFileHash)` restores
an original canonical export. Native input profiles must come from an accepted,
source-validated snapshot; the Python reader performs that full source check.
Canonical JSON uses UTF-8, two-space indentation and a final newline, as the
browser download does. Duplicate keys, nonfinite values and noncanonical input
refuse. The original bundle must match the exact rebuilt selection, rights,
profiles, claims, sources, input hashes and compatibility results. The complete
profile digest uses the existing UTF-8 `JSON.stringify` contract.

## Interpretation

The example records catalogue statements and explicit missing values.
Unnormalised temperature descriptions stay `not_reviewed`; the comparison stays
`not_comparable`. No numeric average, unit conversion, operating-device ranking
or independent complete-entry decision follows. Original source acquisition
values, including null dates, review dates and source-specific support scopes
remain intact. `AGPL-3.0-or-later` applies to authored metadata; referenced
publisher works remain `catalogue-only; original not redistributed`.

The notebook keeps the original comparison inside its research result together
with the two hashes, ordered selection, source-backed claim rows and missing
parameter records. Its deterministic result hash identifies that content; it
is not a signature or scientific acceptance. This example introduces no query
service or unqualified link to a numerical model.
