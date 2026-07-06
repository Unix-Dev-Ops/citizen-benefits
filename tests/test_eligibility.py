import pytest
from google.adk import Context
from citizenbenefits.nodes import eligibility_engine, evaluate_snap, evaluate_medicaid, evaluate_eitc, evaluate_wic
from citizenbenefits.schemas import (
    LikelyEligible,
    BenefitProgram,
    IncomeBand,
    EarnedIncomeShare,
    AgeBand,
    CitizenshipStatus
)
from citizenbenefits.tools import GroundingData
from datetime import date

# 1. Medicaid standard adult, total_income_band 130_200_fpl (130-200), limit 138 -> POSSIBLY
def test_medicaid_straddles_limit(build_request):
    req = build_request(
        total_income_band=IncomeBand.FPL_130_200,
        age_band=AgeBand.AGE_18_59,
        is_pregnant=False,
        num_children=0
    )
    # Get standard grounding data for Medicaid
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.MEDICAID_CHIP, req.state)
    
    # Verify adult limit is 138
    assert data.values["adult_limit_fpl_percentage"] == 138
    
    res = evaluate_medicaid(req, data)
    assert res.likely_eligible == LikelyEligible.POSSIBLY
    assert "straddles" in res.reason


# 2. SNAP age_band 65_plus, 100_130_fpl, no disability -> gross test waived (reason mentions waiver), exempt 65+
def test_snap_elderly_exempt(build_request):
    req = build_request(
        total_income_band=IncomeBand.FPL_100_130,
        age_band=AgeBand.AGE_65_PLUS,
        has_disability=False,
        earned_income_share=EarnedIncomeShare.NONE
    )
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.SNAP, req.state)
    
    res = evaluate_snap(req, data)
    
    # Gross requirement should be waived (reasons mentions "waived")
    assert "gross income requirement waived" in res.reason
    assert "Exempt from SNAP work requirements (age 65+)" in res.reason
    
    # Net test: lower=100, upper=130. standard deduction = 200. fpl_monthly for 1 is 1256 (from contiguous_us).
    # multiplier = 1.0 (no earned income). std_ded_pct = (200 / 1256) * 100 = 15.9%.
    # lower_net_pct = 100 - 15.9 = 84.1%.
    # upper_net_pct = 130 - 15.9 = 114.1%.
    # Net limit is 100%. So lower_net_pct <= 100 < upper_net_pct.
    # Therefore, net test straddles 100%, leading to POSSIBLY.
    assert res.likely_eligible == LikelyEligible.POSSIBLY


# 3. Any program with grounded=False and an over-limit band -> POSSIBLY, never UNLIKELY
def test_ungrounded_over_limit_force_possibly(build_request):
    req = build_request(
        total_income_band=IncomeBand.OVER_200_FPL,
        age_band=AgeBand.AGE_18_59
    )
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.SNAP, req.state)
    
    # Mock grounded=False
    data.grounded = False
    
    res = evaluate_snap(req, data)
    
    # Over 200% FPL exceeds SNAP gross limit of 130%.
    # But because grounded=False, UNLIKELY is forced to POSSIBLY.
    assert res.likely_eligible == LikelyEligible.POSSIBLY
    assert "Based on the most recent verified rules; live verification was not available" in res.reason


# 4. EITC childless, age_band 18_59 -> POSSIBLY with age verification note (because age 18 is in 18_59)
def test_eitc_childless_age_18(build_request):
    req = build_request(
        total_income_band=IncomeBand.UNDER_50_FPL,
        age_band=AgeBand.AGE_18_59,
        num_children=0,
        earned_income_share=EarnedIncomeShare.SOME
    )
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.EITC, req.state)
    
    res = evaluate_eitc(req, data)
    
    assert res.likely_eligible == LikelyEligible.POSSIBLY
    assert "Age requirement: Age 18 is below childless minimum age of 19" in res.reason


# 5. WIC with num_children > 0 only (not pregnant, not under_18) -> POSSIBLY with under-5 note
def test_wic_children_only(build_request):
    req = build_request(
        total_income_band=IncomeBand.FPL_100_130,
        age_band=AgeBand.AGE_18_59,
        is_pregnant=False,
        num_children=2,
        household_size=3
    )
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.WIC, req.state)
    
    res = evaluate_wic(req, data)
    
    assert res.likely_eligible == LikelyEligible.POSSIBLY
    assert "cannot distinguish children under 5 from under 18" in res.reason


# 6. SNAP with a required grounding key removed -> POSSIBLY, grounded=False
def test_snap_missing_key(build_request):
    req = build_request()
    from citizenbenefits.tools import get_grounding_data
    data = get_grounding_data(BenefitProgram.SNAP, req.state)
    
    # Remove standard_deduction key
    data.values.pop("standard_deduction")
    
    res = evaluate_snap(req, data)
    
    assert res.likely_eligible == LikelyEligible.POSSIBLY
    assert res.grounded is False
    assert "SNAP grounding rules could not be fully retrieved" in res.reason
