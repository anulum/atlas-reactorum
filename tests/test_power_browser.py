# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — actual power documentary detail page
"""Use the actual complete Atlas Chrome page to open source-scoped power details."""

from __future__ import annotations

from .test_evidence_profiles_browser import Browser
from .test_evidence_profiles_browser import browser as browser
from .test_evidence_profiles_browser import native_browser as native_browser


def test_actual_power_detail_roles_and_no_fill_scope(browser: Browser) -> None:
    """Open every qualified unit and representative held, unknown and failed-capture cases."""
    result = browser.evaluate(
        """(()=>{
      const rows=AtlasApplicationData.facilities(REACTOR_FACILITIES);
      let qualified=0;const outcomes=new Set();
      for(const row of rows.filter(row=>row.power_field_decisions)) {
        const ds=row.power_field_decisions;
        const selected=ds.some(d=>d.disposition==='qualified');
        const novel=ds.some(d=>!outcomes.has(d.disposition));
        const attempt=ds.some(d=>d.observations.some(o=>o.capture_attempts.length));
        if(!selected&&!novel&&!attempt)continue;
        openFacility(row.id);
        if(!reactorDialog.open||dialogTitle.textContent!==row.name)throw Error('Wrong original unit');
        if(!dialogBody.textContent.includes('Power unit source review'))throw Error('Missing provenance');
        for(const d of ds){
          outcomes.add(d.disposition);
          if(d.disposition==='qualified'){
            qualified++;
            const label=PowerFieldAssertions.label(row,d.field,'Original');
            if(!dialogBody.textContent.includes(label))throw Error('Role was flattened');
          }
        }
        if(!dialogBody.textContent.includes('independent review not recorded'))throw Error('Invented acceptance');
        reactorDialog.close();
      }
      return {qualified,outcomes:[...outcomes].sort(),decisions:rows.reduce((n,r)=>n+(r.power_field_decisions?.length||0),0)};
    })()""",
        timeout=60,
    )
    assert result == {
        "qualified": 54,
        "outcomes": ["held", "qualified", "unknown"],
        "decisions": 930,
    }
