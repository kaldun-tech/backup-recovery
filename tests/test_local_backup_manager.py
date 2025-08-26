#!/usr/bin/env python3
"""
Tests for LocalBackupManager
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.local_backup_manager import LocalBackupManager


@pytest.fixture
def temp_backup_dir():
    """Create a temporary backup directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_files():
    """Create temporary test files"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create test files
    (temp_dir / 'file1.txt').write_text('content of file 1')
    (temp_dir / 'file2.txt').write_text('content of file 2')
    (temp_dir / 'subdir').mkdir()
    (temp_dir / 'subdir' / 'file3.txt').write_text('content of file 3')

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def backup_manager(temp_backup_dir):
    """Create a LocalBackupManager instance"""
    config = {
        'enabled': True,
        'backup_directory': str(temp_backup_dir),
        'compression': False,
        'encryption': False
    }
    return LocalBackupManager(config, 'test-backup-001')


class TestLocalBackupManager:
    """Test cases for LocalBackupManager"""

    def test_init(self, temp_backup_dir):
        """Test LocalBackupManager initialization"""
        config = {
            'enabled': True,
            'backup_directory': str(temp_backup_dir),
            'compression': True,
            'encryption': True
        }

        manager = LocalBackupManager(config, 'test-backup-001')

        assert manager.enabled is True
        assert manager.backup_dir == temp_backup_dir
        assert manager.compression is True
        assert manager.encryption is True
        assert manager.backup_id == 'test-backup-001'
        assert temp_backup_dir.exists()

    def test_init_disabled(self, temp_backup_dir):
        """Test LocalBackupManager with disabled configuration"""
        config = {
            'enabled': False,
            'backup_directory': str(temp_backup_dir)
        }

        manager = LocalBackupManager(config, 'test-backup-001')
        assert manager.enabled is False

    def test_backup_files_disabled(self, temp_backup_dir, test_files):
        """Test backup with disabled manager"""
        config = {
            'enabled': False,
            'backup_directory': str(temp_backup_dir)
        }

        manager = LocalBackupManager(config, 'test-backup-001')
        files = list(test_files.glob('*.txt'))

        result = manager.backup_files(files, 'test-profile')
        assert result is True  # Should succeed but do nothing

    def test_backup_files_success(self, backup_manager, test_files):
        """Test successful file backup"""
        files = [
            test_files / 'file1.txt',
            test_files / 'file2.txt'
        ]

        result = backup_manager.backup_files(files, 'test-profile')

        assert result is True

        # Check backup directory structure
        backup_path = backup_manager.backup_dir / backup_manager.backup_id
        assert backup_path.exists()

        # Check metadata file
        metadata_file = backup_path / 'backup-metadata.json'
        assert metadata_file.exists()

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        assert metadata['backup_id'] == backup_manager.backup_id
        assert metadata['profile'] == 'test-profile'
        assert metadata['files_count'] == 2
        assert len(metadata['files']) == 2

        # Check that files were copied
        for file_info in metadata['files']:
            dest_path = Path(file_info['destination'])
            assert dest_path.exists()
            assert file_info['status'] == 'success'

    def test_backup_nonexistent_files(self, backup_manager):
        """Test backup of non-existent files"""
        files = [
            Path('/nonexistent/file1.txt'),
            Path('/nonexistent/file2.txt')
        ]

        result = backup_manager.backup_files(files, 'test-profile')

        # Should return False as no files were successfully backed up
        assert result is False

        # Check metadata file exists and contains error information
        backup_path = backup_manager.backup_dir / backup_manager.backup_id
        metadata_file = backup_path / 'backup-metadata.json'

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # All files should have failed status
            for file_info in metadata['files']:
                assert file_info['status'] == 'failed'
                assert 'error' in file_info

    def test_backup_mixed_success_failure(self, backup_manager, test_files):
        """Test backup with mix of existing and non-existent files"""
        files = [
            test_files / 'file1.txt',  # Exists
            Path('/nonexistent/file.txt'),  # Does not exist
            test_files / 'file2.txt'   # Exists
        ]

        result = backup_manager.backup_files(files, 'test-profile')

        # Should return True as some files were successfully backed up
        assert result is True

        # Check metadata
        backup_path = backup_manager.backup_dir / backup_manager.backup_id
        metadata_file = backup_path / 'backup-metadata.json'

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        success_count = sum(1 for f in metadata['files'] if f['status'] == 'success')
        failure_count = sum(1 for f in metadata['files'] if f['status'] == 'failed')

        assert success_count == 2
        assert failure_count == 1

    def test_restore_files_disabled(self, temp_backup_dir):
        """Test restore with disabled manager"""
        config = {
            'enabled': False,
            'backup_directory': str(temp_backup_dir)
        }

        manager = LocalBackupManager(config, 'test-backup-001')

        result = manager.restore_files('test-backup-001', Path('/tmp/restore'))
        assert result is True  # Should succeed but do nothing

    def test_restore_files_missing_backup(self, backup_manager):
        """Test restore from non-existent backup"""
        result = backup_manager.restore_files('nonexistent-backup', Path('/tmp/restore'))
        assert result is False

    def test_restore_files_success(self, backup_manager, test_files):
        """Test successful file restore"""
        # First, create a backup
        files = [test_files / 'file1.txt', test_files / 'file2.txt']
        backup_result = backup_manager.backup_files(files, 'test-profile')
        assert backup_result is True

        # Now restore to a different location
        restore_dir = Path(tempfile.mkdtemp())

        try:
            result = backup_manager.restore_files(backup_manager.backup_id, restore_dir)
            assert result is True

            # Check restored files
            restored_files = list(restore_dir.glob('*.txt'))
            assert len(restored_files) == 2

            file_names = [f.name for f in restored_files]
            assert 'file1.txt' in file_names
            assert 'file2.txt' in file_names

            # Check file contents
            for restored_file in restored_files:
                if restored_file.name == 'file1.txt':
                    assert restored_file.read_text() == 'content of file 1'
                elif restored_file.name == 'file2.txt':
                    assert restored_file.read_text() == 'content of file 2'

        finally:
            # Cleanup restore directory
            shutil.rmtree(restore_dir)

    def test_list_backups_empty(self, backup_manager):
        """Test listing backups when none exist"""
        backups = backup_manager.list_backups()
        assert backups == []

    def test_list_backups_with_data(self, backup_manager, test_files):
        """Test listing backups after creating some"""
        # Create first backup
        files1 = [test_files / 'file1.txt']
        backup_manager.backup_files(files1, 'profile1')

        # Create second backup with different ID
        backup_manager2 = LocalBackupManager(
            backup_manager.config,
            'test-backup-002'
        )
        files2 = [test_files / 'file2.txt']
        backup_manager2.backup_files(files2, 'profile2')

        # List backups
        backups = backup_manager.list_backups()

        assert len(backups) == 2

        backup_ids = [b['backup_id'] for b in backups]
        assert 'test-backup-001' in backup_ids
        assert 'test-backup-002' in backup_ids

        profiles = [b['profile'] for b in backups]
        assert 'profile1' in profiles
        assert 'profile2' in profiles

    def test_backup_creates_directory_structure(self, backup_manager, test_files):
        """Test that backup preserves directory structure"""
        # Include file from subdirectory
        files = [
            test_files / 'file1.txt',
            test_files / 'subdir' / 'file3.txt'
        ]

        result = backup_manager.backup_files(files, 'test-profile')
        assert result is True

        # Check that subdirectory structure is preserved
        backup_path = backup_manager.backup_dir / backup_manager.backup_id

        # Check metadata for correct destination paths
        metadata_file = backup_path / 'backup-metadata.json'
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Should have preserved the relative path structure
        destinations = [f['destination'] for f in metadata['files']]
        assert any('file1.txt' in dest for dest in destinations)
        assert any('subdir' in dest and 'file3.txt' in dest for dest in destinations)
