"""Interactive review session with recall by typing."""

import time
from pathlib import Path
from typing import Optional
from .cards import CardManager
from .scheduler import SM2Scheduler, Grade
from .utils import check_answer, read_json, deck_lock


class ReviewSession:
    """Manages interactive review session."""
    
    def __init__(self, deck_path: Path, lenient_threshold: int = 2):
        self.deck_path = deck_path
        self.card_manager = CardManager(deck_path)
        self.lenient_threshold = lenient_threshold
        self.session_stats = {
            'reviewed': 0,
            'correct': 0,
            'incorrect': 0
        }
    
    def run(self) -> None:
        """Run interactive review session."""
        due_cards = self.card_manager.get_due_cards()
        
        if not due_cards:
            print("No cards due for review!")
            return
        
        print(f"\n{len(due_cards)} card(s) due for review\n")
        print("Controls: [Tab] reveal answer, [Esc] exit, [1-4] grade")
        print("Grades: 1=Again, 2=Hard, 3=Good, 4=Easy\n")
        
        for i, (card_id, front, back) in enumerate(due_cards, 1):
            print(f"--- Card {i}/{len(due_cards)} ---")
            print(f"Front: {front}")
            
            # Start timer
            start_time = time.perf_counter()
            
            try:
                user_answer = input("Your answer: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nReview session ended.")
                break
            
            # Check for reveal (Tab would be typed as empty or special handling)
            if user_answer.lower() in ['tab', '\\t', '']:
                print(f"Expected: {back}")
                print("Counted as: Again")
                grade = 1
                elapsed = 0
                correct = False
            else:
                elapsed = time.perf_counter() - start_time
                
                # Check answer
                correct, match_type = check_answer(user_answer, back, self.lenient_threshold)
                
                if correct:
                    print(f"✅ Correct ({match_type})")
                    self.session_stats['correct'] += 1
                else:
                    print(f"❌ Incorrect")
                    print(f"Expected: {back}")
                    print(f"Your answer: {user_answer}")
                    self.session_stats['incorrect'] += 1
                
                # Suggest grade
                suggested = SM2Scheduler.suggest_grade(correct, elapsed)
                grade_names = {1: 'Again', 2: 'Hard', 3: 'Good', 4: 'Easy'}
                
                print(f"\nSuggested: [{suggested}] {grade_names[suggested]}")
                grade_input = input("Grade [1-4, Enter=suggested]: ").strip()
                
                if not grade_input:
                    grade = suggested
                else:
                    try:
                        grade = int(grade_input)
                        if grade not in [1, 2, 3, 4]:
                            grade = suggested
                    except ValueError:
                        grade = suggested
            
            # Update card state
            state = read_json(self.deck_path / 'state.json', {})
            card_state = state.get('cards', {}).get(card_id, SM2Scheduler.new_card())
            new_state = SM2Scheduler.schedule(card_state, grade)
            
            self.card_manager.update_card_state(card_id, new_state)
            self.session_stats['reviewed'] += 1
            
            print()  # Blank line between cards
        
        # Session summary
        print("\n=== Session Complete ===")
        print(f"Cards reviewed: {self.session_stats['reviewed']}")
        if self.session_stats['reviewed'] > 0:
            accuracy = (self.session_stats['correct'] / self.session_stats['reviewed']) * 100
            print(f"Accuracy: {accuracy:.1f}%")
            print(f"Correct: {self.session_stats['correct']}, Incorrect: {self.session_stats['incorrect']}")


def start_review(deck_path: Path, lenient_threshold: int = 2) -> None:
    """Start review session for a deck."""
    session = ReviewSession(deck_path, lenient_threshold)
    session.run()
