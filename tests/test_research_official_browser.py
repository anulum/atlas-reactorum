# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — research source map and download conformance
"""Follow actual facility buttons and native file downloads for original research sources."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import pytest

from .conftest import ROOT
from .test_browser_checks import native_browser as native_browser
from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser


def test_every_actual_research_detail_retains_sources_dates_and_selection(browser: Browser) -> None:
    """Open actual research details and preserve original, superseded and dated field evidence.

    Parameters
    ----------
    browser : Browser
        Live native Chrome connection to the actual complete presentation.
    """
    result = browser.evaluate("""(() => {
      let records = 0, assertions = 0, previous = 0;
      const search = document.querySelector('#facilitySearch');
      for (const row of window.REACTOR_FACILITIES.filter(row => row.research_field_origins?.length)) {
        search.value = row.name;
        search.dispatchEvent(new Event('input'));
        const button = [...document.querySelectorAll('#facilityList .facility-open')]
          .find(button => button.dataset.id === row.id);
        if (!button) throw Error('Original facility search result missing');
        button.click();
        const dialog = document.querySelector('#reactorDialog');
        const section = [...dialog.querySelectorAll('.field-sources')]
          .find(section => section.querySelector('h3')?.textContent === 'Research field sources');
        if (!dialog.open || !section || !section.textContent.includes('Retrieval dates are not publication or reactor event dates'))
          throw Error('Original research sources are not visible');
        const nodes = [...section.querySelectorAll('details')];
        if (nodes.length !== row.research_field_origins.length) throw Error('Original assertion count differs');
        for (const [index, origin] of row.research_field_origins.entries()) {
          const node = nodes[index];
          if (!node.textContent.includes(origin.value) || !node.textContent.includes(origin.source_sha256) ||
              !node.textContent.includes(origin.source_dataset) || node.querySelector('a').href !== origin.source_url)
            throw Error('Original source meaning or byte binding differs');
          if (origin.selection === 'superseded') {
            if (!node.textContent.includes('Previous source assertion')) throw Error('Superseded source hidden');
            previous++;
          }
          assertions++;
        }
        for (const url of row.source_urls)
          if (![...dialog.querySelectorAll('.detail-sources a')].some(link => link.href === url))
            throw Error('Accepted source URL missing from detail');
        const fields = [...dialog.querySelectorAll('dt')].map(node => node.textContent);
        if (row.first_criticality && !fields.includes('First criticality'))
          throw Error('Criticality mislabeled as first operation');
        if (row.first_operation && !fields.includes('First operation'))
          throw Error('First operation missing');
        records++;
        dialog.close();
      }
      search.value = '';
      search.dispatchEvent(new Event('input'));
      return {records, assertions, previous};
    })()""")
    rows = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )["records"]
    origins = [origin for row in rows for origin in row.get("research_field_origins", [])]
    assert result == {
        "records": sum(bool(row.get("research_field_origins")) for row in rows),
        "assertions": len(origins),
        "previous": sum(origin["selection"] == "superseded" for origin in origins),
    }


def test_actual_map_download_buttons_preserve_every_research_source_and_event(
    browser: Browser, tmp_path: Path
) -> None:
    """Download through actual map controls and compare every original source and event field.

    Parameters
    ----------
    browser : Browser
        Live native Chrome connection to the actual complete presentation.
    tmp_path : Path
        Owned temporary directory for real process inputs and outputs.
    """
    browser.command(
        "Browser.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(tmp_path), "eventsEnabled": True},
    )
    browser.evaluate("""
      document.querySelector('#facilityExportJson').click();
      document.querySelector('#facilityExportCsv').click();
    """)
    deadline = time.monotonic() + 15
    csv_files: list[Path] = []
    json_files: list[Path] = []
    while time.monotonic() < deadline:
        csv_files = list(tmp_path.glob("reactor-atlas-filtered-*.csv"))
        json_files = list(tmp_path.glob("reactor-atlas-filtered-*.json"))
        if len(csv_files) == len(json_files) == 1 and not list(tmp_path.glob("*.crdownload")):
            break
        time.sleep(0.05)
    else:
        pytest.fail("Native map download buttons did not produce complete files")
    original = json.loads(
        (ROOT / "04_interactive_presentation/data/global_reactors.sample.json").read_text()
    )["records"]
    assert json.loads(json_files[0].read_text()) == original
    with csv_files[0].open(newline="", encoding="utf-8") as stream:
        downloaded = list(csv.DictReader(stream))
    assert len(downloaded) == len(original) == 13459
    for record, row in zip(original, downloaded, strict=True):
        assert row["id"] == record["id"]
        assert row["first_criticality"] == record.get("first_criticality", "")
        assert row["purpose"] == record.get("purpose", "")
        assert json.loads(row["research_field_origins"]) == record.get("research_field_origins", [])
        assert json.loads(row["source_urls"]) == record.get("source_urls", [])
        assert json.loads(row["field_observations"]) == record.get("field_observations", [])
