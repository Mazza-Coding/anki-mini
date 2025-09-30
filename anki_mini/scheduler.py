"""SM-2 spaced repetition scheduler."""

from datetime import datetime, timedelta
from typing import Dict, Any, Literal

Grade = Literal[1, 2, 3, 4]  # Again, Hard, Good, Easy


class SM2Scheduler:
    """Simplified SM-2 scheduler with 4 grades."""
    
    # Grade multipliers
    AGAIN = 1  # Reset
    HARD_MULT = 0.85
    GOOD_MULT = 1.0
    EASY_MULT = 1.3
    
    # Initial values
    INITIAL_INTERVAL = 1
    INITIAL_EASE = 2.5
    MIN_EASE = 1.3
    
    @staticmethod
    def new_card() -> Dict[str, Any]:
        """Create new card state."""
        return {
            'interval': 0,
            'ease': SM2Scheduler.INITIAL_EASE,
            'due': datetime.now().strftime('%Y-%m-%d'),
            'reps': 0,
            'lapses': 0,
            'last_reviewed': None
        }
    
    @staticmethod
    def schedule(card: Dict[str, Any], grade: Grade) -> Dict[str, Any]:
        """Update card state based on grade."""
        card = card.copy()
        today = datetime.now().strftime('%Y-%m-%d')
        
        card['last_reviewed'] = today
        card['reps'] += 1
        
        if grade == 1:  # Again
            card['lapses'] += 1
            card['interval'] = 0
            card['due'] = today
        else:
            # Calculate new interval
            if card['interval'] == 0:
                # First review after new/lapse
                if grade == 2:  # Hard
                    interval_days = 1
                elif grade == 3:  # Good
                    interval_days = 1
                else:  # Easy
                    interval_days = 4
            else:
                # Subsequent reviews
                if grade == 2:  # Hard
                    interval_days = max(1, int(card['interval'] * SM2Scheduler.HARD_MULT))
                    card['ease'] = max(SM2Scheduler.MIN_EASE, card['ease'] - 0.15)
                elif grade == 3:  # Good
                    interval_days = max(1, int(card['interval'] * card['ease']))
                else:  # Easy
                    interval_days = max(1, int(card['interval'] * card['ease'] * SM2Scheduler.EASY_MULT))
                    card['ease'] += 0.15
            
            card['interval'] = interval_days
            due_date = datetime.now() + timedelta(days=interval_days)
            card['due'] = due_date.strftime('%Y-%m-%d')
        
        return card
    
    @staticmethod
    def is_due(card: Dict[str, Any]) -> bool:
        """Check if card is due for review."""
        today = datetime.now().strftime('%Y-%m-%d')
        return card['due'] <= today
    
    @staticmethod
    def suggest_grade(correct: bool, time_seconds: float) -> Grade:
        """Auto-suggest grade based on correctness and time."""
        if not correct:
            return 1  # Again
        
        # Time-based suggestion for correct answers
        if time_seconds < 3:
            return 4  # Easy
        elif time_seconds < 8:
            return 3  # Good
        else:
            return 2  # Hard
