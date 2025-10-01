"""SM-2 spaced repetition scheduler with learning steps."""

from datetime import datetime, timedelta
from typing import Dict, Any, Literal

Grade = Literal[1, 2, 3, 4]  # Again, Hard, Good, Easy


class SM2Scheduler:
    """Simplified SM-2 scheduler with 4 grades and learning steps."""
    
    # Grade multipliers
    AGAIN = 1  # Reset
    HARD_MULT = 0.85
    GOOD_MULT = 1.0
    EASY_MULT = 1.3
    
    # Initial values
    INITIAL_INTERVAL = 1
    INITIAL_EASE = 2.5
    MIN_EASE = 1.3
    
    # Learning steps (in minutes for intra-session review)
    # Cards progress through these steps before graduating
    LEARNING_STEPS = [1, 10]  # 1 minute, then 10 minutes
    
    @staticmethod
    def new_card() -> Dict[str, Any]:
        """Create new card state."""
        return {
            'interval': 0,
            'ease': SM2Scheduler.INITIAL_EASE,
            'due': datetime.now().strftime('%Y-%m-%d'),
            'reps': 0,
            'lapses': 0,
            'last_reviewed': None,
            'learning_step': 0  # Current position in learning steps
        }
    
    @staticmethod
    def schedule(card: Dict[str, Any], grade: Grade) -> Dict[str, Any]:
        """Update card state based on grade.
        
        Returns updated card state with 'needs_requeue' flag if card should
        be shown again in the same session. The 'requeue_type' indicates:
        - 'immediate': Show again right away (for 'Again')
        - 'delayed': Show again after some other cards (for 'Hard' in learning)
        """
        card = card.copy()
        today = datetime.now().strftime('%Y-%m-%d')
        
        card['last_reviewed'] = today
        card['reps'] += 1
        
        # Ensure learning_step exists (for backward compatibility)
        if 'learning_step' not in card:
            card['learning_step'] = 0
        
        # Check if card is in learning phase (interval == 0)
        is_learning = card['interval'] == 0
        
        if grade == 1:  # Again
            card['lapses'] += 1
            card['interval'] = 0
            card['learning_step'] = 0  # Reset to first learning step
            card['due'] = today
            card['needs_requeue'] = True
            card['requeue_type'] = 'immediate'  # Show again immediately
        elif is_learning:
            # Card is in learning phase
            if grade == 2:  # Hard - stay at current learning step
                card['needs_requeue'] = True
                card['requeue_type'] = 'delayed'  # Show after other cards
            elif grade == 3:  # Good - advance to next learning step
                card['learning_step'] += 1
                if card['learning_step'] >= len(SM2Scheduler.LEARNING_STEPS):
                    # Graduate from learning
                    card['interval'] = 1
                    card['learning_step'] = 0
                    due_date = datetime.now() + timedelta(days=1)
                    card['due'] = due_date.strftime('%Y-%m-%d')
                    card['needs_requeue'] = False
                else:
                    # Still in learning, show again
                    card['needs_requeue'] = True
                    card['requeue_type'] = 'delayed'  # Show after other cards
            else:  # Easy - graduate immediately with longer interval
                card['interval'] = 4
                card['learning_step'] = 0
                due_date = datetime.now() + timedelta(days=4)
                card['due'] = due_date.strftime('%Y-%m-%d')
                card['needs_requeue'] = False
        else:
            # Card is in review phase (interval > 0)
            if grade == 2:  # Hard
                interval_days = max(1, int(card['interval'] * SM2Scheduler.HARD_MULT))
                card['ease'] = max(SM2Scheduler.MIN_EASE, card['ease'] - 0.15)
                card['interval'] = interval_days
                due_date = datetime.now() + timedelta(days=interval_days)
                card['due'] = due_date.strftime('%Y-%m-%d')
                card['needs_requeue'] = False
            elif grade == 3:  # Good
                interval_days = max(1, int(card['interval'] * card['ease']))
                card['interval'] = interval_days
                due_date = datetime.now() + timedelta(days=interval_days)
                card['due'] = due_date.strftime('%Y-%m-%d')
                card['needs_requeue'] = False
            else:  # Easy
                interval_days = max(1, int(card['interval'] * card['ease'] * SM2Scheduler.EASY_MULT))
                card['ease'] += 0.15
                card['interval'] = interval_days
                due_date = datetime.now() + timedelta(days=interval_days)
                card['due'] = due_date.strftime('%Y-%m-%d')
                card['needs_requeue'] = False
        
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
    
    @staticmethod
    def is_learning(card: Dict[str, Any]) -> bool:
        """Check if card is in learning phase."""
        return card.get('interval', 0) == 0
    
    @staticmethod
    def get_learning_step_name(card: Dict[str, Any]) -> str:
        """Get human-readable learning step."""
        if not SM2Scheduler.is_learning(card):
            return "Review"
        
        step = card.get('learning_step', 0)
        if step >= len(SM2Scheduler.LEARNING_STEPS):
            return "Graduating"
        
        minutes = SM2Scheduler.LEARNING_STEPS[step]
        if minutes < 60:
            return f"Learning ({minutes}m)"
        else:
            hours = minutes / 60
            return f"Learning ({hours:.0f}h)"
