# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — primary decisions through native map and downloads
"""Use an actual release-built fixture page, map details and native file downloads.

Fixture citation values exercise software contracts without approving a real
operator, event, scientific claim or redistribution licence.
"""

from __future__ import annotations

import csv
import json
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from .test_browser_checks import BrowserEndpoints
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser
from .test_research_primary_integration import primary_bundle as primary_bundle
from .test_research_primary_integration import primary_source_tree as primary_source_tree
from .test_research_primary_projection import baseline as baseline


def test_release_producer_to_native_map_detail_and_both_download_formats(
    browser: Browser, native_browser: BrowserEndpoints, primary_source_tree: Path, tmp_path: Path
) -> None:
    """Exercise complete producer inputs, both viewports and real downloads without approving fixture claims.

    Parameters
    ----------
    browser : Browser
        Live native Chrome connection to the actual complete presentation.
    native_browser : BrowserEndpoints
        Owned native browser endpoints and original page location.
    primary_source_tree : Path
        Complete source tree rebuilt by the real release CLI from a fixture bundle.
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    """
    data = primary_source_tree / "04_interactive_presentation/data"
    original = json.loads((data / "global_reactors.sample.json").read_text())["records"]
    selected = [row for row in original if row.get("research_primary_assertions")]
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(data.parent)),
    )
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        browser.command(
            "Page.navigate", {"url": f"http://127.0.0.1:{server.server_port}/index.html"}
        )
        browser.wait_ready()
        for width, height, mobile in ((1440, 1000, False), (375, 812, True)):
            browser.command(
                "Emulation.setDeviceMetricsOverride",
                {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile},
            )
            result = browser.evaluate("""(() => {
              const search = document.querySelector('#facilitySearch');
              let records = 0, decisions = 0;
              for (const row of window.REACTOR_FACILITIES.filter(row => row.research_primary_assertions?.length)) {
                search.value = row.name;
                search.dispatchEvent(new Event('input'));
                const button = [...document.querySelectorAll('#facilityList .facility-open')].find(node => node.dataset.id === row.id);
                if (!button) throw Error('Primary reactor missing from real search');
                button.click();
                const dialog = document.querySelector('#reactorDialog');
                const section = dialog.querySelector('.primary-research-sources');
                if (!dialog.open || !section) throw Error('Primary decisions missing from real dialog');
                const nodes = [...section.querySelectorAll('details')];
                if (nodes.length !== row.research_primary_assertions.length) throw Error('Primary decisions dropped');
                row.research_primary_assertions.forEach((assertion, index) => {
                  const node = nodes[index];
                  if (!node.textContent.includes(assertion.scope) || !node.textContent.includes(assertion.assertion_basis)) throw Error('Review scope changed');
                  if (assertion.source_id && (!node.textContent.includes(assertion.source_sha256) || !node.textContent.includes(assertion.rights) || node.querySelector('a').href !== assertion.source_url)) throw Error('Original citation changed');
                  if (assertion.date_precision && !node.textContent.includes('Event precision: ' + assertion.date_precision)) throw Error('Event precision hidden');
                  if (assertion.selection === 'held' && row[assertion.field] !== '') throw Error('Held claim filled a scalar');
                  decisions++;
                });
                records++;
                dialog.close();
              }
              search.value = '';
              search.dispatchEvent(new Event('input'));
              return {records, decisions};
            })()""")
            assert result == {"records": len(selected), "decisions": 358}
        browser.command("Emulation.clearDeviceMetricsOverride")
        downloads = tmp_path / "downloads"
        downloads.mkdir()
        browser.command(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(downloads), "eventsEnabled": True},
        )
        browser.evaluate(
            "document.querySelector('#facilityExportJson').click(); document.querySelector('#facilityExportCsv').click();"
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            csv_files = list(downloads.glob("*.csv"))
            json_files = list(downloads.glob("*.json"))
            if len(csv_files) == len(json_files) == 1 and not list(downloads.glob("*.crdownload")):
                break
            time.sleep(0.05)
        else:
            pytest.fail("Native primary map downloads did not complete")
        assert json.loads(json_files[0].read_text()) == original
        with csv_files[0].open(newline="") as stream:
            exported = list(csv.DictReader(stream))
        assert len(exported) == len(original) == 13459
        for record, row in zip(original, exported, strict=True):
            assert row["id"] == record["id"]
            assert json.loads(row["research_primary_assertions"]) == record.get(
                "research_primary_assertions", []
            )
            for field in ("operator", "purpose", "first_criticality"):
                assert row[field] == str(record.get(field) or "")
    finally:
        browser.command("Emulation.clearDeviceMetricsOverride")
        browser.command("Page.navigate", {"url": native_browser["page"]})
        browser.wait_ready()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
