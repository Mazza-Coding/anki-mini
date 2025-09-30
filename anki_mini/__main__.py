"""Entry point for python -m anki_mini."""

import sys

# Use absolute import for PyInstaller compatibility
if __name__ == '__main__':
    from anki_mini.cli import main
    sys.exit(main())
