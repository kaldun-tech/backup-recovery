#!/usr/bin/env python3
"""
Local Backup Manager - Handles air-gapped local backup operations
Functional implementation for testing
"""

import logging
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LocalBackupManager:
    """Local backup manager for air-gapped storage"""

    def __init__(self, config: Dict[str, Any], backup_id: str):
        self.config = config
        self.backup_id = backup_id
        self.enabled = config.get('enabled', True)
        self.backup_dir = Path(config.get('backup_directory', '/tmp/local-backups'))
        self.compression = config.get('compression', False)
        self.encryption = config.get('encryption', False)
    
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
        if not self.enabled:
            logger.info("Local backup is disabled in configuration")
        
    def backup_files(self, files: List[Path], profile: str) -> bool:
        """Backup files to local storage"""
        if not self.enabled:
            logger.info(f"Local backup skipped for {len(files)} files (disabled)")
            return True
        
        try:
            logger.info(f"Local backup starting for {len(files)} files")
        
            # Create backup-specific directory
            backup_path = self.backup_dir / self.backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
        
            # Backup metadata
            metadata = {
                'backup_id': self.backup_id,
                'profile': profile,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'files_count': len(files),
                'files': []
            }
        
            # Copy files
            successful_files = 0
            for file_path in files:
                try:
                    if file_path.exists() and file_path.is_file():
                        # Create relative path structure
                        rel_path = file_path.relative_to(file_path.anchor)
                        dest_path = backup_path / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                        # Copy file
                        shutil.copy2(file_path, dest_path)
                        successful_files += 1
                    
                        # Add to metadata
                        metadata['files'].append({
                            'source': str(file_path),
                            'destination': str(dest_path),
                            'size': file_path.stat().st_size,
                            'status': 'success'
                        })
                    
                        logger.debug(f"Backed up {file_path} to {dest_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to backup {file_path}: {e}")
                    metadata['files'].append({
                        'source': str(file_path),
                        'status': 'failed',
                        'error': str(e)
                    })
        
            # Save metadata
            metadata_file = backup_path / 'backup-metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Local backup completed: {successful_files}/{len(files)} files successful")
            return successful_files > 0
        
        except Exception as e:
            logger.error(f"Local backup failed: {e}")
            return False
        
    def restore_files(self, backup_id: str, target_path: Path) -> bool:
        """Restore files from local backup"""
        if not self.enabled:
            logger.info("Local restore skipped (disabled)")
            return True
        
        try:
            logger.info(f"Local restore starting for backup {backup_id}")
        
            # Find backup directory
            backup_path = self.backup_dir / backup_id
            if not backup_path.exists():
                logger.error(f"Backup directory not found: {backup_path}")
                return False
            
            # Read metadata
            metadata_file = backup_path / 'backup-metadata.json'
            if not metadata_file.exists():
                logger.error(f"Backup metadata not found: {metadata_file}")
                return False
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Restore files
            target_path.mkdir(parents=True, exist_ok=True)
            successful_restores = 0
        
            for file_info in metadata.get('files', []):
                if file_info.get('status') != 'success':
                    continue
                
                try:
                    source_path = Path(file_info['destination'])
                    if source_path.exists():
                        # Use original filename in target directory
                        original_name = Path(file_info['source']).name
                        dest_path = target_path / original_name
                    
                        shutil.copy2(source_path, dest_path)
                        successful_restores += 1
                        logger.debug(f"Restored {source_path} to {dest_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to restore {file_info['source']}: {e}")
        
            logger.info(f"Local restore completed: {successful_restores} files restored")
            return successful_restores > 0
        
        except Exception as e:
            logger.error(f"Local restore failed: {e}")
            return False
        
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
    
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / 'backup-metadata.json'
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                                backups.append(metadata)
                        except Exception as e:
                            logger.error(f"Failed to read metadata for {backup_dir}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups