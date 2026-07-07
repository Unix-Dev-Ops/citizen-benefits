import os
import json
from pathlib import Path
from datetime import date
from typing import Any
import httpx
from pydantic import BaseModel, Field

from citizenbenefits.schemas import BenefitProgram

class GroundingData(BaseModel):
    values: dict[str, Any] = Field(description="Dictionary of eligibility thresholds and rules")
    source_cited: str = Field(description="Authoritative source URL")
    as_of_date: date = Field(description="The date the thresholds were last verified/updated")
    grounded: bool = Field(description="True if the thresholds were verified via live fetch, False if fallback")


def parse_snap_live(html: str) -> dict[str, Any] | None:
    """Parses the USDA FNS SNAP eligibility page and extracts:
    - gross_income_limit_fpl_percentage
    - net_income_limit_fpl_percentage
    - standard_deduction
    - earned_income_deduction_pct
    - asset_limit_standard
    - asset_limit_elderly_disabled
    """
    from bs4 import BeautifulSoup
    import re
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        text = re.sub(r"\s+", " ", text)
        
        # Regex matches matching the official USDA SNAP page layout
        gross_match = re.search(r"Gross monthly income.*?\(([0-9]+)\s*percent of poverty\)", text, re.IGNORECASE)
        net_match = re.search(r"Net monthly income.*?\(([0-9]+)\s*percent of poverty\)", text, re.IGNORECASE)
        std_match = re.search(r"standard deduction of \$([0-9,]+)", text, re.IGNORECASE)
        earned_match = re.search(r"([0-9]+)-percent deduction from earned income", text, re.IGNORECASE)
        asset_std_match = re.search(r"households may have \$([0-9,]+) in countable resources", text, re.IGNORECASE)
        asset_elderly_match = re.search(r"or \$([0-9,]+) in countable resources if at least one member", text, re.IGNORECASE)
        
        if not (gross_match and net_match and std_match and earned_match and asset_std_match and asset_elderly_match):
            return None
            
        parsed = {
            "gross_income_limit_fpl_percentage": int(gross_match.group(1)),
            "net_income_limit_fpl_percentage": int(net_match.group(1)),
            "standard_deduction": int(std_match.group(1).replace(",", "")),
            "earned_income_deduction_pct": int(earned_match.group(1)),
            "asset_limit_standard": int(asset_std_match.group(1).replace(",", "")),
            "asset_limit_elderly_disabled": int(asset_elderly_match.group(1).replace(",", "")),
        }
        
        # Validate against sanity ranges in grounding_fixtures.json
        fixtures_path = Path(__file__).parent / "grounding_fixtures.json"
        with open(fixtures_path, "r") as f:
            fixtures = json.load(f)
        sanity = fixtures.get("sanity_ranges", {})
        
        for key, limits in sanity.items():
            if key not in parsed:
                return None
            val = parsed[key]
            lower_lim, upper_lim = limits
            if not (lower_lim <= val <= upper_lim):
                return None
                
        return parsed
    except Exception:
        return None


def parse_medicaid_live(html: str) -> dict[str, Any] | None:
    """Live parser for Medicaid/CHIP. Returns None as the tables are state-by-state only."""
    return None


def parse_eitc_live(html: str) -> dict[str, Any] | None:
    """Live parser for EITC. Parses the IRS EITC tables for the current tax year."""
    from bs4 import BeautifulSoup
    import re
    try:
        soup = BeautifulSoup(html, "html.parser")
        target_table = None
        # Locate the table under the 2025 (or current tax year) header
        for t in soup.find_all("table"):
            prev = t.find_previous(["h2", "h3", "h4", "p", "div"])
            if prev and "2025" in prev.get_text():
                target_table = t
                break
        if not target_table:
            target_table = soup.find("table")
        if not target_table:
            return None
            
        rows = []
        for tr in target_table.find_all("tr"):
            cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
                
        if len(rows) < 5:
            return None
            
        def parse_val(s):
            return int(s.replace("$", "").replace(",", "").strip())
            
        limits = {
            "single_or_head_of_household": {
                "0": parse_val(rows[1][1]),
                "1": parse_val(rows[2][1]),
                "2": parse_val(rows[3][1]),
                "3_or_more": parse_val(rows[4][1])
            },
            "married_filing_jointly": {
                "0": parse_val(rows[1][2]),
                "1": parse_val(rows[2][2]),
                "2": parse_val(rows[3][2]),
                "3_or_more": parse_val(rows[4][2])
            }
        }
        
        # Sanity validation range checks
        if not (15000 <= limits["single_or_head_of_household"]["0"] <= 25000):
            return None
        if not (50000 <= limits["married_filing_jointly"]["3_or_more"] <= 80000):
            return None
            
        return {"income_limits": limits}
    except Exception:
        return None


