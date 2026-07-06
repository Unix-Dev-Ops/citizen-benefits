import os
import json
import pytest
from pathlib import Path
from citizenbenefits.schemas import EligibilityRequest, CitizenshipStatus, IncomeBand, EarnedIncomeShare, AgeBand

# Force EVAL_MODE for all tests
os.environ["EVAL_MODE"] = "true"

@pytest.fixture(scope="session")
def grounding_fixtures():
    fixtures_path = Path(__file__).parent.parent / "src" / "citizenbenefits" / "grounding_fixtures.json"
    with open(fixtures_path, "r") as f:
        return json.load(f)

@pytest.fixture
def build_request():
    def _build(
        status=CitizenshipStatus.US_CITIZEN,
        household_size=1,
        total_income_band=IncomeBand.UNDER_50_FPL,
        earned_income_share=EarnedIncomeShare.NONE,
        age_band=AgeBand.AGE_18_59,
        has_disability=False,
        is_pregnant=False,
        num_children=0,
        state="OH",
        zip_code="43215",
        is_married=False,
        is_veteran_or_military=False
    ):
        return EligibilityRequest(
            status=status,
            household_size=household_size,
            total_income_band=total_income_band,
            earned_income_share=earned_income_share,
            age_band=age_band,
            has_disability=has_disability,
            is_pregnant=is_pregnant,
            num_children=num_children,
            state=state,
            zip=zip_code,
            is_married=is_married,
            is_veteran_or_military=is_veteran_or_military
        )
    return _build
