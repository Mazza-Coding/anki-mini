"""Tests for SM-2 scheduler."""

import pytest
from datetime import datetime, timedelta
from anki_mini.scheduler import SM2Scheduler


def test_new_card():
    """Test new card initialization."""
    card = SM2Scheduler.new_card()
    
    assert card['interval'] == 0
    assert card['ease'] == 2.5
    assert card['reps'] == 0
    assert card['lapses'] == 0
    assert card['last_reviewed'] is None


def test_schedule_again():
    """Test Again grade resets interval."""
    card = SM2Scheduler.new_card()
    card['interval'] = 10
    card['ease'] = 2.5
    
    updated = SM2Scheduler.schedule(card, 1)  # Again
    
    assert updated['interval'] == 0
    assert updated['lapses'] == 1
    assert updated['due'] == datetime.now().strftime('%Y-%m-%d')


def test_schedule_good_first_time():
    """Test Good grade on first review."""
    card = SM2Scheduler.new_card()
    
    updated = SM2Scheduler.schedule(card, 3)  # Good
    
    assert updated['interval'] == 1
    assert updated['reps'] == 1
    assert updated['lapses'] == 0


def test_schedule_easy_first_time():
    """Test Easy grade on first review."""
    card = SM2Scheduler.new_card()
    
    updated = SM2Scheduler.schedule(card, 4)  # Easy
    
    assert updated['interval'] == 4
    assert updated['reps'] == 1


def test_schedule_progression():
    """Test interval progression with Good grades."""
    card = SM2Scheduler.new_card()
    
    # First review: Good
    card = SM2Scheduler.schedule(card, 3)
    assert card['interval'] == 1
    
    # Second review: Good
    card = SM2Scheduler.schedule(card, 3)
    assert card['interval'] >= 2  # Should increase
    
    # Third review: Good
    card = SM2Scheduler.schedule(card, 3)
    assert card['interval'] >= 4


def test_schedule_hard_reduces_ease():
    """Test Hard grade reduces ease factor."""
    card = SM2Scheduler.new_card()
    initial_ease = card['ease']
    
    card = SM2Scheduler.schedule(card, 3)  # Good first
    card = SM2Scheduler.schedule(card, 2)  # Hard
    
    assert card['ease'] < initial_ease


def test_schedule_easy_increases_ease():
    """Test Easy grade increases ease factor."""
    card = SM2Scheduler.new_card()
    
    card = SM2Scheduler.schedule(card, 3)  # Good first
    initial_ease = card['ease']
    card = SM2Scheduler.schedule(card, 4)  # Easy
    
    assert card['ease'] > initial_ease


def test_is_due():
    """Test due date checking."""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    card_due_today = {'due': today}
    card_due_yesterday = {'due': yesterday}
    card_due_tomorrow = {'due': tomorrow}
    
    assert SM2Scheduler.is_due(card_due_today)
    assert SM2Scheduler.is_due(card_due_yesterday)
    assert not SM2Scheduler.is_due(card_due_tomorrow)


def test_suggest_grade():
    """Test grade suggestion logic."""
    # Incorrect answer
    assert SM2Scheduler.suggest_grade(False, 5.0) == 1
    
    # Correct, fast
    assert SM2Scheduler.suggest_grade(True, 2.0) == 4
    
    # Correct, moderate
    assert SM2Scheduler.suggest_grade(True, 5.0) == 3
    
    # Correct, slow
    assert SM2Scheduler.suggest_grade(True, 10.0) == 2


def test_learning_steps_new_card():
    """Test learning steps for new cards."""
    card = SM2Scheduler.new_card()
    
    # New card should be in learning
    assert SM2Scheduler.is_learning(card)
    assert card['learning_step'] == 0
    
    # Mark as Hard - should stay in learning and requeue with delay
    updated = SM2Scheduler.schedule(card, 2)
    assert updated['needs_requeue'] is True
    assert updated['requeue_type'] == 'delayed'
    assert SM2Scheduler.is_learning(updated)
    assert updated['learning_step'] == 0
    
    # Mark as Good - should advance to next learning step with delay
    updated = SM2Scheduler.schedule(card, 3)
    assert updated['needs_requeue'] is True
    assert updated['requeue_type'] == 'delayed'
    assert SM2Scheduler.is_learning(updated)
    assert updated['learning_step'] == 1


