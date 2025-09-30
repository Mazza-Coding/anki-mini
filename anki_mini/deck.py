"""Deck management: create, list, select, rename, delete."""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from .utils import sanitize_deck_name, atomic_write, read_json, atomic_write_json, get_data_dir


class DeckManager:
    """Manages multiple decks."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.decks_dir = data_dir / 'decks'
        self.active_deck_file = data_dir / 'active_deck.txt'
    
    def get_active_deck(self) -> str:
        """Get current active deck slug."""
        if not self.active_deck_file.exists():
            return 'default'
        return self.active_deck_file.read_text(encoding='utf-8').strip()
    
    def set_active_deck(self, deck_name: str) -> None:
        """Set active deck by name or slug."""
        slug = self._resolve_deck(deck_name)
        atomic_write(self.active_deck_file, slug)
    
    def list_decks(self) -> List[Dict[str, Any]]:
        """List all decks with metadata."""
        if not self.decks_dir.exists():
            return []
        
        active = self.get_active_deck()
        decks = []
        
        for deck_dir in self.decks_dir.iterdir():
            if deck_dir.is_dir():
                state = read_json(deck_dir / 'state.json', {})
                display_name = state.get('display_name', deck_dir.name)
                card_count = self._count_cards(deck_dir)
                
                decks.append({
                    'slug': deck_dir.name,
                    'display_name': display_name,
                    'card_count': card_count,
                    'is_active': deck_dir.name == active
                })
        
        return sorted(decks, key=lambda d: d['display_name'].lower())
    
    def create_deck(self, name: str, set_active: bool = False) -> str:
        """Create new deck; return slug."""
        slug = sanitize_deck_name(name)
        deck_dir = self.decks_dir / slug
        
        if deck_dir.exists():
            raise ValueError(f"Deck already exists: {name}")
        
        # Create deck structure
        deck_dir.mkdir(parents=True, exist_ok=True)
        (deck_dir / 'cards.txt').touch()
        
        # Initialize state with display name
        state = {
            'display_name': name,
            'cards': {},
            'next_id': 1
        }
        atomic_write_json(deck_dir / 'state.json', state)
        
        if set_active:
            self.set_active_deck(slug)
        
        return slug
    
    def rename_deck(self, old_name: str, new_name: str) -> None:
        """Rename deck (folder and metadata)."""
        old_slug = self._resolve_deck(old_name)
        new_slug = sanitize_deck_name(new_name)
        
        old_dir = self.decks_dir / old_slug
        new_dir = self.decks_dir / new_slug
        
        if not old_dir.exists():
            raise ValueError(f"Deck not found: {old_name}")
        if new_dir.exists() and new_dir != old_dir:
            raise ValueError(f"Deck already exists: {new_name}")
        
        # Update display name in state
        state = read_json(old_dir / 'state.json', {})
        state['display_name'] = new_name
        atomic_write_json(old_dir / 'state.json', state)
        
        # Rename folder if slug changed
        if old_slug != new_slug:
            old_dir.rename(new_dir)
            
            # Update active deck if needed
            if self.get_active_deck() == old_slug:
                self.set_active_deck(new_slug)
    
    def delete_deck(self, name: str, force: bool = False, backup: bool = False) -> None:
        """Delete deck; refuse if not empty unless force."""
        slug = self._resolve_deck(name)
        deck_dir = self.decks_dir / slug
        
        if not deck_dir.exists():
            raise ValueError(f"Deck not found: {name}")
        
        # Check if empty
        if not force and self._count_cards(deck_dir) > 0:
            raise ValueError(f"Deck not empty. Use --force to delete anyway.")
        
        # Backup if requested
        if backup:
            self._backup_deck(deck_dir)
        
        # Delete deck
        shutil.rmtree(deck_dir)
        
        # If was active, switch to first available or create default
        if self.get_active_deck() == slug:
            remaining = self.list_decks()
            if remaining:
                self.set_active_deck(remaining[0]['slug'])
            else:
                # Create default deck
                self.create_deck('Default', set_active=True)
    
    def get_deck_path(self, deck_name: Optional[str] = None) -> Path:
        """Get path to deck directory; use active if not specified."""
        if deck_name is None:
            slug = self.get_active_deck()
        else:
            slug = self._resolve_deck(deck_name)
        
        deck_path = self.decks_dir / slug
        if not deck_path.exists():
            raise ValueError(f"Deck not found: {deck_name or slug}")
        
        return deck_path
    
    def _resolve_deck(self, name: str) -> str:
        """Resolve deck name or slug to slug."""
        # First try as slug
        slug = sanitize_deck_name(name)
        if (self.decks_dir / slug).exists():
            return slug
        
        # Try to find by display name
        for deck in self.list_decks():
            if deck['display_name'].lower() == name.lower():
                return deck['slug']
        
        # Not found, return sanitized version (may not exist)
        return slug
    
    def _count_cards(self, deck_dir: Path) -> int:
        """Count cards in deck."""
        cards_file = deck_dir / 'cards.txt'
        if not cards_file.exists():
            return 0
        
        content = cards_file.read_text(encoding='utf-8').strip()
        return len([line for line in content.split('\n') if line.strip()])
    
    def _backup_deck(self, deck_dir: Path) -> None:
        """Backup deck to zip file."""
        from datetime import datetime
        import zipfile
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.data_dir.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"{timestamp}-{deck_dir.name}.zip"
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in deck_dir.rglob('*'):
                if file.is_file() and file.name != '.lock':
                    zf.write(file, file.relative_to(deck_dir))
        
        print(f"Backup created: {backup_file}")
