"""Interactive review session with recall by typing."""

import time
from pathlib import Path
from typing import Optional, List, Tuple
from collections import deque
from .cards import CardManager
from .scheduler import SM2Scheduler, Grade
from .utils import check_answer, read_json, deck_lock


class ReviewSession:
    """Manages interactive review session with learning queue."""
    
    def __init__(self, deck_path: Path, lenient_threshold: int = 2):
        self.deck_path = deck_path
        self.card_manager = CardManager(deck_path)
        self.lenient_threshold = lenient_threshold
        self.session_stats = {
            'reviewed': 0,
            'correct': 0,
            'incorrect': 0,
            'learning': 0,  # Cards in learning phase
            'graduated': 0  # Cards that graduated
        }
        self.immediate_queue: deque = deque()  # Cards marked "Again" - show immediately
        self.delayed_queue: deque = deque()  # Cards marked "Hard" - show after others
    
    def run(self) -> None:
        """Run interactive review session with learning queue."""
        due_cards = self.card_manager.get_due_cards()
        
        if not due_cards:
            print("No cards due for review!")
            return
        
        print(f"\n{len(due_cards)} card(s) due for review\n")
        print("Controls: [Tab] reveal answer, [Esc] exit, [1-4] grade")
        print("Grades: 1=Again, 2=Hard, 3=Good, 4=Easy")
        print("\nℹ️  'Again' shows immediately, 'Hard' shows after other cards\n")
        
        # Initialize main queue with due cards
        main_queue = deque(due_cards)
        cards_seen = set()  # Track unique cards reviewed
        total_reviews = 0  # Total number of times cards were shown
        
        while main_queue or self.immediate_queue or self.delayed_queue:
            # Priority: immediate queue > main queue > delayed queue
            if self.immediate_queue:
                card_id, front, back = self.immediate_queue.popleft()
                queue_type = "Again"
            elif main_queue:
                card_id, front, back = main_queue.popleft()
                queue_type = "New" if card_id not in cards_seen else "Review"
            elif self.delayed_queue:
                card_id, front, back = self.delayed_queue.popleft()
                queue_type = "Learning"
            else:
                break
            
            cards_seen.add(card_id)
            total_reviews += 1
            
            # Get current card state
            state = read_json(self.deck_path / 'state.json', {})
            card_state = state.get('cards', {}).get(card_id, SM2Scheduler.new_card())
            
            # Show card info
            learning_status = SM2Scheduler.get_learning_step_name(card_state)
            print(f"--- Card {total_reviews} [{learning_status}] ---")
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
            new_state = SM2Scheduler.schedule(card_state, grade)
            
            # Check if card needs to be re-queued in this session
            if new_state.get('needs_requeue', False):
                requeue_type = new_state.get('requeue_type', 'delayed')
                
                if requeue_type == 'immediate':
                    self.immediate_queue.append((card_id, front, back))
                    self.session_stats['learning'] += 1
                    print("↻ Card will be shown again immediately")
                else:  # delayed
                    self.delayed_queue.append((card_id, front, back))
                    self.session_stats['learning'] += 1
                    print("↻ Card will be shown again after other cards")
            else:
                if SM2Scheduler.is_learning(card_state) and not SM2Scheduler.is_learning(new_state):
                    self.session_stats['graduated'] += 1
                    print("🎓 Card graduated from learning!")
            
            # Remove temporary flags before saving
            new_state.pop('needs_requeue', None)
            new_state.pop('requeue_type', None)
            self.card_manager.update_card_state(card_id, new_state)
            self.session_stats['reviewed'] += 1
            
            print()  # Blank line between cards
        
        # Session summary
        print("\n=== Session Complete ===")
        print(f"Unique cards reviewed: {len(cards_seen)}")
        print(f"Total reviews: {total_reviews}")
        if self.session_stats['reviewed'] > 0:
            accuracy = (self.session_stats['correct'] / self.session_stats['reviewed']) * 100
            print(f"Accuracy: {accuracy:.1f}%")
            print(f"Correct: {self.session_stats['correct']}, Incorrect: {self.session_stats['incorrect']}")
        if self.session_stats['graduated'] > 0:
            print(f"Cards graduated: {self.session_stats['graduated']}")
        
        # Show remaining cards in queues
        remaining = len(self.immediate_queue) + len(self.delayed_queue)
        if remaining > 0:
            print(f"\nℹ️  {remaining} card(s) still in learning (will appear in next session)")


def start_review(deck_path: Path, lenient_threshold: int = 2) -> None:
    """Start review session for a deck with learning queue support."""
    session = ReviewSession(deck_path, lenient_threshold)
    session.run()
