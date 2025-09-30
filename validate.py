"""Validation script to test anki-mini functionality."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run command and return result."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    return result.returncode, result.stdout, result.stderr

def test_basic_commands():
    """Test basic CLI commands."""
    print("=" * 60)
    print("ANKI-MINI VALIDATION TEST")
    print("=" * 60)
    
    tests = [
        ("Version check", "python -m anki_mini --version"),
        ("Help command", "python -m anki_mini --help"),
        ("Deck list", "python -m anki_mini deck list"),
        ("Stats", "python -m anki_mini stats"),
    ]
    
    passed = 0
    failed = 0
    
    for name, cmd in tests:
        print(f"\n[TEST] {name}")
        print(f"  Command: {cmd}")
        
        code, stdout, stderr = run_command(cmd)
        
        if code == 0:
            print(f"  ✅ PASSED")
            if stdout.strip():
                print(f"  Output: {stdout.strip()[:100]}...")
            passed += 1
        else:
            print(f"  ❌ FAILED (exit code: {code})")
            if stderr:
                print(f"  Error: {stderr.strip()[:200]}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = test_basic_commands()
    sys.exit(0 if success else 1)
