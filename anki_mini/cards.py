"""Card operations: add, import, export."""

from pathlib import Path
from typing import List, Tuple, Optional
from .utils import stable_card_id, atomic_write, read_json, atomic_write_json, deck_lock
from .scheduler import SM2Scheduler


class CardManager:
    """Manages cards within a deck."""
    
    def __init__(self, deck_path: Path):
        self.deck_path = deck_path
        self.cards_file = deck_path / 'cards.txt'
        self.state_file = deck_path / 'state.json'
    
    def add_card(self, front: str, back: str) -> bool:
        """Add card to deck. Returns True if added, False if duplicate."""
        front = front.strip()
        back = back.strip()
        
        if not front or not back:
            raise ValueError("Front and back cannot be empty")
        
        with deck_lock(self.deck_path):
            # Check for duplicate
            if self._is_duplicate(front, back):
                return False
            
            # Append to cards.txt
            line = f"{front}\t{back}\n"
            with open(self.cards_file, 'a', encoding='utf-8') as f:
                f.write(line)
            
            # Add to state
            state = read_json(self.state_file, {})
            if 'cards' not in state:
                state['cards'] = {}
            
            card_id = stable_card_id(front, back)
            state['cards'][card_id] = SM2Scheduler.new_card()
            
            atomic_write_json(self.state_file, state)
        
        return True
    
    def get_all_cards(self) -> List[Tuple[str, str, str]]:
        """Get all cards as (id, front, back) tuples."""
        if not self.cards_file.exists():
            return []
        
        cards = []
        content = self.cards_file.read_text(encoding='utf-8')
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('\t', 1)
            if len(parts) == 2:
                front, back = parts
                card_id = stable_card_id(front, back)
                cards.append((card_id, front, back))
        
        return cards
    
    def get_due_cards(self) -> List[Tuple[str, str, str]]:
        """Get cards due for review."""
        state = read_json(self.state_file, {})
        cards_state = state.get('cards', {})
        
        all_cards = self.get_all_cards()
        due_cards = []
        
        for card_id, front, back in all_cards:
            if card_id in cards_state:
                card_state = cards_state[card_id]
                if SM2Scheduler.is_due(card_state):
                    due_cards.append((card_id, front, back))
            else:
                # New card with no state
                due_cards.append((card_id, front, back))
        
        return due_cards
    
    def get_all_cards_by_difficulty(self) -> List[Tuple[str, str, str]]:
        """Get all cards sorted by difficulty (hardest first).
        
        Difficulty is based on:
        1. Cards with lapses (more lapses = harder)
        2. Cards with lower ease factor
        3. Cards with more reviews but lower ease
        """
        state = read_json(self.state_file, {})
        cards_state = state.get('cards', {})
        
        all_cards = self.get_all_cards()
        
        # Create list with difficulty scores
        cards_with_difficulty = []
        for card_id, front, back in all_cards:
            if card_id in cards_state:
                card_state = cards_state[card_id]
                # Calculate difficulty score (higher = harder)
                # Factors: lapses (most important), low ease, high reps with low ease
                lapses = card_state.get('lapses', 0)
                ease = card_state.get('ease', 2.5)
                reps = card_state.get('reps', 0)
                
                # Difficulty score: lapses are most important, then inverted ease
                # Cards with more lapses and lower ease are harder
                difficulty = (lapses * 10) + (2.5 - ease) * 5 + (reps * 0.1 if ease < 2.3 else 0)
            else:
                # New cards have medium difficulty
                difficulty = 1.0
            
            cards_with_difficulty.append((difficulty, card_id, front, back))
        
        # Sort by difficulty (highest first = hardest first)
        cards_with_difficulty.sort(key=lambda x: x[0], reverse=True)
        
        # Return without difficulty score
        return [(card_id, front, back) for _, card_id, front, back in cards_with_difficulty]
    
    def update_card_state(self, card_id: str, new_state: dict) -> None:
        """Update state for a specific card."""
        with deck_lock(self.deck_path):
            state = read_json(self.state_file, {})
            if 'cards' not in state:
                state['cards'] = {}
            
            state['cards'][card_id] = new_state
            atomic_write_json(self.state_file, state)
    
    def import_cards(self, source_file: Path) -> Tuple[int, int]:
        """Import cards from txt file. Returns (added, skipped)."""
        if not source_file.exists():
            raise FileNotFoundError(f"File not found: {source_file}")
        
        content = source_file.read_text(encoding='utf-8')
        added = 0
        skipped = 0
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue
            
            front, back = parts[0].strip(), parts[1].strip()
            if front and back:
                if self.add_card(front, back):
                    added += 1
                else:
                    skipped += 1
        
        return added, skipped
    
    def export_cards(self, dest_file: Path) -> int:
        """Export all cards to txt file. Returns count."""
        cards = self.get_all_cards()
        
        lines = [f"{front}\t{back}\n" for _, front, back in cards]
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(dest_file, ''.join(lines))
        
        return len(cards)
    
    def _is_duplicate(self, front: str, back: str) -> bool:
        """Check if exact card already exists."""
        card_id = stable_card_id(front, back)
        existing_ids = [cid for cid, _, _ in self.get_all_cards()]
        return card_id in existing_ids
