"""Tests for utility functions."""

import pytest
from anki_mini.utils import (
    sanitize_deck_name,
    stable_card_id,
    levenshtein_distance,
    check_answer
)


def test_sanitize_deck_name():
    """Test deck name sanitization."""
    assert sanitize_deck_name("Hello World") == "hello-world"
    assert sanitize_deck_name("Test123") == "test123"
    assert sanitize_deck_name("Special!@#$%Chars") == "specialchars"
    assert sanitize_deck_name("  spaces  ") == "spaces"
    assert sanitize_deck_name("") == "default"


def test_stable_card_id():
    """Test card ID generation."""
    id1 = stable_card_id("front", "back")
    id2 = stable_card_id("front", "back")
    id3 = stable_card_id("front", "different")
    
    assert id1 == id2  # Same input = same ID
    assert id1 != id3  # Different input = different ID
    assert len(id1) == 16  # Fixed length


def test_levenshtein_distance():
    """Test Levenshtein distance calculation."""
    assert levenshtein_distance("hello", "hello") == 0
    assert levenshtein_distance("hello", "helo") == 1
    assert levenshtein_distance("hello", "world") == 4
    assert levenshtein_distance("", "") == 0
    assert levenshtein_distance("abc", "") == 3


def test_check_answer_exact():
    """Test exact answer matching."""
    correct, match_type = check_answer("hello", "hello")
    assert correct is True
    assert match_type == "exact"
    
    # Case insensitive
    correct, match_type = check_answer("HELLO", "hello")
    assert correct is True
    assert match_type == "exact"
    
    # With whitespace
    correct, match_type = check_answer("  hello  ", "hello")
    assert correct is True
    assert match_type == "exact"


def test_check_answer_lenient():
    """Test lenient answer matching."""
    correct, match_type = check_answer("helo", "hello", threshold=2)
    assert correct is True
    assert match_type == "lenient"
    
    correct, match_type = check_answer("bonjur", "bonjour", threshold=2)
    assert correct is True
    assert match_type == "lenient"


def test_check_answer_mismatch():
    """Test answer mismatch."""
    correct, match_type = check_answer("world", "hello", threshold=2)
    assert correct is False
    assert match_type == "mismatch"


def test_check_answer_multiple_options():
    """Test multiple acceptable answers."""
    correct, match_type = check_answer("hello", "hi;hello;hey")
    assert correct is True
    
    correct, match_type = check_answer("hey", "hi;hello;hey")
    assert correct is True
    
    correct, match_type = check_answer("bonjour", "hi;hello;hey")
    assert correct is False
