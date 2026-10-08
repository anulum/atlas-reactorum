# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — original history wire shapes and native refusal boundary.

"""Exercise schema admission using real native history/proposal production."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import coverage
import pytest
from jsonschema import ValidationError

from tools.evidence_history_inputs import PROFILE_SCHEMA, PacketKind, main, validate_packet

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/evidence_history_inputs.py"
REFUSAL = "Evidence history input shape refused.\n"


@pytest.fixture(scope="module")
def packets() -> dict[str, object]:
    """Produce real original profiles, journal and pending proposal via native APIs."""
    node = shutil.which("node")
    assert node is not None
    code = """
const root=process.argv[1];
require(root+'/04_interactive_presentation/taxonomy-claim-sources.js');
require(root+'/04_interactive_presentation/taxonomy-evidence-profile.js');
require(root+'/04_interactive_presentation/taxonomy-comparison.js');
require(root+'/04_interactive_presentation/evidence-history.js');
require(root+'/04_interactive_presentation/evidence-corrections.js');
const {loadHistoryProfiles}=require(root+'/tests/evidence_history_fixture.cjs');
(async()=>{
 const profiles=loadHistoryProfiles(root);
 const api=globalThis.AtlasEvidenceHistory;
 const time='2026-10-03T07:20:00.000Z';
 const history=await api.importProfiles(null,profiles,time);
 const hash=await api.digest(history);
 const record=await api.readClaim(history,hash,'pwr','pwr:classification:1');
 const original=record.revisions[0];
 const proposal=await globalThis.AtlasEvidenceCorrections.propose(
  history,hash,'pwr','pwr:classification:1',original.revision_sha256,
  {proposed_statement:'Source-bound software conformance proposal.',
   source_url:original.source.url,locator:original.claim.citation.section,
   reason:'Tests packet admission without publication.',submitted_by:'Named test contributor',
   proposed_at:time});
 console.log(JSON.stringify({profiles,history,proposal}));
})();
"""
    result = subprocess.run(
        [node, "-e", code, str(ROOT)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    parsed: object = json.loads(result.stdout)
    assert isinstance(parsed, dict)
    return cast(dict[str, object], parsed)


def member(value: object, key: str) -> object:
    """Select an actual existing JSON object member without inventing a fallback."""
    assert isinstance(value, dict)
    return cast(dict[str, object], value)[key]


def item(value: object, index: int = 0) -> dict[str, object]:
    """Select an actual existing object in the original wire array."""
    assert isinstance(value, list)
    selected = cast(list[object], value)[index]
    assert isinstance(selected, dict)
    return cast(dict[str, object], selected)


@pytest.mark.parametrize("kind", ["profiles", "history", "proposal"])
def test_complete_real_packet_shapes_and_cli_preserve_originals(
    packets: dict[str, object], kind: PacketKind
) -> None:
    """Admit actual producer packets without changing their original cells."""
    original = copy.deepcopy(packets[kind])
    validate_packet(kind, packets[kind])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), kind],
        input=json.dumps(packets[kind]).encode("utf8"),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0 and result.stdout == b"" and result.stderr == b""
    assert packets[kind] == original


@pytest.mark.parametrize("kind", ["profiles", "history", "proposal"])
@pytest.mark.parametrize("damage", ["null", "unknown-key", "wrong-schema", "wrong-cell"])
def test_actual_packet_damage_refuses_before_native_interpretation(
    packets: dict[str, object], kind: PacketKind, damage: str
) -> None:
    """Refuse malformed actual wire packets rather than laundering them into types."""
    value: object = copy.deepcopy(packets[kind])
    assert isinstance(value, dict)
    if damage == "null":
        value = None
    elif damage == "unknown-key":
        value["unbound"] = "caller-sensitive-input"
    elif damage == "wrong-schema":
        value["schema_version"] = "future"
    elif kind == "profiles":
        item(member(value, "records"))["taxonomy_record"] = {"id": "incomplete"}
    elif kind == "history":
        item(member(value, "snapshots"))["document"] = {}
    else:
        revision = member(value, "original_revision")
        assert isinstance(revision, dict)
        revision["source"] = {}
    with pytest.raises(ValidationError):
        validate_packet(kind, value)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), kind],
        input=json.dumps(value).encode("utf8"),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr.decode("utf8") == REFUSAL


@pytest.mark.parametrize(
    "body",
    [b"{", b'{"schema_version":1,"schema_version":2}', b"NaN", b"1e999", b"0.0", b"\xff"],
)
def test_native_stdin_refuses_malformed_duplicate_nonfinite_and_invalid_utf8(body: bytes) -> None:
    """Exercise real stdin parsing with fixed refusal and no echoed caller bytes."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "profiles"], input=body, capture_output=True, timeout=10
    )
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr.decode("utf8") == REFUSAL


