#!/usr/bin/env python3
"""
Local Backup Manager - Handles air-gapped local backup operations
Functional implementation for testing
"""

import logging
import shutil
import json
import zipfile
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
        self.cleanup_source = config.get('cleanup_source_after_compression', True)
        self.retention_days = config.get('retention_days', None)
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

            logger.info(
                "Local backup completed: %d/%d files successful",
                successful_files, len(files))

            # Apply compression if enabled
            if self.compression and successful_files > 0:
                self._compress_backup(backup_path)

            # Clean up old backups based on retention policy
            if self.retention_days is not None:
                self._cleanup_old_backups()

            return successful_files > 0

        except (OSError, json.JSONEncodeError) as e:
            logger.error("Local backup failed: %s", e, exc_info=True)
            return False

    def _compress_backup(self, backup_path: Path) -> bool:
        """Compress backup directory to zip file"""
        try:
            zip_file = self.backup_dir / f"{self.backup_id}.zip"
            logger.info("Compressing backup to %s", zip_file)

            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        # Store relative path in zip
                        arcname = file_path.relative_to(backup_path)
                        zf.write(file_path, arcname)
                        logger.debug("Added to zip: %s", arcname)

            original_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            compressed_size = zip_file.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            logger.info(
                "Compression completed: %d bytes -> %d bytes (%.1f%% reduction)",
                original_size, compressed_size, compression_ratio)

            # Remove source directory if cleanup is enabled
            if self.cleanup_source:
                logger.info("Removing uncompressed backup directory: %s", backup_path)
                shutil.rmtree(backup_path)

            return True

        except (OSError, zipfile.BadZipFile) as e:
            logger.error("Failed to compress backup: %s", e, exc_info=True)
            return False

    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention_days"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

            for backup_dir in self.backup_dir.iterdir():
                if not backup_dir.is_dir():
                    continue

                metadata_file = backup_dir / self.backup_metadata
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        backup_time = datetime.fromisoformat(metadata['timestamp'])

                        if backup_time < cutoff_time:
                            logger.info(
                                "Removing backup older than %d days: %s",
                                self.retention_days, backup_dir.name)
                            shutil.rmtree(backup_dir)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error("Failed to parse backup metadata %s: %s", metadata_file, e)

            # Also remove orphaned zip files older than retention period
            for zip_file in self.backup_dir.glob('*.zip'):
                zip_mtime = datetime.fromtimestamp(zip_file.stat().st_mtime, tz=timezone.utc)
                if zip_mtime < cutoff_time:
                    logger.info("Removing old zip file: %s", zip_file.name)
                    zip_file.unlink()

        except OSError as e:
            logger.error("Failed to cleanup old backups: %s", e, exc_info=True)

    def restore_files(self, backup_id: str, target_path: Path) -> bool:
        """Restore files from local backup (supports both directories and zip files)"""
        if not self.enabled:
            logger.info("Local restore skipped (disabled)")
            return True

        try:
            logger.info("Local restore starting for backup %s", backup_id)

            # Check for compressed backup first
            zip_file = self.backup_dir / f"{backup_id}.zip"
            backup_path = self.backup_dir / backup_id

            if zip_file.exists():
                logger.info("Found compressed backup, extracting from %s", zip_file)
                return self._restore_from_zip(zip_file, target_path, backup_id)
            elif backup_path.exists():
                logger.info("Found uncompressed backup directory")
                return self._restore_from_directory(backup_path, target_path)
            else:
                logger.error("Backup not found: %s or %s", backup_path, zip_file)
                return False

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Local restore failed: %s", e, exc_info=True)
            return False

    def _restore_from_zip(self, zip_file: Path, target_path: Path, backup_id: str) -> bool:
        """Restore files from a compressed zip backup"""
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            successful_restores = 0

            with zipfile.ZipFile(zip_file, 'r') as zf:
                for file_info in zf.filelist:
                    if not file_info.is_dir():
                        try:
                            # Extract file, preserving structure
                            extracted_path = target_path / file_info.filename
                            extracted_path.parent.mkdir(parents=True, exist_ok=True)

                            with zf.open(file_info) as source, open(extracted_path, 'wb') as target:
                                shutil.copyfileobj(source, target)

                            successful_restores += 1
                            logger.debug("Restored from zip: %s", file_info.filename)

                        except (OSError, KeyError) as e:
                            logger.error("Failed to restore %s from zip: %s", file_info.filename, e)

            logger.info("Local restore from zip completed: %d files restored", successful_restores)
            return successful_restores > 0

        except zipfile.BadZipFile as e:
            logger.error("Failed to read zip file %s: %s", zip_file, e, exc_info=True)
            return False

    def _restore_from_directory(self, backup_path: Path, target_path: Path) -> bool:
        """Restore files from an uncompressed backup directory"""
        try:
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
                    logger.error(
                        "Failed to restore %s: %s",
                        file_info.get('source', 'unknown'), e, exc_info=True)

            logger.info("Local restore from directory completed: %d files restored", successful_restores)
            return successful_restores > 0

        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Local restore from directory failed: %s", e, exc_info=True)
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups (both compressed and uncompressed)"""
        backups = []

        try:
            # List uncompressed backups (directories with metadata)
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / self.backup_metadata
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                metadata['compressed'] = False
                                backups.append(metadata)
                        except (OSError, json.JSONDecodeError) as e:
                            logger.error(
                                "Failed to read metadata for %s: %s",
                                backup_dir, e, exc_info=True)

            # List compressed backups (zip files)
            for zip_file in self.backup_dir.glob('*.zip'):
                try:
                    with zipfile.ZipFile(zip_file, 'r') as zf:
                        metadata_data = zf.read(self.backup_metadata).decode('utf-8')
                        metadata = json.loads(metadata_data)
                        metadata['compressed'] = True
                        metadata['file_size'] = zip_file.stat().st_size
                        backups.append(metadata)
                except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, OSError) as e:
                    logger.error("Failed to read metadata from %s: %s", zip_file, e, exc_info=True)

        except OSError as e:
            logger.error("Failed to list backups: %s", e, exc_info=True)

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return backups
