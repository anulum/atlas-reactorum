# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — real fallback page and consumed dataset-shape boundaries.
"""Exercise source absence and malformed cells through the real Chrome page."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from typing import cast
from urllib.parse import urlsplit

from ._catalogue_inputs import run_cli
from .browser_checks_runtime import ASSETS, SCRIPT, AtlasHandler, BrowserEndpoints, wait_for_page
from .browser_checks_runtime import native_browser as native_browser
from .conftest import load_module
from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser


class FallbackHandler(AtlasHandler):
    """Serve original assets with only the authored taxonomy script omitted."""

    def do_GET(self) -> None:
        """Serve the actual missing-source candidate index and unchanged sibling assets."""
        if urlsplit(self.path).path != "/index.html":
            super().do_GET()
            return
        original = (ASSETS / "index.html").read_bytes()
        script = b'<script src="data/taxonomy-expanded.js"></script>'
        assert original.count(script) == 1
        body = original.replace(script, b"")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def test_actual_missing_taxonomy_keeps_fallback_unattributed_and_full_cli_refuses(
    native_browser: BrowserEndpoints,
) -> None:
    """Omit one real script, retain all other data and refuse evidence for authored fallback cards."""
    module = load_module("04_interactive_presentation/browser-check.py", "atlas_fallback_browser")
    server = ThreadingHTTPServer(("127.0.0.1", 0), FallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    try:
        with module.BrowserSession(native_browser["endpoint"], native_browser["page"]) as baseline:
            target = baseline.command("Target.createTarget", {"url": page})["targetId"]
            assert isinstance(target, str)
            try:
                wait_for_page(native_browser["endpoint"], page)
                with module.BrowserSession(native_browser["endpoint"], page) as connected:
                    active = cast(Browser, connected)
                    active.wait_ready()
                    assert active.evaluate("reactors.length") == 31
                    assert (
                        active.evaluate(
                            "reactors.every(row=>row.id===undefined&&row.source_urls===undefined)"
                        )
                        is True
                    )
                    assert active.evaluate(
                        "[REACTOR_FACILITIES.length,FUSION_COMPANIES.length,ANULUM_REACTOR_REPOS.length]"
                    ) == [13459, 98, 30]
                    active.evaluate("openReactor('PWR')")
                    assert active.evaluate("reactorDialog.open") is True
                    assert active.evaluate(
                        "dialogBody.querySelector('[role=status]').textContent"
                    ) == ("Source-bound evidence is unavailable for this authored fallback entry.")
                    assert (
                        active.evaluate("dialogBody.querySelector('.evidence-profile')===null")
                        is True
                    )
                    assert (
                        active.evaluate("dialogBody.querySelector('.profile-download')===null")
                        is True
                    )
                for optimized in (False, True):
                    result = run_cli(
                        SCRIPT,
                        "--endpoint",
                        native_browser["endpoint"],
                        "--page-url",
                        page,
                        optimize=optimized,
                    )
                    assert result.returncode == 1
                    assert json.loads(result.stdout) == {
                        "result": "failed",
                        "reason": "Atlas complete dataset count mismatch: types",
                    }
            finally:
                baseline.command("Target.closeTarget", {"targetId": target})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_actual_browser_readers_refuse_malformed_cells_and_preserve_all_original_records(
    browser: Browser,
) -> None:
    """Use public native readers with original rows and real malformed coordinate/count/namespace inputs."""
    for expression in [
        "AtlasApplicationData.facilities([{...REACTOR_FACILITIES[0],lat:'0'}])",
        "AtlasApplicationData.companies({records:FUSION_COMPANIES,record_count:0})",
        "AtlasBrowserElements.requireElements(document,'.reactor-card','select')",
    ]:
        result = browser.evaluate(
            "(()=>{try{" + expression + ";}catch(error){return error.message;}})()"
        )
        assert isinstance(result, str) and result.startswith(("Atlas", "Required Atlas"))
    assert (
        browser.evaluate("AtlasApplicationData.facilities(REACTOR_FACILITIES)===REACTOR_FACILITIES")
        is True
    )
    assert browser.evaluate("filteredFacilities().length") == 13459
