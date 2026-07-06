from google.adk import Workflow

from citizenbenefits.nodes import (
    pii_guard,
    pii_refusal_node,
    status_gate,
    results_stop_node,
    eligibility_engine,
    router,
    explainer,
    invalid_input_node,
)

root_agent = Workflow(
    name="citizenbenefits",
    edges=[
        ("START", pii_guard),
        (pii_guard, {"pii_detected": pii_refusal_node, "clean": status_gate}),
        (
            status_gate,
            {
                "ineligible": results_stop_node,
                "eligible": eligibility_engine,
                "invalid_input": invalid_input_node,
            },
        ),
        (eligibility_engine, router),
        (router, explainer),
    ],
)
