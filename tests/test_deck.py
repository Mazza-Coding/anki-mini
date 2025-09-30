"""Tests for deck management."""

import pytest
from pathlib import Path
import tempfile
import shutil
from anki_mini.deck import DeckManager


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_create_deck(temp_data_dir):
    """Test deck creation."""
    manager = DeckManager(temp_data_dir)
    
    slug = manager.create_deck("Test Deck")
    
    assert slug == "test-deck"
    assert (temp_data_dir / 'decks' / 'test-deck').exists()
    assert (temp_data_dir / 'decks' / 'test-deck' / 'cards.txt').exists()
    assert (temp_data_dir / 'decks' / 'test-deck' / 'state.json').exists()


def test_create_deck_with_activation(temp_data_dir):
    """Test deck creation with immediate activation."""
    manager = DeckManager(temp_data_dir)
    
    slug = manager.create_deck("Active Deck", set_active=True)
    
    assert manager.get_active_deck() == "active-deck"


def test_list_decks(temp_data_dir):
    """Test listing decks."""
    manager = DeckManager(temp_data_dir)
    
    manager.create_deck("Deck A", set_active=True)
    manager.create_deck("Deck B")
    
    decks = manager.list_decks()
    
    assert len(decks) == 2
    assert decks[0]['display_name'] == "Deck A"
    assert decks[0]['is_active'] is True
    assert decks[1]['display_name'] == "Deck B"
    assert decks[1]['is_active'] is False


def test_rename_deck(temp_data_dir):
    """Test deck renaming."""
    manager = DeckManager(temp_data_dir)
    
    manager.create_deck("Old Name", set_active=True)
    manager.rename_deck("Old Name", "New Name")
    
    decks = manager.list_decks()
    assert decks[0]['display_name'] == "New Name"
    assert decks[0]['slug'] == "new-name"


def test_delete_empty_deck(temp_data_dir):
    """Test deleting empty deck."""
    manager = DeckManager(temp_data_dir)
    
    manager.create_deck("To Delete")
    manager.delete_deck("To Delete", force=True)
    
    assert len(manager.list_decks()) == 0


def test_sanitize_deck_name(temp_data_dir):
    """Test deck name sanitization."""
    manager = DeckManager(temp_data_dir)
    
    slug = manager.create_deck("Test Deck With Spaces!")
    
    assert slug == "test-deck-with-spaces"


def test_active_deck_persistence(temp_data_dir):
    """Test active deck persists."""
    manager = DeckManager(temp_data_dir)
    
    manager.create_deck("Deck 1", set_active=True)
    manager.create_deck("Deck 2")
    
    # Create new manager instance
    manager2 = DeckManager(temp_data_dir)
    
    assert manager2.get_active_deck() == "deck-1"