@pytest.mark.parametrize("args", [[], ["caller-sensitive-kind"], ["profiles", "extra"]])
def test_unsupported_public_arguments_have_only_the_authored_refusal(args: list[str]) -> None:
    """Reject invalid API/CLI argument vectors before reading any input stream."""
    assert main(args) == 1
    result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, timeout=10)
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr.decode("utf8") == REFUSAL


def test_real_stdlib_only_interpreter_refuses_missing_schema_dependency() -> None:
    """Refuse an actual interpreter with site packages disabled, without a traceback."""
    code = """
import importlib.util,os,runpy,sys
package=sys.argv[1]
spec=importlib.util.spec_from_file_location('coverage',package,submodule_search_locations=[os.path.dirname(package)])
module=importlib.util.module_from_spec(spec)
sys.modules['coverage']=module
spec.loader.exec_module(module)
measurement=module.Coverage(config_file=sys.argv[2],data_suffix=True)
measurement.start()
sys.argv=[sys.argv[3],'profiles']
try:
 runpy.run_path(sys.argv[0],run_name='__main__')
finally:
 measurement.stop()
 measurement.save()
"""
    config = os.environ.get("COVERAGE_RCFILE", str(ROOT / "pyproject.toml"))
    assert importlib.util.find_spec("coverage") is not None
    result = subprocess.run(
        [sys.executable, "-S", "-c", code, str(coverage.__file__), config, str(SCRIPT)],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr.decode("utf8") == REFUSAL


@pytest.mark.parametrize("schema", [None, "null", '{"type":"unsupported"}', "{}"])
def test_real_candidate_with_unavailable_or_broken_owning_schema_refuses(
    packets: dict[str, object], tmp_path: Path, schema: str | None
) -> None:
    """Run a real candidate tool against missing or damaged original schema bytes."""
    target = tmp_path / "tools/evidence_history_inputs.py"
    target.parent.mkdir()
    shutil.copyfile(SCRIPT, target)
    assert target.read_bytes() == SCRIPT.read_bytes()
    if schema is not None:
        source = tmp_path / PROFILE_SCHEMA.relative_to(ROOT)
        source.parent.mkdir(parents=True)
        source.write_text(schema, encoding="utf8")
    # The normal whole-tree coverage source filter names the canonical root.
    # Measure this actual byte-identical candidate root explicitly, then let
    # the owning coverage path contract combine its real executed regions.
    code = """
import coverage,os,runpy,sys
from pathlib import Path
target,config=sys.argv[1:]
measurement=coverage.Coverage(source=[str(Path(target).parent)],
 config_file=config,data_suffix=True)
measurement.start()
sys.argv=[target,'profiles']
try:
 runpy.run_path(target,run_name='__main__')
finally:
 measurement.stop()
 measurement.save()
"""
    config = os.environ.get("COVERAGE_RCFILE", str(ROOT / "pyproject.toml"))
    result = subprocess.run(
        [sys.executable, "-c", code, str(target), config],
        input=json.dumps(packets["profiles"]).encode("utf8"),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 1 and result.stdout == b""
    assert result.stderr.decode("utf8") == REFUSAL
