"""Full app data export/import for device migration."""

import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .utils import get_data_dir, read_json


class DataMigration:
    """Handles complete app data export and import for device migration."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = get_data_dir(data_dir)
        self.settings_file = self.data_dir.parent / 'settings.json'
    
    def export_all_data(self, output_path: Optional[Path] = None) -> Path:
        """
        Export complete app data to a zip file.
        Includes: all decks (cards + state), settings, active deck.
        
        Args:
            output_path: Destination file path. If None, generates timestamped filename.
        
        Returns:
            Path to created export file.
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path.cwd() / f"anki-mini-export-{timestamp}.zip"
        
        output_path = Path(output_path)
        
        # Create export archive
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add metadata
            metadata = self._create_metadata()
            zf.writestr('export_metadata.json', json.dumps(metadata, indent=2))
            
            # Export settings
            if self.settings_file.exists():
                zf.write(self.settings_file, 'settings.json')
            
            # Export active deck info
            active_deck_file = self.data_dir / 'active_deck.txt'
            if active_deck_file.exists():
                zf.write(active_deck_file, 'active_deck.txt')
            
            # Export all decks
            decks_dir = self.data_dir / 'decks'
            if decks_dir.exists():
                for deck_dir in decks_dir.iterdir():
                    if deck_dir.is_dir():
                        self._export_deck(zf, deck_dir)
        
        return output_path
    
    def import_all_data(self, import_path: Path, merge: bool = False, 
                       overwrite: bool = False) -> Dict[str, Any]:
        """
        Import complete app data from a zip file.
        
        Args:
            import_path: Path to import zip file.
            merge: If True, merge with existing data. If False, replace all data.
            overwrite: If True, overwrite existing decks with same name.
        
        Returns:
            Dictionary with import statistics.
        """
        import_path = Path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        stats = {
            'decks_imported': 0,
            'decks_skipped': 0,
            'total_cards': 0,
            'settings_imported': False,
            'errors': []
        }
        
        # Validate export file
        with zipfile.ZipFile(import_path, 'r') as zf:
            if 'export_metadata.json' not in zf.namelist():
                raise ValueError("Invalid export file: missing metadata")
            
            metadata = json.loads(zf.read('export_metadata.json'))
            self._validate_metadata(metadata)
        
        # If not merging, backup and clear existing data
        if not merge:
            self._backup_current_data()
            self._clear_data()
        
        # Import data
        with zipfile.ZipFile(import_path, 'r') as zf:
            # Import settings
            if 'settings.json' in zf.namelist():
                if not merge or overwrite:
                    self.settings_file.parent.mkdir(parents=True, exist_ok=True)
                    self.settings_file.write_bytes(zf.read('settings.json'))
                    stats['settings_imported'] = True
            
            # Import decks
            deck_stats = self._import_decks(zf, overwrite)
            stats['decks_imported'] = deck_stats['imported']
            stats['decks_skipped'] = deck_stats['skipped']
            stats['total_cards'] = deck_stats['total_cards']
            stats['errors'] = deck_stats['errors']
            
            # Import active deck (if not merging or if deck was imported)
            if 'active_deck.txt' in zf.namelist():
                active_deck = zf.read('active_deck.txt').decode('utf-8').strip()
                if not merge or (self.data_dir / 'decks' / active_deck).exists():
                    active_file = self.data_dir / 'active_deck.txt'
                    active_file.parent.mkdir(parents=True, exist_ok=True)
                    active_file.write_text(active_deck, encoding='utf-8')
        
        return stats
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create export metadata."""
        from .deck import DeckManager
        
        deck_manager = DeckManager(self.data_dir)
        decks = deck_manager.list_decks()
        
        return {
            'export_version': '1.0',
            'app_version': '1.0.0',
            'export_timestamp': datetime.now().isoformat(),
            'deck_count': len(decks),
            'total_cards': sum(d['card_count'] for d in decks),
            'deck_names': [d['display_name'] for d in decks]
        }
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate export metadata."""
        required_fields = ['export_version', 'app_version', 'export_timestamp']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Invalid export file: missing {field}")
        
        # Check version compatibility (currently accepting all v1.x)
        export_version = metadata.get('export_version', '0.0')
        if not export_version.startswith('1.'):
            raise ValueError(f"Incompatible export version: {export_version}")
    
    def _export_deck(self, zf: zipfile.ZipFile, deck_dir: Path) -> None:
        """Export a single deck to the archive."""
        deck_name = deck_dir.name
        
        # Export cards.txt
        cards_file = deck_dir / 'cards.txt'
        if cards_file.exists():
            zf.write(cards_file, f'decks/{deck_name}/cards.txt')
        
        # Export state.json
        state_file = deck_dir / 'state.json'
        if state_file.exists():
            zf.write(state_file, f'decks/{deck_name}/state.json')
    
    def _import_decks(self, zf: zipfile.ZipFile, overwrite: bool) -> Dict[str, Any]:
        """Import all decks from archive."""
        stats = {
            'imported': 0,
            'skipped': 0,
            'total_cards': 0,
            'errors': []
        }
        
        # Get list of decks in archive
        deck_dirs = set()
        for name in zf.namelist():
            if name.startswith('decks/') and '/' in name[6:]:
                deck_name = name.split('/')[1]
                deck_dirs.add(deck_name)
        
        # Import each deck
        for deck_name in deck_dirs:
            try:
                deck_path = self.data_dir / 'decks' / deck_name
                
                # Check if deck exists
                if deck_path.exists() and not overwrite:
                    stats['skipped'] += 1
                    continue
                
                # Create deck directory
                deck_path.mkdir(parents=True, exist_ok=True)
                
                # Import cards.txt
                cards_archive_path = f'decks/{deck_name}/cards.txt'
                if cards_archive_path in zf.namelist():
                    cards_content = zf.read(cards_archive_path)
                    (deck_path / 'cards.txt').write_bytes(cards_content)
                    
                    # Count cards
                    card_count = len([line for line in cards_content.decode('utf-8').strip().split('\n') 
                                     if line.strip()])
                    stats['total_cards'] += card_count
                
                # Import state.json
                state_archive_path = f'decks/{deck_name}/state.json'
                if state_archive_path in zf.namelist():
                    state_content = zf.read(state_archive_path)
                    (deck_path / 'state.json').write_bytes(state_content)
                
                stats['imported'] += 1
                
            except Exception as e:
                stats['errors'].append(f"Error importing deck '{deck_name}': {str(e)}")
        
        return stats
    
    def _backup_current_data(self) -> None:
        """Create backup of current data before import."""
        if not self.data_dir.exists():
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.data_dir.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"pre-import-backup-{timestamp}.zip"
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Backup settings
            if self.settings_file.exists():
                zf.write(self.settings_file, 'settings.json')
            
            # Backup data directory
            for file in self.data_dir.rglob('*'):
                if file.is_file() and file.name != '.lock':
                    rel_path = file.relative_to(self.data_dir.parent)
                    zf.write(file, str(rel_path))
        
        print(f"Backup created: {backup_file}")
    
    def _clear_data(self) -> None:
        """Clear existing data (used when not merging)."""
        import shutil
        
        # Clear decks
        decks_dir = self.data_dir / 'decks'
        if decks_dir.exists():
            shutil.rmtree(decks_dir)
        
        # Clear active deck file
        active_file = self.data_dir / 'active_deck.txt'
        if active_file.exists():
            active_file.unlink()
        
        # Note: We don't clear settings here as it's handled separately


def export_data(output_path: Optional[Path] = None, data_dir: Optional[Path] = None) -> Path:
    """
    Export all app data to a zip file.
    
    Args:
        output_path: Destination file path. If None, generates timestamped filename.
        data_dir: Data directory path. If None, uses default.
    
    Returns:
        Path to created export file.
    """
    migration = DataMigration(data_dir)
    return migration.export_all_data(output_path)


def import_data(import_path: Path, merge: bool = False, overwrite: bool = False,
                data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Import all app data from a zip file.
    
    Args:
        import_path: Path to import zip file.
        merge: If True, merge with existing data. If False, replace all data.
        overwrite: If True, overwrite existing decks with same name.
        data_dir: Data directory path. If None, uses default.
    
    Returns:
        Dictionary with import statistics.
    """
    migration = DataMigration(data_dir)
    return migration.import_all_data(import_path, merge, overwrite)
