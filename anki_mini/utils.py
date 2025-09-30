"""Core utilities for file operations, locking, and path handling."""

import os
import sys
import json
import msvcrt
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager


def get_data_dir(override: Optional[str] = None) -> Path:
    """Get base data directory. Default is folder of executable."""
    if override:
        return Path(override).resolve()
    
    # If running as PyInstaller bundle, use executable directory
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'data'
    # Otherwise use current working directory (for dev)
    return Path.cwd() / 'data'


def sanitize_deck_name(name: str) -> str:
    """Convert deck name to safe slug: lowercase, spaces→-, alnum + - only."""
    slug = name.lower().strip()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    return slug or 'default'


def stable_card_id(front: str, back: str) -> str:
    """Generate stable hash-based card ID from front+back."""
    content = f"{front}\t{back}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def atomic_write(path: Path, content: str) -> None:
    """Atomic write: tmp→flush+fsync→rename."""
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    tmp_path.replace(path)


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Atomic JSON write."""
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))


def read_json(path: Path, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """Read JSON file; return default if not exists."""
    if not path.exists():
        return default or {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@contextmanager
def deck_lock(deck_path: Path):
    """Acquire exclusive lock for deck using Windows file locking."""
    lock_file = deck_path / '.lock'
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Open/create lock file
    fd = os.open(str(lock_file), os.O_RDWR | os.O_CREAT)
    
    try:
        # Try to acquire exclusive lock (non-blocking)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            os.close(fd)
            raise RuntimeError(f"Deck is locked by another process: {deck_path.name}")
        
        yield
        
    finally:
        # Release lock and close
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except:
            pass
        os.close(fd)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Damerau-Levenshtein distance for fuzzy matching."""
    len1, len2 = len(s1), len(s2)
    
    # Create distance matrix
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
            
            # Damerau: transposition
            if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                matrix[i][j] = min(matrix[i][j], matrix[i-2][j-2] + cost)
    
    return matrix[len1][len2]


def check_answer(user_answer: str, expected: str, threshold: int = 2) -> tuple[bool, str]:
    """
    Check answer with exact and lenient matching.
    Returns (is_correct, match_type).
    Supports multiple answers separated by ; in expected.
    """
    user_clean = user_answer.strip().lower()
    
    # Support multiple acceptable answers
    expected_answers = [ans.strip().lower() for ans in expected.split(';')]
    
    # Check exact match first
    for exp in expected_answers:
        if user_clean == exp:
            return True, 'exact'
    
    # Check lenient match
    for exp in expected_answers:
        distance = levenshtein_distance(user_clean, exp)
        if distance <= threshold:
            return True, 'lenient'
    
    return False, 'mismatch'
