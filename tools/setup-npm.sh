#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — verified native package-manager bootstrap

set -euo pipefail

version=12.2.0
digest=66c2632a94e796649738b2d7894d710c2cc2e1696893823066687f6b0d8a52e5f2b54eeaeaa32ffdc513ecca1e49ff794a5c2ec3f9515d879f1b3182b291cf35
parent=${1:?Usage: setup-npm.sh existing-temporary-parent}
tool_dir="$parent/atlas-npm-$version"
mkdir "$tool_dir"
curl --fail --silent --show-error --proto '=https' \
    --connect-timeout 20 --max-time 120 \
    "https://registry.npmjs.org/npm/-/npm-$version.tgz" --output "$tool_dir/archive.tgz"
printf '%s  %s\n' "$digest" "$tool_dir/archive.tgz" | sha512sum --check
tar --extract --gzip --file "$tool_dir/archive.tgz" --directory "$tool_dir" --no-same-owner
mkdir "$tool_dir/bin"
ln -s ../package/bin/npm-cli.js "$tool_dir/bin/npm"
ln -s ../package/bin/npx-cli.js "$tool_dir/bin/npx"
test "$("$tool_dir/bin/npm" --version)" = "$version"
if [[ -n ${GITHUB_PATH:-} ]]; then
    printf '%s\n' "$tool_dir/bin" >>"$GITHUB_PATH"
fi
printf '%s\n' "$tool_dir/bin"