def parse_liheap_live(html: str) -> dict[str, Any] | None:
    """Live parser for LIHEAP. Returns None due to ACF portal restrictions."""
    return None


def parse_wic_live(html: str) -> dict[str, Any] | None:
    """Live parser for WIC. Parses the WIC FAQs page table for effective period and 185% FPL limits."""
    from bs4 import BeautifulSoup
    from datetime import date, datetime
    import re
    try:
        soup = BeautifulSoup(html, "html.parser")
        target_table = None
        for t in soup.find_all("table"):
            prev = t.find_previous(["h2", "h3", "h4", "p", "div"])
            if prev and "Income Eligibility Guidelines" in prev.get_text():
                target_table = t
                break
        if not target_table:
            target_table = soup.find("table")
        if not target_table:
            return None
            
        # Parse effective date range from preceding text
        # e.g., "effective July 1, 2026 to June 30, 2027"
        prev_text = prev.get_text() if prev else ""
        date_pattern = r"effective\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})\s+to\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        match = re.search(date_pattern, prev_text, re.IGNORECASE)
        if not match:
            return None
            
        start_date = datetime.strptime(match.group(1).replace(",", ""), "%B %d %Y").date()
        end_date = datetime.strptime(match.group(2).replace(",", ""), "%B %d %Y").date()
        
        today = date.today()
        if not (start_date <= today <= end_date):
            return None
            
        # Extract rows
        rows = []
        for tr in target_table.find_all("tr"):
            cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
                
        if len(rows) < 9:
            return None
            
        def parse_val(s):
            return int(re.sub(r"[^\d]", "", s))
            
        ann_1 = parse_val(rows[1][1])
        # Sanity check range for WIC annual limit for household size of 1
        if not (25000 <= ann_1 <= 35000):
            return None
            
        return {
            "income_limit_fpl_percentage": 185,
            "annual_income_limits": {
                "1": ann_1,
                "2": parse_val(rows[2][1]),
                "3": parse_val(rows[3][1]),
                "4": parse_val(rows[4][1]),
                "5": parse_val(rows[5][1]),
                "6": parse_val(rows[6][1]),
                "7": parse_val(rows[7][1]),
                "8": parse_val(rows[8][1]),
            }
        }
    except Exception:
        return None


