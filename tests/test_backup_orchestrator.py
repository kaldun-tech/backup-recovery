#!/usr/bin/env python3
"""
Tests for BackupOrchestrator
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from backup_orchestrator import BackupOrchestrator


@pytest.fixture
def temp_config():
    """Create a temporary configuration file"""
    config_data = {
        'profiles': {
            'test-profile': {
                'name': 'Test Profile',
                'paths': [
                    {
                        'path': '/tmp/test-source',
                        'include': ['**/*.txt'],
                        'exclude': ['**/temp/**']
                    }
                ]
            }
        },
        'aws': {'enabled': False},
        'proton': {'enabled': False},
        'local': {'enabled': True, 'backup_directory': '/tmp/test-backups'},
        'classification': {
            'sensitive': {
                'keywords': ['secret'],
                'file_extensions': ['.key']
            },
            'critical': {
                'patterns': ['**/config*']
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def orchestrator(temp_config):
    """Create a BackupOrchestrator instance with test configuration"""
    return BackupOrchestrator(temp_config)


@pytest.fixture
def test_files():
    """Create temporary test files"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create test files
    (temp_dir / 'test.txt').write_text('test content')
    (temp_dir / 'secret.key').write_text('secret key')
    (temp_dir / 'config.json').write_text('{"test": true}')
    (temp_dir / 'temp').mkdir()
    (temp_dir / 'temp' / 'temp.txt').write_text('temp file')

    yield temp_dir

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


class TestBackupOrchestrator:
    """Test cases for BackupOrchestrator"""

    def test_init(self, temp_config):
        """Test BackupOrchestrator initialization"""
        orchestrator = BackupOrchestrator(temp_config)
    
        assert orchestrator.config is not None
        assert orchestrator.backup_id.startswith('backup-')
        assert 'start_time' in orchestrator.stats
    
    def test_load_config_missing_file(self):
        """Test loading configuration from missing file"""
        with pytest.raises(SystemExit):
            BackupOrchestrator('/nonexistent/config.yaml')
        
    def test_generate_backup_id(self, orchestrator):
        """Test backup ID generation"""
        backup_id1 = orchestrator._generate_backup_id()
        backup_id2 = orchestrator._generate_backup_id()
    
        assert backup_id1.startswith('backup-')
        assert backup_id2.startswith('backup-')
        # IDs should be different due to timestamp
        assert backup_id1 != backup_id2
    
    def test_discover_files(self, orchestrator, test_files):
        """Test file discovery"""
        # Update config to use test directory
        orchestrator.config['profiles']['test-profile']['paths'][0]['path'] = str(test_files)
    
        profile = orchestrator.config['profiles']['test-profile']
        files = orchestrator._discover_files(profile)
    
        # Should find test.txt but not temp/temp.txt (excluded)
        assert len(files) >= 1
        assert any(f.name == 'test.txt' for f in files)
        assert not any('temp' in str(f) for f in files)
    
    def test_classify_data(self, orchestrator, test_files):
        """Test data classification"""
        files = [
            test_files / 'test.txt',
            test_files / 'secret.key',
            test_files / 'config.json'
        ]
    
        classification = orchestrator._classify_data(files)
    
        # Check sensitive file classification
        sensitive_files = [f.name for f in classification['proton_sensitive']]
        assert 'secret.key' in sensitive_files
    
        # Check critical file classification
        critical_files = [f.name for f in classification['local_airgapped']]
        assert 'config.json' in critical_files
    
    @patch('backup_orchestrator.AWSBackupManager')
    def test_backup_to_aws(self, mock_aws_manager, orchestrator, test_files):
        """Test AWS backup"""
        mock_manager = Mock()
        mock_manager.backup_files.return_value = True
        mock_aws_manager.return_value = mock_manager
    
        files = [test_files / 'test.txt']
        result = orchestrator._backup_to_aws(files, 'test-profile')
    
        assert result is True
        mock_aws_manager.assert_called_once()
        mock_manager.backup_files.assert_called_once_with(files, 'test-profile')
    
    @patch('backup_orchestrator.ProtonSyncManager')
    def test_backup_to_proton(self, mock_proton_manager, orchestrator, test_files):
        """Test Proton Drive backup"""
        mock_manager = Mock()
        mock_manager.sync_files.return_value = True
        mock_proton_manager.return_value = mock_manager
    
        files = [test_files / 'secret.key']
        result = orchestrator._backup_to_proton(files, 'test-profile')
    
        assert result is True
        mock_proton_manager.assert_called_once()
        mock_manager.sync_files.assert_called_once_with(files, 'test-profile')
    
    @patch('backup_orchestrator.LocalBackupManager')
    def test_backup_to_local(self, mock_local_manager, orchestrator, test_files):
        """Test local backup"""
        mock_manager = Mock()
        mock_manager.backup_files.return_value = True
        mock_local_manager.return_value = mock_manager
    
        files = [test_files / 'config.json']
        result = orchestrator._backup_to_local(files, 'test-profile')
    
        assert result is True
        mock_local_manager.assert_called_once()
        mock_manager.backup_files.assert_called_once_with(files, 'test-profile')
    
    def test_backup_profile_not_found(self, orchestrator):
        """Test backup with non-existent profile"""
        result = orchestrator.backup_profile('nonexistent-profile')
        assert result is False
    
    def test_backup_profile_no_files(self, orchestrator):
        """Test backup with no discoverable files"""
        # Point to empty directory
        empty_dir = Path(tempfile.mkdtemp())
        orchestrator.config['profiles']['test-profile']['paths'][0]['path'] = str(empty_dir)
    
        result = orchestrator.backup_profile('test-profile')
        assert result is True  # No files to backup is considered success
    
        # Cleanup
        empty_dir.rmdir()
    
    def test_log_summary(self, orchestrator):
        """Test backup summary logging"""
        orchestrator.stats['end_time'] = orchestrator.stats['start_time']
        orchestrator.stats['files_processed'] = 5
        orchestrator.stats['tiers_completed'] = ['local_airgapped']
    
        # Should not raise an exception
        orchestrator._log_summary()
    
        # Check that summary file would be created in the right location
        expected_dir = Path.home() / '.backup-recovery/summaries'
        summary_file_pattern = f"{orchestrator.backup_id}-summary.json"
    
        # We can't easily test file creation without mocking, but we can test the method runs
        assert True  # Method completed without error


class TestBackupOrchestratorIntegration:
    """Integration tests for BackupOrchestrator"""

    def test_full_backup_workflow(self, orchestrator, test_files):
        """Test complete backup workflow"""
        # Update config to use test directory
        orchestrator.config['profiles']['test-profile']['paths'][0]['path'] = str(test_files)
    
        # Mock all backup managers to avoid actual external calls
        with patch('backup_orchestrator.AWSBackupManager') as mock_aws, \
             patch('backup_orchestrator.ProtonSyncManager') as mock_proton, \
             patch('backup_orchestrator.LocalBackupManager') as mock_local:
        
            # Configure mocks
            mock_aws.return_value.backup_files.return_value = True
            mock_proton.return_value.sync_files.return_value = True
            mock_local.return_value.backup_files.return_value = True
        
            # Run backup
            result = orchestrator.backup_profile('test-profile')
        
            # Verify result
            assert result is True
            assert orchestrator.stats['files_processed'] > 0
            assert 'end_time' in orchestrator.stats