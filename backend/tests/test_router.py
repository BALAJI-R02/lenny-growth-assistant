"""Tests: router classification."""
from __future__ import annotations

import pytest

from app.services.router import Route, classify


@pytest.mark.parametrize("message,expected_route", [
    # Essay triggers
    ("Write a ship 30 for 30 essay about retention", Route.ESSAY),
    ("Write a ship30 essay about PLG", Route.ESSAY),
    ("Write an essay about product-led growth", Route.ESSAY),
    ("Draft an essay about activation metrics", Route.ESSAY),
    # Artifact triggers
    ("Generate artifact from our conversation", Route.ARTIFACT),
    ("Create html dashboard for retention metrics", Route.ARTIFACT),
    ("Create markdown summary of this discussion", Route.ARTIFACT),
    ("Generate a document about our findings", Route.ARTIFACT),
    ("Make html landing page for our product", Route.ARTIFACT),
    # QA (default)
    ("What does Lenny say about retention?", Route.QA),
    ("How do top companies think about activation?", Route.QA),
    ("Tell me about product-led growth from Lenny's interviews", Route.QA),
    ("What is the capital of France?", Route.QA),
    ("", Route.QA),  # empty → QA default
])
def test_classify_routing(message: str, expected_route: Route):
    assert classify(message) == expected_route


def test_classify_case_insensitive():
    assert classify("WRITE A SHIP 30 ESSAY ABOUT GROWTH") == Route.ESSAY
    assert classify("CREATE HTML DASHBOARD") == Route.ARTIFACT
    assert classify("WHAT DOES LENNY SAY") == Route.QA


def test_classify_returns_enum():
    result = classify("any message")
    assert isinstance(result, Route)
    assert result in list(Route)