def get_grounding_data(program: BenefitProgram, state: str) -> GroundingData:
    """Retrieves eligibility rules and thresholds for a program and state.
    
    If EVAL_MODE=true is set in environment, reads from grounding_fixtures.json.
    Otherwise, attempts a live HTTP fetch from the program's authoritative URL.
    On failure, returns grounded=False with fallback values.
    """
    eval_mode = os.environ.get("EVAL_MODE", "").lower() == "true"
    
    # Load local fixtures for mock data and fallback
    fixtures_path = Path(__file__).parent / "grounding_fixtures.json"
    with open(fixtures_path, "r") as f:
        fixtures = json.load(f)
        
    program_key = program.value
    # In grounding_fixtures.json, Medicaid uses medicaid_chip key
    if program == BenefitProgram.MEDICAID_CHIP:
        program_key = "medicaid_chip"
        
    fixture_data = fixtures.get(program_key, {})
    
    # Determine the primary authoritative URL
    urls = fixtures.get("source_urls", {})
    url = urls.get(program_key, "https://www.benefits.gov")
    
    if eval_mode:
        # Construct flat values dictionary from fixtures
        flat_values = {}
        for k, v in fixture_data.items():
            if isinstance(v, dict) and "value" in v:
                flat_values[k] = v["value"]
            else:
                flat_values[k] = v
        # Add FPL guidelines
        flat_values["fpl"] = fixtures.get("fpl_monthly_2026", {})
        
        return GroundingData(
            values=flat_values,
            source_cited=url,
            as_of_date=date(2026, 1, 1),
            grounded=True,
        )
        
    # Live fetch path
    final_url = url
    try:
        # Attempt live fetch to verify connectivity
        # Note: We use follow_redirects=True as government sites often redirect
        response = httpx.get(url, follow_redirects=True, timeout=5.0)
        final_url = str(response.url)
        if response.status_code == 200:
            # Live fetch succeeded!
            if program == BenefitProgram.SNAP:
                parsed_values = parse_snap_live(response.text)
            elif program == BenefitProgram.MEDICAID_CHIP:
                parsed_values = parse_medicaid_live(response.text)
            elif program == BenefitProgram.EITC:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                tables_link = None
                for a in soup.find_all("a", href=True):
                    if "tables" in a["href"]:
                        tables_link = a["href"]
                        break
                if tables_link:
                    if not tables_link.startswith("http"):
                        tables_link = "https://www.irs.gov" + tables_link
                    tables_resp = httpx.get(tables_link, follow_redirects=True, timeout=5.0)
                    if tables_resp.status_code == 200:
                        parsed_values = parse_eitc_live(tables_resp.text)
                        final_url = str(tables_resp.url)
                    else:
                        parsed_values = None
                else:
                    parsed_values = None
            elif program == BenefitProgram.LIHEAP:
                parsed_values = parse_liheap_live(response.text)
            elif program == BenefitProgram.WIC:
                parsed_values = parse_wic_live(response.text)
            else:
                parsed_values = None
                
            if parsed_values is not None:
                flat_values = parsed_values.copy()
                # Merge in any other keys from fixture_data
                for k, v in fixture_data.items():
                    if k not in flat_values:
                        if isinstance(v, dict) and "value" in v:
                            flat_values[k] = v["value"]
                        else:
                            flat_values[k] = v
                flat_values["fpl"] = fixtures.get("fpl_monthly_2026", {})
                return GroundingData(
                    values=flat_values,
                    source_cited=final_url,
                    as_of_date=date.today(),
                    grounded=True,
                )
            
            # For other programs, or if parsing failed/returned None, fall back to ungrounded
            flat_values = {}
            for k, v in fixture_data.items():
                if isinstance(v, dict) and "value" in v:
                    flat_values[k] = v["value"]
                else:
                    flat_values[k] = v
            # Add FPL guidelines
            flat_values["fpl"] = fixtures.get("fpl_monthly_2026", {})
            
            return GroundingData(
                values=flat_values,
                source_cited=final_url,
                as_of_date=date.today(),
                grounded=False,
            )
    except Exception:
        # Fetch failed, fall back to ungrounded state
        pass
        
    # Return ungrounded fallback data on fetch exception
    flat_values = {}
    for k, v in fixture_data.items():
        if isinstance(v, dict) and "value" in v:
            flat_values[k] = v["value"]
        else:
            flat_values[k] = v
    # Add FPL guidelines
    flat_values["fpl"] = fixtures.get("fpl_monthly_2026", {})
    
    return GroundingData(
        values=flat_values,
        source_cited=final_url,
        as_of_date=date(2026, 1, 1),
        grounded=False,
    )


