"""Interactive shell interface for anki-mini."""

import sys
from pathlib import Path
from typing import Optional

from .utils import get_data_dir
from .deck import DeckManager
from .cards import CardManager
from .review import start_review, start_practice
from .stats import StatsCalculator, print_stats
from .config import load_config
from .init import initialize_data_dir
from .utils import read_json
from .migration import export_data, import_data


class InteractiveShell:
    """Interactive command-line shell for anki-mini."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = get_data_dir(data_dir)
        self.running = True
        self.deck_manager = None
        self.config = None
        
        # Check if initialized
        if not (self.data_dir / 'decks').exists():
            print("ℹ️  Data directory not initialized. Initializing now...")
            initialize_data_dir(self.data_dir)
        
        self.deck_manager = DeckManager(self.data_dir)
        self.config = load_config(self.data_dir)
    
    def run(self):
        """Run the interactive shell."""
        self.print_welcome()
        
        while self.running:
            try:
                self.print_prompt()
                command = input().strip()
                
                if not command:
                    continue
                
                self.execute_command(command)
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to leave the shell.")
            except EOFError:
                print("\n")
                break
        
        print("Goodbye! Happy learning! 🎓")
    
    def print_welcome(self):
        """Print welcome message."""
        print("=" * 60)
        print("  anki-mini v1.0.0 - Interactive Shell")
        print("=" * 60)
        print()
        print("Type 'help' for available commands or 'exit' to quit.")
        print()
        
        # Show active deck with stats
        active = self.deck_manager.get_active_deck()
        state = read_json(self.data_dir / 'decks' / active / 'state.json', {})
        display_name = state.get('display_name', active)
        
        # Quick stats for active deck
        try:
            deck_path = self.deck_manager.get_deck_path()
            calc = StatsCalculator(deck_path)
            stats = calc.get_stats()
            
            print(f"Active deck: {display_name}")
            print(f"  Cards: {stats['total_cards']} total, {stats['due_today']} due today")
            print()
        except Exception:
            print(f"Active deck: {display_name}")
            print()
    
    def print_prompt(self):
        """Print command prompt."""
        active = self.deck_manager.get_active_deck()
        state = read_json(self.data_dir / 'decks' / active / 'state.json', {})
        display_name = state.get('display_name', active)
        prompt_text = f"[{display_name}]> "
        print(prompt_text, end='', flush=True)
    
    def execute_command(self, command: str):
        """Execute a command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Command routing
        commands = {
            'help': self.cmd_help,
            '?': self.cmd_help,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
            'q': self.cmd_exit,
            'add': self.cmd_add,
            'edit': self.cmd_edit_card,
            'delete': self.cmd_delete_card,
            'remove': self.cmd_delete_card,
            'review': self.cmd_review,
            'r': self.cmd_review,
            'practice': self.cmd_practice,
            'p': self.cmd_practice,
            'stats': self.cmd_stats,
            's': self.cmd_stats,
            'decks': self.cmd_decks,
            'deck': self.cmd_deck_select,
            'new': self.cmd_deck_new,
            'rename': self.cmd_deck_rename,
            'deldeck': self.cmd_deck_delete,
            'list': self.cmd_list_cards,
            'import': self.cmd_import,
            'export': self.cmd_export,
            'export-data': self.cmd_export_data,
            'import-data': self.cmd_import_data,
            'clear': self.cmd_clear,
        }
        
        handler = commands.get(cmd)
        if handler:
            try:
                handler(args)
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Unknown command: {cmd}")
            print("Type 'help' for available commands.")
        
        print()  # Blank line after command
    
    def cmd_help(self, args: str):
        """Show help."""
        print("\n=== Available Commands ===\n")
        
        sections = [
            ("Deck Management", [
                ("decks", "List all decks"),
                ("deck <name>", "Switch to deck"),
                ("new <name>", "Create new deck"),
                ("rename <new_name>", "Rename active deck"),
                ("deldeck [name]", "Delete deck (with confirmation)")
            ]),
            ("Card Operations", [
                ("add", "Add new card"),
                ("list", "List all cards in active deck"),
                ("edit <number>", "Edit card by number from list"),
                ("delete <number>", "Delete card by number from list"),
                ("import [file]", "Import cards from file"),
                ("export [file]", "Export cards to file")
            ]),
            ("Study", [
                ("review, r", "Start review session (due cards only)"),
                ("practice, p [limit]", "Practice all cards (hardest first)"),
                ("stats, s", "Show statistics")
            ]),
            ("Data Migration", [
                ("export-data [file]", "Export all app data for device migration"),
                ("import-data [file]", "Import all app data from backup")
            ]),
            ("Other", [
                ("clear", "Clear screen"),
                ("help, ?", "Show this help"),
                ("exit, quit, q", "Exit shell")
            ])
        ]
        
        for section_name, commands in sections:
            print(f"{section_name}:")
            for cmd, desc in commands:
                print(f"  {cmd.ljust(20)} - {desc}")
            print()
    
    def cmd_exit(self, args: str):
        """Exit the shell."""
        self.running = False
    
    def cmd_add(self, args: str):
        """Add a card."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            
            print("ℹ️  Add new card (Ctrl+C to cancel)")
            front = input("Front: ").strip()
            back = input("Back:  ").strip()
            
            if not front or not back:
                print("❌ Error: Both front and back required")
                return
            
            if card_manager.add_card(front, back):
                print("✅ Card added!")
            else:
                print("⚠️  Card already exists (duplicate)")
        
        except KeyboardInterrupt:
            print("\nℹ️  Cancelled")
    
    def cmd_review(self, args: str):
        """Start review session."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            threshold = self.config.get('lenient_threshold', 2)
            start_review(deck_path, threshold)
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_practice(self, args: str):
        """Start practice session with all cards (hardest first)."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            threshold = self.config.get('lenient_threshold', 2)
            
            # Parse optional limit argument
            limit = None
            if args.strip():
                try:
                    limit = int(args.strip())
                    if limit <= 0:
                        print("Error: Limit must be a positive number")
                        return
                except ValueError:
                    print("Error: Invalid limit. Usage: practice [number]")
                    return
            
            start_practice(deck_path, threshold, limit)
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_stats(self, args: str):
        """Show statistics."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            active = self.deck_manager.get_active_deck()
            state = read_json(deck_path / 'state.json', {})
            display_name = state.get('display_name', active)
            
            calc = StatsCalculator(deck_path)
            stats = calc.get_stats()
            print_stats(stats, display_name)
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_decks(self, args: str):
        """List all decks."""
        decks = self.deck_manager.list_decks()
        if not decks:
            print("ℹ️  No decks found.")
            return
        
        print("\nAvailable decks:")
        for deck in decks:
            marker = " *" if deck['is_active'] else "  "
            name = deck['display_name']
            cards = f"({deck['card_count']} cards)"
            print(f"{marker} {name} {cards}")
        print()
    
    def cmd_deck_select(self, args: str):
        """Switch to a deck."""
        if not args:
            print("Usage: deck <name>")
            return
        
        try:
            self.deck_manager.set_active_deck(args)
            print(f"✅ Switched to deck: {args}")
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_deck_new(self, args: str):
        """Create new deck."""
        if not args:
            print("Usage: new <name>")
            return
        
        try:
            slug = self.deck_manager.create_deck(args, set_active=True)
            print(f"✅ Created and activated deck: {args}")
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_list_cards(self, args: str):
        """List all cards in active deck."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            cards = card_manager.get_all_cards()
            
            if not cards:
                print("No cards in this deck.")
                return
            
            print(f"\nCards in deck ({len(cards)} total):")
            for i, (card_id, front, back) in enumerate(cards, 1):
                # Display full text without truncation
                print(f"  {i}. {front} → {back}")
            print()
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_import(self, args: str):
        """Import cards from file."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            
            if args:
                # File path provided
                source = Path(args)
            else:
                # Open file picker
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_path = filedialog.askopenfilename(
                        title="Select file to import",
                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                    )
                    
                    root.destroy()
                    
                    if not file_path:
                        print("Import cancelled")
                        return
                    
                    source = Path(file_path)
                except Exception as e:
                    print(f"Error opening file picker: {e}")
                    return
            
            added, skipped = card_manager.import_cards(source)
            print(f"✅ Imported {added} card(s), skipped {skipped} duplicate(s)")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_export(self, args: str):
        """Export cards to file."""
        try:
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            
            if args:
                # File path provided
                dest = Path(args)
            else:
                # Open save dialog
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_path = filedialog.asksaveasfilename(
                        title="Save exported cards",
                        defaultextension=".txt",
                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                    )
                    
                    root.destroy()
                    
                    if not file_path:
                        print("Export cancelled")
                        return
                    
                    dest = Path(file_path)
                except Exception as e:
                    print(f"Error opening save dialog: {e}")
                    return
            
            count = card_manager.export_cards(dest)
            print(f"✅ Exported {count} card(s) to {dest}")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_clear(self, args: str):
        """Clear screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_welcome()
    
    def cmd_edit_card(self, args: str):
        """Edit a card by number."""
        if not args:
            print("Usage: edit <number>")
            print("Use 'list' to see card numbers.")
            return
        
        try:
            card_num = int(args)
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            cards = card_manager.get_all_cards()
            
            if card_num < 1 or card_num > len(cards):
                print(f"Error: Card number must be between 1 and {len(cards)}")
                return
            
            card_id, old_front, old_back = cards[card_num - 1]
            
            print(f"\nEditing card #{card_num}")
            print(f"Current front: {old_front}")
            print(f"Current back:  {old_back}")
            print()
            
            new_front = input(f"New front (Enter to keep): ").strip()
            new_back = input(f"New back (Enter to keep): ").strip()
            
            if not new_front:
                new_front = old_front
            if not new_back:
                new_back = old_back
            
            if new_front == old_front and new_back == old_back:
                print("No changes made.")
                return
            
            # Delete old card and add new one
            self._delete_card_by_id(card_id, deck_path)
            
            if card_manager.add_card(new_front, new_back):
                print("✅ Card updated!")
            else:
                # Restore old card if new one is duplicate
                card_manager.add_card(old_front, old_back)
                print("⚠️  New card already exists. Changes reverted.")
        
        except ValueError:
            print("Error: Please provide a valid card number")
        except KeyboardInterrupt:
            print("\nCancelled")
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_delete_card(self, args: str):
        """Delete a card by number."""
        if not args:
            print("Usage: delete <number>")
            print("Use 'list' to see card numbers.")
            return
        
        try:
            card_num = int(args)
            deck_path = self.deck_manager.get_deck_path()
            card_manager = CardManager(deck_path)
            cards = card_manager.get_all_cards()
            
            if card_num < 1 or card_num > len(cards):
                print(f"Error: Card number must be between 1 and {len(cards)}")
                return
            
            card_id, front, back = cards[card_num - 1]
            
            # Show card and confirm
            print(f"\nDelete card #{card_num}?")
            print(f"Front: {front}")
            print(f"Back:  {back}")
            
            confirm = input("\nConfirm deletion? (yes/y): ").strip().lower()
            
            if confirm in ['yes', 'y']:
                self._delete_card_by_id(card_id, deck_path)
                print("✅ Card deleted!")
            else:
                print("Cancelled.")
        
        except ValueError:
            print("Error: Please provide a valid card number")
        except Exception as e:
            print(f"Error: {e}")
    
    def _delete_card_by_id(self, card_id: str, deck_path: Path):
        """Delete a card by its ID (internal helper)."""
        from .utils import deck_lock, atomic_write
        
        with deck_lock(deck_path):
            # Remove from cards.txt
            cards_file = deck_path / 'cards.txt'
            if cards_file.exists():
                lines = []
                content = cards_file.read_text(encoding='utf-8')
                
                for line in content.strip().split('\n'):
                    if not line.strip():
                        continue
                    
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        from .utils import stable_card_id
                        line_id = stable_card_id(parts[0], parts[1])
                        if line_id != card_id:
                            lines.append(line)
                
                atomic_write(cards_file, '\n'.join(lines) + '\n' if lines else '')
            
            # Remove from state.json
            state_file = deck_path / 'state.json'
            state = read_json(state_file, {})
            if 'cards' in state and card_id in state['cards']:
                del state['cards'][card_id]
                from .utils import atomic_write_json
                atomic_write_json(state_file, state)
    
    def cmd_deck_rename(self, args: str):
        """Rename the active deck."""
        if not args:
            print("Usage: rename <new_name>")
            return
        
        try:
            active = self.deck_manager.get_active_deck()
            self.deck_manager.rename_deck(active, args)
            print(f"✅ Deck renamed to: {args}")
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_deck_delete(self, args: str):
        """Delete a deck."""
        if args:
            deck_name = args
        else:
            # Delete active deck
            active = self.deck_manager.get_active_deck()
            state = read_json(self.data_dir / 'decks' / active / 'state.json', {})
            deck_name = state.get('display_name', active)
        
        try:
            # Get deck info
            decks = self.deck_manager.list_decks()
            deck_info = next((d for d in decks if d['display_name'].lower() == deck_name.lower() or d['slug'] == deck_name), None)
            
            if not deck_info:
                print(f"Error: Deck not found: {deck_name}")
                return
            
            # Confirm deletion
            print(f"\nDelete deck '{deck_info['display_name']}'?")
            print(f"Cards: {deck_info['card_count']}")
            
            if deck_info['card_count'] > 0:
                print("⚠️  Warning: This deck contains cards!")
            
            confirm = input("\nConfirm deletion? (yes/y): ").strip().lower()
            
            if confirm in ['yes', 'y']:
                backup = input("Create backup? (yes/y): ").strip().lower()
                do_backup = backup in ['yes', 'y']
                
                self.deck_manager.delete_deck(deck_name, force=True, backup=do_backup)
                print(f"✅ Deck '{deck_info['display_name']}' deleted!")
            else:
                print("Cancelled.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_export_data(self, args: str):
        """Export complete app data for migration."""
        try:
            if args:
                # File path provided
                dest = Path(args)
            else:
                # Open save dialog
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    from datetime import datetime
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    default_name = f"anki-mini-export-{timestamp}.zip"
                    
                    file_path = filedialog.asksaveasfilename(
                        title="Save complete data export",
                        defaultextension=".zip",
                        initialfile=default_name,
                        filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
                    )
                    
                    root.destroy()
                    
                    if not file_path:
                        print("Export cancelled")
                        return
                    
                    dest = Path(file_path)
                except Exception as e:
                    print(f"Error opening save dialog: {e}")
                    return
            
            # Export all data
            print("Exporting complete app data...")
            output_path = export_data(dest, self.data_dir)
            print(f"✅ Export complete: {output_path}")
            print("\nThis file contains:")
            print("  • All decks (cards + learning progress)")
            print("  • App settings")
            print("  • Active deck selection")
            print("\nYou can import this on another device using 'import-data' command.")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def cmd_import_data(self, args: str):
        """Import complete app data from migration file."""
        try:
            if args:
                # Parse arguments (file path and optional flags)
                parts = args.split()
                source = Path(parts[0])
                merge = '--merge' in parts
                overwrite = '--overwrite' in parts
            else:
                # Open file picker
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    file_path = filedialog.askopenfilename(
                        title="Select data export file to import",
                        filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
                    )
                    
                    root.destroy()
                    
                    if not file_path:
                        print("Import cancelled")
                        return
                    
                    source = Path(file_path)
                    merge = False
                    overwrite = False
                except Exception as e:
                    print(f"Error opening file picker: {e}")
                    return
            
            if not source.exists():
                print(f"Error: File not found: {source}")
                return
            
            # Confirm import action
            if not merge:
                print("⚠️  WARNING: This will REPLACE all existing data!")
                print("   Add '--merge' to merge with existing data instead.")
                print("   A backup will be created automatically.")
                confirm = input("\nContinue? (yes/y): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("Import cancelled")
                    return
            
            # Import data
            print("Importing app data...")
            stats = import_data(source, merge=merge, overwrite=overwrite, data_dir=self.data_dir)
            
            # Print results
            print("\n✅ Import complete!")
            print(f"\nStatistics:")
            print(f"  • Decks imported: {stats['decks_imported']}")
            print(f"  • Decks skipped: {stats['decks_skipped']}")
            print(f"  • Total cards: {stats['total_cards']}")
            print(f"  • Settings imported: {'Yes' if stats['settings_imported'] else 'No'}")
            
            if stats['errors']:
                print(f"\n⚠️  Errors encountered:")
                for error in stats['errors']:
                    print(f"  • {error}")
        
        except Exception as e:
            print(f"Error: {e}")


def start_shell(data_dir: Optional[str] = None):
    """Start interactive shell."""
    shell = InteractiveShell(data_dir)
    shell.run()
