from citizenbenefits.nodes import router, explainer
from citizenbenefits.schemas import EligibilityRequest, ProgramResult, BenefitProgram, LikelyEligible
from citizenbenefits.tools import get_official_link
from datetime import date

class DummyContext:
    def __init__(self, state=None):
        self.state = state or {}

def test_router_populates_links(build_request):
    req = build_request(state="OH")
    
    ctx = DummyContext(state={"request": req})
    
    results = [
        ProgramResult(
            program=BenefitProgram.SNAP,
            likely_eligible=LikelyEligible.LIKELY,
            reason="Meets requirements",
            source_cited="https://fns.usda.gov",
            as_of_date=date.today(),
            grounded=True,
            apply_link=""
        ),
        ProgramResult(
            program=BenefitProgram.MEDICAID_CHIP,
            likely_eligible=LikelyEligible.LIKELY,
            reason="Meets requirements",
            source_cited="https://medicaid.gov",
            as_of_date=date.today(),
            grounded=True,
            apply_link=""
        )
    ]
    
    event = router(ctx, results)
    updated_results = event.output
    
    assert updated_results[0].apply_link == "https://www.fna.usda.gov/snap-directory-entry/ohio"
    assert updated_results[1].apply_link == "https://www.healthcare.gov/medicaid-chip/"



def test_explainer_disclaimer(build_request):
    ctx = DummyContext()
    results = [
        ProgramResult(
            program=BenefitProgram.SNAP,
            likely_eligible=LikelyEligible.LIKELY,
            reason="Meets requirements",
            source_cited="https://fns.usda.gov",
            as_of_date=date.today(),
            grounded=True,
            apply_link="https://benefits.ohio.gov"
        )
    ]
    
    event = explainer(ctx, results)
    
    # Check that disclaimer is present in the markdown output text
    text_content = event.content.parts[0].text
    mandatory_disclaimer = "This is an estimate, not a determination. Rules change. Only the official agency can decide."
    assert mandatory_disclaimer in text_content
