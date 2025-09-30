"""Initialization and migration logic."""

import shutil
from pathlib import Path
from .deck import DeckManager
from .utils import atomic_write_json


def initialize_data_dir(data_dir: Path) -> None:
    """Initialize data directory structure."""
    
    # Check if legacy structure exists (pre-deck)
    legacy_cards = data_dir / 'cards.txt'
    legacy_state = data_dir / 'state.json'
    
    # Create directories
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / 'decks').mkdir(exist_ok=True)
    (data_dir.parent / 'backups').mkdir(exist_ok=True)
    
    # Initialize deck manager
    deck_manager = DeckManager(data_dir)
    
    # Check if default deck exists
    default_deck = data_dir / 'decks' / 'default'
    
    if default_deck.exists():
        print(f"Data directory already initialized at: {data_dir}")
        return
    
    # Create default deck
    if legacy_cards.exists() and legacy_state.exists():
        # Migration path
        print("Migrating legacy data structure...")
        
        default_deck.mkdir(parents=True)
        shutil.move(str(legacy_cards), str(default_deck / 'cards.txt'))
        shutil.move(str(legacy_state), str(default_deck / 'state.json'))
        
        # Ensure state has display_name
        from .utils import read_json
        state = read_json(default_deck / 'state.json', {})
        if 'display_name' not in state:
            state['display_name'] = 'Default'
            atomic_write_json(default_deck / 'state.json', state)
        
        deck_manager.set_active_deck('default')
        print("Migration complete!")
    else:
        # Fresh initialization
        deck_manager.create_deck('Default', set_active=True)
        print(f"Initialized data directory at: {data_dir}")
        print("Default deck created and activated.")
    
    print(f"\nData structure:")
    print(f"  {data_dir}/")
    print(f"    active_deck.txt")
    print(f"    decks/default/")
    print(f"    ../backups/")
    print(f"\nReady! Use 'anki-mini add' to add your first card.")
