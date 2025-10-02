# anki-mini

**Interactive CLI flashcard application with spaced repetition for Windows**

anki-mini is a lightweight, portable app with an interactive shell interface. Features multi-deck support, recall-by-typing reviews, and SM-2 spaced repetition scheduling—all using Python's standard library.

## Features

- 🎯 **Interactive Shell**: Persistent CLI interface
- 📦 **Portable**: Single `.exe` file with data stored
- 📚 **Multi-deck**: Create, manage, and switch between multiple decks
- ⌨️ **Recall by typing**: Test yourself by typing answers
- 🧠 **Smart scheduling**: SM-2 algorithm with 4 grades (Again, Hard, Good, Easy)
- ✏️ **Full CRUD**: Add, edit, delete, import/export cards and decks
- 🔒 **Data safety**: Atomic writes, file locking, optional backups
- ⚡ **Fast & minimal**: Standard library only, optimized for quick startup

## Quick Start

### Option 1: Run the Executable (Recommended)

1. **Download** `anki-mini.exe` or build it yourself (see below)
2. **Run** the executable:
   ```powershell
   .\anki-mini.exe
   ```
3. **Start learning!** The interactive shell will open automatically

### Option 2: Run from Python Source

```powershell
# Clone or download the repository
git clone https://github.com/yourusername/anki-mini.git
cd anki-mini

# Create and activate virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# Run directly with Python (no dependencies needed)
python -m anki_mini
```

### Option 3: Build Your Own Executable

```powershell
# Clone repository
git clone https://github.com/yourusername/anki-mini.git
cd anki-mini

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Build the executable
pyinstaller build.spec

# Find it in dist/anki-mini.exe
cd dist
.\anki-mini.exe
```

## Interactive Shell Usage

When you run `anki-mini.exe` (or `python -m anki_mini`), you enter an interactive shell:

```
============================================================
  anki-mini v1.0.0 - Interactive Shell
============================================================

Type 'help' for available commands or 'exit' to quit.

Active deck: Default

[Default]>
```

### Available Commands

Type `help` in the shell to see all commands:

#### Deck Management

- `decks` - List all decks
- `deck <name>` - Switch to a deck
- `new <name>` - Create new deck
- `rename <new_name>` - Rename active deck
- `deldeck [name]` - Delete deck (with confirmation)

#### Card Operations

- `add` - Add new card interactively
- `list` - List all cards in active deck
- `edit <number>` - Edit card by number from list
- `delete <number>` - Delete card by number from list
- `import [file]` - Import cards from file (opens file picker if no path)
- `export [file]` - Export cards to file (opens save dialog if no path)

#### Study

- `review` or `r` - Start review session
- `stats` or `s` - Show statistics

#### Data Migration

- `export-data [file]` - Export complete app data for device migration
- `import-data [file]` - Import complete app data from backup

#### Other

- `clear` - Clear screen
- `help` or `?` - Show help
- `exit`, `quit`, or `q` - Exit shell

### Example Session

````
[Default]> add
Add new card (Ctrl+C to cancel)
Front: bonjour
Back:  hello
✅ Card added!

[Default]> add
Front: au revoir
Back:  goodbye
✅ Card added!

[Default]> list
Cards in deck (2 total):
  1. bonjour → hello
  2. au revoir → goodbye

[Default]> review
2 card(s) due for review

--- Card 1/2 ---
Front: bonjour
Your answer: hello
✅ Correct (exact)
Suggested: [4] Easy
Grade [1-4, Enter=suggested]:

[Default]> stats
=== Stats for 'Default' ===
Total cards: 2
  New: 0
  Learning: 2
  Review: 0

Due today: 1
Reviews today: 1

[Default]> new Spanish
✅ Created and activated deck: Spanish

[Spanish]> decks
Available decks:
   Default (2 cards)

[Spanish]> exit
Goodbye! Happy learning! 🎓

## Command-Line Mode (Optional)

You can also use anki-mini with individual commands instead of the interactive shell:

```powershell
# Initialize (first time only)
anki-mini.exe init

# Add a card
anki-mini.exe add

# Start review
anki-mini.exe review

# View stats
anki-mini.exe stats

# Manage decks
anki-mini.exe deck list
anki-mini.exe deck new "Spanish"
anki-mini.exe deck select spanish

# Import/export cards
anki-mini.exe import cards.txt
anki-mini.exe export

# Full data migration (all decks, stats, settings)
anki-mini.exe export-data
anki-mini.exe import-data backup.zip
````

## Import/Export

### Card Import/Export

Cards are stored in tab-separated text files for easy editing:

```
front text<TAB>back text
bonjour<TAB>hello
au revoir<TAB>goodbye;bye
```

**Multiple answers**: Separate alternatives with `;` in the back field.

### Full Data Migration

For migrating between devices without USB, use the data migration commands:

**Export all data:**

```powershell
anki-mini.exe export-data
# Or specify file path:
anki-mini.exe export-data my-backup.zip
```

**Import all data:**

```powershell
anki-mini.exe import-data my-backup.zip
# Merge with existing data:
anki-mini.exe import-data my-backup.zip --merge
# Overwrite existing decks:
anki-mini.exe import-data my-backup.zip --merge --overwrite
```

The export file includes:

- ✅ All decks (cards + learning progress)
- ✅ App settings
- ✅ Active deck selection
- ✅ Review statistics and scheduling data

**Use cases:**

- Transfer data to a new device
- Create backups before major changes
- Share your complete deck collection

## Data Storage

Data is stored alongside the executable:

```
anki-mini/
  anki-mini.exe
  data/
    active_deck.txt
    decks/
      default/
        cards.txt
        state.json
    settings.json
  backups/
```

## Configuration

Edit `settings.json` to customize:

```json
{
  "daily_new": 20,
  "daily_review": 200,
  "lenient_threshold": 2,
  "autosave_every": 10
}
```

## Scheduling Algorithm

Uses **SM-2 (SuperMemo 2)** with 4 grades:

- **1 - Again**: Wrong answer, reset interval
- **2 - Hard**: Correct but struggled, shorter interval
- **3 - Good**: Correct, normal progression
- **4 - Easy**: Very easy, accelerated interval

The system auto-suggests grades based on correctness and response time.

## Requirements

- **Windows 10 or later** (x86_64)
- **No Python required** for the executable
- **Python 3.8+** if running from source

## License

MIT License - Free to use, modify, and distribute.

## Troubleshooting

**"Deck is locked by another process"**

- Close other anki-mini instances
- Delete `.lock` file in the deck folder if crashed

**Cards not showing as due**

- Check system date/time is correct

**Import/export dialog not appearing**

- Specify file path explicitly: `import cards.txt`

**Data migration between devices**

- Use `export-data` on old device, transfer the .zip file
- Use `import-data` on new device to restore everything

---

**Happy learning! 🎓**
