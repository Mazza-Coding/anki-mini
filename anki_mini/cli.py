"""CLI interface using argparse."""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .utils import get_data_dir
from .config import load_config
from .deck import DeckManager
from .cards import CardManager
from .review import start_review
from .stats import StatsCalculator, print_stats
from .init import initialize_data_dir
from .migration import export_data, import_data


def cmd_init(args) -> int:
    """Initialize data directory."""
    data_dir = get_data_dir(args.data_dir)
    try:
        initialize_data_dir(data_dir)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_deck(args) -> int:
    """Manage decks."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    
    try:
        if args.deck_action == 'list':
            decks = deck_manager.list_decks()
            if not decks:
                print("No decks found. Use 'anki-mini deck new <name>' to create one.")
                return 0
            
            print("\nAvailable decks:")
            for deck in decks:
                marker = " *" if deck['is_active'] else "  "
                print(f"{marker} {deck['display_name']} ({deck['card_count']} cards)")
            print()
        
        elif args.deck_action == 'new':
            if not args.name:
                print("Error: deck name required", file=sys.stderr)
                return 1
            
            slug = deck_manager.create_deck(args.name, set_active=args.select)
            print(f"Created deck: {args.name}")
            if args.select:
                print(f"Activated deck: {args.name}")
        
        elif args.deck_action == 'select':
            if not args.name:
                print("Error: deck name required", file=sys.stderr)
                return 1
            
            deck_manager.set_active_deck(args.name)
            print(f"Activated deck: {args.name}")
        
        elif args.deck_action == 'rename':
            if not args.name or not args.new_name:
                print("Error: both old and new names required", file=sys.stderr)
                return 1
            
            deck_manager.rename_deck(args.name, args.new_name)
            print(f"Renamed deck: {args.name} → {args.new_name}")
        
        elif args.deck_action == 'delete':
            if not args.name:
                print("Error: deck name required", file=sys.stderr)
                return 1
            
            deck_manager.delete_deck(args.name, force=args.force, backup=args.backup)
            print(f"Deleted deck: {args.name}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_add(args) -> int:
    """Add cards to deck."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    
    try:
        deck_path = deck_manager.get_deck_path(args.deck)
        card_manager = CardManager(deck_path)
        
        if args.file:
            # Batch add from file
            source = Path(args.file)
            added, skipped = card_manager.import_cards(source)
            print(f"Imported {added} card(s), skipped {skipped} duplicate(s)")
        else:
            # Interactive add
            print("Add new card (Ctrl+C to cancel)")
            front = input("Front: ").strip()
            back = input("Back:  ").strip()
            
            if not front or not back:
                print("Error: both front and back required", file=sys.stderr)
                return 1
            
            if card_manager.add_card(front, back):
                print("Card added!")
            else:
                print("Card already exists (duplicate)")
        
        return 0
    
    except KeyboardInterrupt:
        print("\nCancelled")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_review(args) -> int:
    """Start review session."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    config = load_config(data_dir)
    
    try:
        deck_path = deck_manager.get_deck_path(args.deck)
        threshold = config.get('lenient_threshold', 2)
        start_review(deck_path, threshold)
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_stats(args) -> int:
    """Show deck statistics."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    
    try:
        if args.all:
            # Show stats for all decks
            decks = deck_manager.list_decks()
            for deck in decks:
                deck_path = deck_manager.get_deck_path(deck['slug'])
                calc = StatsCalculator(deck_path)
                stats = calc.get_stats()
                print_stats(stats, deck['display_name'])
        else:
            # Show stats for specific or active deck
            deck_path = deck_manager.get_deck_path(args.deck)
            deck_name = args.deck or deck_manager.get_active_deck()
            
            # Get display name
            from .utils import read_json
            state = read_json(deck_path / 'state.json', {})
            display_name = state.get('display_name', deck_name)
            
            calc = StatsCalculator(deck_path)
            stats = calc.get_stats()
            print_stats(stats, display_name)
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_import(args) -> int:
    """Import cards from file."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    
    try:
        # Get source file
        if args.path:
            source = Path(args.path)
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
                    return 0
                
                source = Path(file_path)
            except Exception as e:
                print(f"Error opening file picker: {e}", file=sys.stderr)
                return 1
        
        # Import to deck
        deck_path = deck_manager.get_deck_path(args.deck)
        card_manager = CardManager(deck_path)
        
        added, skipped = card_manager.import_cards(source)
        print(f"Imported {added} card(s), skipped {skipped} duplicate(s)")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_shell(args) -> int:
    """Start interactive shell."""
    from .shell import start_shell
    start_shell(args.data_dir)
    return 0


def cmd_export(args) -> int:
    """Export cards to file."""
    data_dir = get_data_dir(args.data_dir)
    deck_manager = DeckManager(data_dir)
    
    try:
        if args.all:
            # Export all decks
            decks = deck_manager.list_decks()
            for deck in decks:
                deck_path = deck_manager.get_deck_path(deck['slug'])
                card_manager = CardManager(deck_path)
                
                output = Path(f"{deck['slug']}.txt")
                count = card_manager.export_cards(output)
                print(f"Exported {count} card(s) from '{deck['display_name']}' to {output}")
        else:
            # Get destination file
            if args.path:
                dest = Path(args.path)
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
                        return 0
                    
                    dest = Path(file_path)
                except Exception as e:
                    print(f"Error opening save dialog: {e}", file=sys.stderr)
                    return 1
            
            # Export deck
            deck_path = deck_manager.get_deck_path(args.deck)
            card_manager = CardManager(deck_path)
            
            count = card_manager.export_cards(dest)
            print(f"Exported {count} card(s) to {dest}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_export_data(args) -> int:
    """Export complete app data for migration."""
    data_dir = get_data_dir(args.data_dir)
    
    try:
        # Get destination file
        if args.path:
            dest = Path(args.path)
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
                    return 0
                
                dest = Path(file_path)
            except Exception as e:
                print(f"Error opening save dialog: {e}", file=sys.stderr)
                return 1
        
        # Export all data
        print("Exporting complete app data...")
        output_path = export_data(dest, data_dir)
        print(f"✅ Export complete: {output_path}")
        print("\nThis file contains:")
        print("  • All decks (cards + learning progress)")
        print("  • App settings")
        print("  • Active deck selection")
        print("\nYou can import this on another device using 'import-data' command.")
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_import_data(args) -> int:
    """Import complete app data from migration file."""
    data_dir = get_data_dir(args.data_dir)
    
    try:
        # Get source file
        if args.path:
            source = Path(args.path)
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
                    return 0
                
                source = Path(file_path)
            except Exception as e:
                print(f"Error opening file picker: {e}", file=sys.stderr)
                return 1
        
        if not source.exists():
            print(f"Error: File not found: {source}", file=sys.stderr)
            return 1
        
        # Confirm import action
        if not args.merge and not args.yes:
            print("⚠️  WARNING: This will REPLACE all existing data!")
            print("   Use --merge to merge with existing data instead.")
            print("   A backup will be created automatically.")
            confirm = input("\nContinue? (yes/y): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("Import cancelled")
                return 0
        
        # Import data
        print("Importing app data...")
        stats = import_data(source, merge=args.merge, overwrite=args.overwrite, data_dir=data_dir)
        
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
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='anki-mini',
        description='Portable CLI flashcard app with spaced repetition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  anki-mini init                        Initialize data directory
  anki-mini deck list                   List all decks
  anki-mini deck new "Spanish Vocab"   Create new deck
  anki-mini deck select spanish-vocab  Set active deck
  anki-mini add                         Add card interactively
  anki-mini review                      Start review session
  anki-mini stats                       Show statistics
  anki-mini import cards.txt            Import cards
  anki-mini export                      Export cards with dialog
  anki-mini export-data                 Export all data for migration
  anki-mini import-data backup.zip      Import all data from backup
        """
    )
    
    parser.add_argument('--data-dir', help='Override data directory path')
    parser.add_argument('--version', action='version', version='anki-mini 1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init
    subparsers.add_parser('init', help='Initialize data directory')
    
    # shell
    subparsers.add_parser('shell', help='Start interactive shell (default if no command)')
    
    # deck
    deck_parser = subparsers.add_parser('deck', help='Manage decks')
    deck_parser.add_argument('deck_action', choices=['list', 'new', 'select', 'rename', 'delete'])
    deck_parser.add_argument('name', nargs='?', help='Deck name')
    deck_parser.add_argument('--new-name', help='New name for rename')
    deck_parser.add_argument('--select', action='store_true', help='Set as active after creating')
    deck_parser.add_argument('--force', action='store_true', help='Force delete non-empty deck')
    deck_parser.add_argument('--backup', action='store_true', help='Backup before delete')
    
    # add
    add_parser = subparsers.add_parser('add', help='Add cards')
    add_parser.add_argument('--deck', help='Target deck (default: active)')
    add_parser.add_argument('--file', help='Batch add from file')
    
    # review
    review_parser = subparsers.add_parser('review', help='Start review session')
    review_parser.add_argument('--deck', help='Deck to review (default: active)')
    
    # stats
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--deck', help='Deck to show (default: active)')
    stats_parser.add_argument('--all', action='store_true', help='Show all decks')
    
    # import
    import_parser = subparsers.add_parser('import', help='Import cards from file')
    import_parser.add_argument('path', nargs='?', help='Source file (or use picker)')
    import_parser.add_argument('--deck', help='Target deck (default: active)')
    
    # export
    export_parser = subparsers.add_parser('export', help='Export cards to file')
    export_parser.add_argument('path', nargs='?', help='Destination file (or use picker)')
    export_parser.add_argument('--deck', help='Source deck (default: active)')
    export_parser.add_argument('--all', action='store_true', help='Export all decks')
    
    # export-data (full migration)
    export_data_parser = subparsers.add_parser('export-data', help='Export complete app data for migration')
    export_data_parser.add_argument('path', nargs='?', help='Destination file (or use picker)')
    
    # import-data (full migration)
    import_data_parser = subparsers.add_parser('import-data', help='Import complete app data from migration file')
    import_data_parser.add_argument('path', nargs='?', help='Source file (or use picker)')
    import_data_parser.add_argument('--merge', action='store_true', help='Merge with existing data instead of replacing')
    import_data_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing decks with same name')
    import_data_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command provided, start interactive shell
    if not args.command:
        from .shell import start_shell
        start_shell(args.data_dir)
        return 0
    
    # Route to command handlers
    commands = {
        'init': cmd_init,
        'shell': cmd_shell,
        'deck': cmd_deck,
        'add': cmd_add,
        'review': cmd_review,
        'stats': cmd_stats,
        'import': cmd_import,
        'export': cmd_export,
        'export-data': cmd_export_data,
        'import-data': cmd_import_data,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    
    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
