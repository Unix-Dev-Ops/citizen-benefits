from citizenbenefits.nodes import status_gate
from citizenbenefits.schemas import CitizenshipStatus, LikelyEligible, BenefitProgram

def test_status_gate_ineligible(build_request):
    req = build_request(status=CitizenshipStatus.OTHER_NOT_LISTED)
    event = status_gate(req)
    
    assert event.actions.route == "ineligible"
    results = event.output
    assert len(results) == 5
    for res in results:
        assert res.likely_eligible == LikelyEligible.NOT_AVAILABLE_FOR_STATUS
        assert res.grounded is False
        assert "Ineligibility Scope" in res.reason


def test_status_gate_eligible(build_request):
    req = build_request(status=CitizenshipStatus.US_CITIZEN)
    event = status_gate(req)
    
    assert event.actions.route == "eligible"
    assert event.output == req
    assert event.actions.state_delta["request"] == req