def test_learning_graduation():
    """Test card graduation from learning."""
    card = SM2Scheduler.new_card()
    
    # First Good - advance to step 1
    card = SM2Scheduler.schedule(card, 3)
    assert card['learning_step'] == 1
    assert card['needs_requeue'] is True
    
    # Second Good - should graduate
    card.pop('needs_requeue', None)
    card = SM2Scheduler.schedule(card, 3)
    assert card['needs_requeue'] is False
    assert not SM2Scheduler.is_learning(card)
    assert card['interval'] == 1
    assert card['learning_step'] == 0


def test_learning_easy_graduation():
    """Test immediate graduation with Easy."""
    card = SM2Scheduler.new_card()
    
    # Easy on new card - should graduate immediately
    updated = SM2Scheduler.schedule(card, 4)
    assert updated['needs_requeue'] is False
    assert not SM2Scheduler.is_learning(updated)
    assert updated['interval'] == 4


def test_learning_again_resets():
    """Test Again resets learning progress."""
    card = SM2Scheduler.new_card()
    
    # Advance to step 1
    card = SM2Scheduler.schedule(card, 3)
    card.pop('needs_requeue', None)
    card.pop('requeue_type', None)
    assert card['learning_step'] == 1
    
    # Mark as Again - should reset to step 0 with immediate requeue
    updated = SM2Scheduler.schedule(card, 1)
    assert updated['needs_requeue'] is True
    assert updated['requeue_type'] == 'immediate'
    assert updated['learning_step'] == 0
    assert updated['lapses'] == 1


def test_review_card_again_returns_to_learning():
    """Test that review cards marked Again return to learning."""
    card = SM2Scheduler.new_card()
    
    # Graduate the card
    card = SM2Scheduler.schedule(card, 3)
    card.pop('needs_requeue', None)
    card.pop('requeue_type', None)
    card = SM2Scheduler.schedule(card, 3)
    card.pop('needs_requeue', None)
    card.pop('requeue_type', None)
    
    assert not SM2Scheduler.is_learning(card)
    assert card['interval'] > 0
    
    # Mark as Again - should return to learning with immediate requeue
    updated = SM2Scheduler.schedule(card, 1)
    assert updated['needs_requeue'] is True
    assert updated['requeue_type'] == 'immediate'
    assert SM2Scheduler.is_learning(updated)
    assert updated['interval'] == 0
    assert updated['learning_step'] == 0


def test_get_learning_step_name():
    """Test learning step name display."""
    card = SM2Scheduler.new_card()
    
    # New card at step 0
    assert "Learning (1m)" in SM2Scheduler.get_learning_step_name(card)
    
    # Advance to step 1
    card['learning_step'] = 1
    assert "Learning (10m)" in SM2Scheduler.get_learning_step_name(card)
    
    # Graduated card
    card['interval'] = 1
    assert SM2Scheduler.get_learning_step_name(card) == "Review"


def test_requeue_types():
    """Test that Again uses immediate requeue and Hard uses delayed."""
    card = SM2Scheduler.new_card()
    
    # Again should be immediate
    updated_again = SM2Scheduler.schedule(card, 1)
    assert updated_again['requeue_type'] == 'immediate'
    
    # Hard should be delayed
    updated_hard = SM2Scheduler.schedule(card, 2)
    assert updated_hard['requeue_type'] == 'delayed'
    
    # Good should be delayed (still in learning)
    updated_good = SM2Scheduler.schedule(card, 3)
    assert updated_good['requeue_type'] == 'delayed'
