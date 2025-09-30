"""Statistics and analytics for decks."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from .cards import CardManager
from .scheduler import SM2Scheduler
from .utils import read_json


class StatsCalculator:
    """Calculate deck statistics."""
    
    def __init__(self, deck_path: Path):
        self.deck_path = deck_path
        self.card_manager = CardManager(deck_path)
        self.state = read_json(deck_path / 'state.json', {})
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive deck stats."""
        all_cards = self.card_manager.get_all_cards()
        cards_state = self.state.get('cards', {})
        
        total = len(all_cards)
        new = 0
        learning = 0
        review = 0
        due_today = 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for card_id, _, _ in all_cards:
            if card_id not in cards_state:
                new += 1
                due_today += 1
            else:
                card = cards_state[card_id]
                if card['reps'] == 0:
                    new += 1
                elif card['interval'] < 21:
                    learning += 1
                else:
                    review += 1
                
                if SM2Scheduler.is_due(card):
                    due_today += 1
        
        # Calculate review accuracy for recent periods
        accuracy_7d = self._calculate_accuracy(days=7)
        accuracy_30d = self._calculate_accuracy(days=30)
        reviews_today = self._count_reviews_today()
        
        return {
            'total_cards': total,
            'new': new,
            'learning': learning,
            'review': review,
            'due_today': due_today,
            'reviews_today': reviews_today,
            'accuracy_7d': accuracy_7d,
            'accuracy_30d': accuracy_30d
        }
    
    def _calculate_accuracy(self, days: int) -> Optional[float]:
        """Calculate accuracy for last N days from review log."""
        log_file = self.deck_path / 'review_log.txt'
        if not log_file.exists():
            return None
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        total = 0
        correct = 0
        
        try:
            content = log_file.read_text(encoding='utf-8')
            for line in content.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 3:
                    date, grade_str = parts[0], parts[2]
                    if date >= cutoff:
                        total += 1
                        if int(grade_str) >= 3:  # Good or Easy
                            correct += 1
        except:
            return None
        
        return (correct / total * 100) if total > 0 else None
    
    def _count_reviews_today(self) -> int:
        """Count reviews done today."""
        today = datetime.now().strftime('%Y-%m-%d')
        cards_state = self.state.get('cards', {})
        
        count = 0
        for card in cards_state.values():
            if card.get('last_reviewed') == today:
                count += 1
        
        return count


def print_stats(stats: Dict[str, Any], deck_name: str) -> None:
    """Pretty-print deck statistics."""
    print(f"\n=== Stats for '{deck_name}' ===")
    print(f"Total cards: {stats['total_cards']}")
    print(f"  New: {stats['new']}")
    print(f"  Learning: {stats['learning']}")
    print(f"  Review: {stats['review']}")
    print(f"\nDue today: {stats['due_today']}")
    print(f"Reviews today: {stats['reviews_today']}")
    
    if stats['accuracy_7d'] is not None:
        print(f"\nAccuracy (7 days): {stats['accuracy_7d']:.1f}%")
    if stats['accuracy_30d'] is not None:
        print(f"Accuracy (30 days): {stats['accuracy_30d']:.1f}%")
    print()
