from pathlib import Path
from citizenbenefits.tools import parse_snap_live, parse_eitc_live, parse_wic_live

def test_parse_snap_live_success():
    fixture_path = Path(__file__).parent / "fixtures" / "snap_page.html"
    with open(fixture_path, "r") as f:
        html = f.read()
        
    result = parse_snap_live(html)
    assert result is not None
    assert result["gross_income_limit_fpl_percentage"] == 130
    assert result["net_income_limit_fpl_percentage"] == 100
    assert result["standard_deduction"] == 209
    assert result["earned_income_deduction_pct"] == 20
    assert result["asset_limit_standard"] == 3000
    assert result["asset_limit_elderly_disabled"] == 4500

def test_parse_snap_live_mangled():
    html = "<html><body>Mangled content without standard deduction or limits</body></html>"
    result = parse_snap_live(html)
    assert result is None

def test_parse_other_programs_return_none():
    from citizenbenefits.tools import (
        parse_medicaid_live,
        parse_eitc_live,
        parse_liheap_live,
        parse_wic_live
    )
    assert parse_medicaid_live("<html></html>") is None
    assert parse_liheap_live("<html></html>") is None
    assert parse_wic_live("<html></html>") is None


def test_parse_eitc_live_success():
    fixture_path = Path(__file__).parent / "fixtures" / "eitc_tables.html"
    with open(fixture_path, "r") as f:
        html = f.read()
        
    result = parse_eitc_live(html)
    assert result is not None
    assert result["income_limits"]["single_or_head_of_household"]["0"] == 19104
    assert result["income_limits"]["married_filing_jointly"]["3_or_more"] == 68675


def test_parse_wic_live_success():
    fixture_path = Path(__file__).parent / "fixtures" / "wic_faqs.html"
    with open(fixture_path, "r") as f:
        html = f.read()
        
    result = parse_wic_live(html)
    assert result is not None
    assert result["income_limit_fpl_percentage"] == 185
    assert result["annual_income_limits"]["1"] == 29526
    assert result["annual_income_limits"]["8"] == 103082