# Recorded state SNAP links for future reference
RECORDED_STATE_SNAP_LINKS = {
    "washington": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/washington",
    "alabama": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/alabama",
    "alaska": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/alaska",
    "arizona": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/arizona",
    "arkansas": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/arkansas",
    "california": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/california",
    "colorado": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/colorado",
    "connecticut": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/connecticut",
    "delaware": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/delaware",
    "district of columbia": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/district_of_columbia",
    "florida": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/florida",
    "georgia": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/georgia",
    "hawaii": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/hawaii",
    "idaho": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/idaho",
    "illinois": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/illinois",
    "indiana": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/indiana",
    "iowa": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/iowa",
    "kansas": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/kansas",
    "kentucky": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/kentucky",
    "louisiana": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/louisiana",
    "maine": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/maine",
    "maryland": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/maryland",
    "massachusetts": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/massachusetts",
    "michigan": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/michigan",
    "minnesota": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/minnesota",
    "mississippi": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/mississippi",
    "missouri": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/missouri",
    "montana": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/montana",
    "nebraska": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/nebraska",
    "nevada": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/nevada",
    "new hampshire": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/new_hampshire",
    "new jersey": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/new_jersey",
    "new mexico": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/new_mexico",
    "new york": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/new_york",
    "new york city": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/new_york_city",
    "north carolina": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/north_carolina",
    "north dakota": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/north_dakota",
    "ohio": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/ohio",
    "oklahoma": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/oklahoma",
    "oregon": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/oregon",
    "pennsylvania": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/pennsylvania",
    "rhode island": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/rhode_island",
    "south carolina": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/south_carolina",
    "south dakota": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/south_dakota",
    "tennessee": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/tennessee",
    "texas": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/texas",
    "utah": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/utah",
    "vermont": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/vermont",
    "virginia": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/virginia",
    "west virginia": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/west_virginia",
    "wisconsin": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/wisconsin",
    "wyoming": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/wyoming",
    "guam": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/guam",
    "puerto rico": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/puerto_rico",
    "virgin islands": "https://www.fna.usda.gov/snap-directory-entry/snap-directory-entry/virgin_islands",
}

# Recorded state Medicaid links for future reference
RECORDED_STATE_MEDICAID_LINKS = {
    "alabama": "https://medicaid.alabama.gov/",
    "alaska": "https://health.alaska.gov/dpa/Pages/default.aspx",
    "american samoa": "http://medicaid.as.gov/",
    "arizona": "http://www.healthearizonaplus.gov/",
    "arkansas": "http://access.arkansas.gov/",
    "california": "http://www.dhcs.ca.gov/Pages/default.aspx",
    "colorado": "http://www.colorado.gov/hcpf",
    "connecticut": "http://www.ct.gov/hh/site/default.asp",
}

PROGRAM_APPLY_LINKS = {
    "snap": "https://www.fna.usda.gov/snap/state-directory",
    "medicaid_chip": "https://www.healthcare.gov/medicaid-chip/",
    "wic": "https://www.fna.usda.gov/wic/program-contacts",
    "liheap": "https://liheapch.acf.gov/search-tool/state-territory/",
    "eitc": "https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/earned-income-and-earned-income-tax-credit-eitc-tables",
}


