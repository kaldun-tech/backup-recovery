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
from typing import Dict, List, Any

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
        self.backup_metadata = 'backup-metadata.json'

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        if not self.enabled:
            logger.info("Local backup is disabled in configuration")

    def backup_files(self, files: List[Path], profile: str) -> bool:
        """Backup files to local storage"""
        if not self.enabled:
            logger.info("Local backup skipped for %d files (disabled)", len(files))
            return True

        try:
            logger.info("Local backup starting for %d files", len(files))

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

                        logger.debug("Backed up %s to %s", file_path, dest_path)
                    else:
                        # File doesn't exist or isn't a regular file
                        error_msg = f"File does not exist or is not a regular file: {file_path}"
                        logger.error(error_msg)
                        metadata['files'].append({
                            'source': str(file_path),
                            'status': 'failed',
                            'error': error_msg,
                            'error_type': 'FileNotFoundError'
                        })

                except OSError as e:
                    logger.error("Failed to backup %s: %s", file_path, e, exc_info=True)
                    metadata['files'].append({
                        'source': str(file_path),
                        'status': 'failed',
                        'error': str(e),
                        'error_type': type(e).__name__
                    })

            # Save metadata
            metadata_file = backup_path / self.backup_metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.info("Local backup completed: %d/%d files successful", successful_files, len(files))
            return successful_files > 0

        except (OSError, json.JSONEncodeError) as e:
            logger.error("Local backup failed: %s", e, exc_info=True)
            return False

    def restore_files(self, backup_id: str, target_path: Path) -> bool:
        """Restore files from local backup"""
        if not self.enabled:
            logger.info("Local restore skipped (disabled)")
            return True

        try:
            logger.info("Local restore starting for backup %s", backup_id)

            # Find backup directory
            backup_path = self.backup_dir / backup_id
            if not backup_path.exists():
                logger.error("Backup directory not found: %s", backup_path)
                return False

            # Read metadata
            metadata_file = backup_path / self.backup_metadata
            if not metadata_file.exists():
                logger.error("Backup metadata not found: %s", metadata_file)
                return False

            with open(metadata_file, 'r', encoding='utf-8') as f:
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
                        logger.debug("Restored %s to %s", source_path, dest_path)

                except (OSError, KeyError) as e:
                    logger.error("Failed to restore %s: %s", file_info.get('source', 'unknown'), e, exc_info=True)

            logger.info("Local restore completed: %d files restored", successful_restores)
            return successful_restores > 0

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Local restore failed: %s", e, exc_info=True)
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []

        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / self.backup_metadata
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                backups.append(metadata)
                        except (OSError, json.JSONDecodeError) as e:
                            logger.error("Failed to read metadata for %s: %s", backup_dir, e, exc_info=True)

        except OSError as e:
            logger.error("Failed to list backups: %s", e, exc_info=True)

        return backups
