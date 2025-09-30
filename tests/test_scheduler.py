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
