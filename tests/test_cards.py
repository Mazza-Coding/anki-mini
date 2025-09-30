"""Tests for card operations."""

import pytest
from pathlib import Path
import tempfile
import shutil
from anki_mini.deck import DeckManager
from anki_mini.cards import CardManager


@pytest.fixture
def temp_deck():
    """Create temporary deck."""
    temp_dir = Path(tempfile.mkdtemp())
    manager = DeckManager(temp_dir)
    slug = manager.create_deck("Test Deck")
    deck_path = temp_dir / 'decks' / slug
    
    yield deck_path
    
    shutil.rmtree(temp_dir)


def test_add_card(temp_deck):
    """Test adding a card."""
    manager = CardManager(temp_deck)
    
    result = manager.add_card("hello", "bonjour")
    
    assert result is True
    cards = manager.get_all_cards()
    assert len(cards) == 1
    assert cards[0][1] == "hello"
    assert cards[0][2] == "bonjour"


def test_add_duplicate_card(temp_deck):
    """Test adding duplicate card."""
    manager = CardManager(temp_deck)
    
    manager.add_card("hello", "bonjour")
    result = manager.add_card("hello", "bonjour")
    
    assert result is False
    assert len(manager.get_all_cards()) == 1


def test_add_empty_card(temp_deck):
    """Test adding empty card raises error."""
    manager = CardManager(temp_deck)
    
    with pytest.raises(ValueError):
        manager.add_card("", "test")
    
    with pytest.raises(ValueError):
        manager.add_card("test", "")


def test_get_due_cards_new(temp_deck):
    """Test new cards are due."""
    manager = CardManager(temp_deck)
    
    manager.add_card("hello", "bonjour")
    due_cards = manager.get_due_cards()
    
    assert len(due_cards) == 1


def test_import_export_roundtrip(temp_deck):
    """Test import/export round trip."""
    manager = CardManager(temp_deck)
    
    # Add some cards
    manager.add_card("hello", "bonjour")
    manager.add_card("goodbye", "au revoir")
    
    # Export
    export_file = temp_deck / "export.txt"
    count = manager.export_cards(export_file)
    assert count == 2
    
    # Create new deck and import
    temp_dir = temp_deck.parent.parent
    manager2 = DeckManager(temp_dir)
    slug2 = manager2.create_deck("Import Test")
    deck_path2 = temp_dir / 'decks' / slug2
    
    manager_import = CardManager(deck_path2)
    added, skipped = manager_import.import_cards(export_file)
    
    assert added == 2
    assert skipped == 0
    assert len(manager_import.get_all_cards()) == 2
