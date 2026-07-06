import pytest
from citizenbenefits.nodes import pii_guard

class DummyContext:
    def __init__(self):
        self.state = {}

def test_pii_guard_ssn():
    ctx = DummyContext()
    ssn_text = "My SSN is 123-45-6789."
    event = pii_guard(ctx, ssn_text)
    
    assert event.actions.route == "pii_detected"
    assert "WARNING: Request rejected" in event.output
    assert "123-45-6789" not in event.output


def test_pii_guard_email():
    ctx = DummyContext()
    email_text = "Contact me at test@example.com."
    event = pii_guard(ctx, email_text)
    
    assert event.actions.route == "pii_detected"
    assert "WARNING: Request rejected" in event.output
    assert "test@example.com" not in event.output


def test_pii_guard_clean():
    ctx = DummyContext()
    clean_text = "I live in Ohio with a household of 3."
    # Mock Client to prevent actual API calls for clean path
    class MockClient:
        def __init__(self):
            self.models = self
        def generate_content(self, **kwargs):
            class MockResponse:
                text = '{"has_pii": false, "pii_types": [], "explanation": "Clean text"}'
            return MockResponse()

    # Monkeypatch genai.Client
    import google.genai as genai
    original_client = genai.Client
    genai.Client = MockClient
    
    try:
        event = pii_guard(ctx, clean_text)
        assert event.actions.route == "clean"
        assert event.output == clean_text
    finally:
        genai.Client = original_client


def test_pii_guard_exception_fails_closed(monkeypatch):
    ctx = DummyContext()
    clean_text = "I live in Ohio."
    
    # Force genai.Client constructor or call to raise an exception
    import google.genai as genai
    monkeypatch.setattr(genai, "Client", lambda *args, **kwargs: Exception("Simulated API failure"))
    
    event = pii_guard(ctx, clean_text)
    
    assert event.actions.route == "pii_detected"
    assert "Safety check could not complete" in event.output