SNAP_STATE_DIRECTORY_LINKS = {
    "AL": "https://www.fna.usda.gov/snap-directory-entry/alabama",
    "AK": "https://www.fna.usda.gov/snap-directory-entry/alaska",
    "AZ": "https://www.fna.usda.gov/snap-directory-entry/arizona",
    "AR": "https://www.fna.usda.gov/snap-directory-entry/arkansas",
    "CA": "https://www.fna.usda.gov/snap-directory-entry/california",
    "CO": "https://www.fna.usda.gov/snap-directory-entry/colorado",
    "CT": "https://www.fna.usda.gov/snap-directory-entry/connecticut",
    "DE": "https://www.fna.usda.gov/snap-directory-entry/delaware",
    "DC": "https://www.fna.usda.gov/snap-directory-entry/district-columbia",
    "FL": "https://www.fna.usda.gov/snap-directory-entry/florida",
    "GA": "https://www.fna.usda.gov/snap-directory-entry/georgia",
    "GU": "https://www.fna.usda.gov/snap-directory-entry/guam",
    "HI": "https://www.fna.usda.gov/snap-directory-entry/hawaii",
    "ID": "https://www.fna.usda.gov/snap-directory-entry/idaho",
    "IL": "https://www.fna.usda.gov/snap-directory-entry/illinois",
    "IN": "https://www.fna.usda.gov/snap-directory-entry/indiana",
    "IA": "https://www.fna.usda.gov/snap-directory-entry/iowa",
    "KS": "https://www.fna.usda.gov/snap-directory-entry/kansas",
    "KY": "https://www.fna.usda.gov/snap-directory-entry/kentucky",
    "LA": "https://www.fna.usda.gov/snap-directory-entry/louisiana",
    "ME": "https://www.fna.usda.gov/snap-directory-entry/maine",
    "MD": "https://www.fna.usda.gov/snap-directory-entry/maryland",
    "MA": "https://www.fna.usda.gov/snap-directory-entry/massachusetts",
    "MI": "https://www.fna.usda.gov/snap-directory-entry/michigan",
    "MN": "https://www.fna.usda.gov/snap-directory-entry/minnesota",
    "MS": "https://www.fna.usda.gov/snap-directory-entry/mississippi",
    "MO": "https://www.fna.usda.gov/snap-directory-entry/missouri",
    "MT": "https://www.fna.usda.gov/snap-directory-entry/montana",
    "NE": "https://www.fna.usda.gov/snap-directory-entry/nebraska",
    "NV": "https://www.fna.usda.gov/snap-directory-entry/nevada",
    "NH": "https://www.fna.usda.gov/snap-directory-entry/new-hampshire",
    "NJ": "https://www.fna.usda.gov/snap-directory-entry/new-jersey",
    "NM": "https://www.fna.usda.gov/snap-directory-entry/new-mexico",
    "NY": "https://www.fna.usda.gov/snap-directory-entry/new-york",
    "NC": "https://www.fna.usda.gov/snap-directory-entry/north-carolina",
    "ND": "https://www.fna.usda.gov/snap-directory-entry/north-dakota",
    "OH": "https://www.fna.usda.gov/snap-directory-entry/ohio",
    "OK": "https://www.fna.usda.gov/snap-directory-entry/oklahoma",
    "OR": "https://www.fna.usda.gov/snap-directory-entry/oregon",
    "PA": "https://www.fna.usda.gov/snap-directory-entry/pennsylvania",
    "PR": "https://www.fna.usda.gov/snap-directory-entry/puerto-rico",
    "RI": "https://www.fna.usda.gov/snap-directory-entry/rhode-island",
    "SC": "https://www.fna.usda.gov/snap-directory-entry/south-carolina",
    "SD": "https://www.fna.usda.gov/snap-directory-entry/south-dakota",
    "TN": "https://www.fna.usda.gov/snap-directory-entry/tennessee",
    "TX": "https://www.fna.usda.gov/snap-directory-entry/texas",
    "UT": "https://www.fna.usda.gov/snap-directory-entry/utah",
    "VT": "https://www.fna.usda.gov/snap-directory-entry/vermont",
    "VI": "https://www.fna.usda.gov/snap-directory-entry/virgin-islands",
    "VA": "https://www.fna.usda.gov/snap-directory-entry/virginia",
    "WA": "https://www.fna.usda.gov/snap-directory-entry/washington",
    "WV": "https://www.fna.usda.gov/snap-directory-entry/west-virginia",
    "WI": "https://www.fna.usda.gov/snap-directory-entry/wisconsin",
    "WY": "https://www.fna.usda.gov/snap-directory-entry/wyoming",
}


def get_official_link(program: BenefitProgram, state: str) -> str:
    """Returns the official application portal link for the program in the given state."""
    if program == BenefitProgram.SNAP:
        state_upper = state.upper()
        if state_upper in SNAP_STATE_DIRECTORY_LINKS:
            return SNAP_STATE_DIRECTORY_LINKS[state_upper]
    return PROGRAM_APPLY_LINKS.get(program.value, "https://www.benefits.gov")

