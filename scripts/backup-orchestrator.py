#!/usr/bin/env python3
"""
Backup Orchestrator - Main backup coordination and scheduling
Adapted from AWS POC disaster recovery patterns for hybrid 3-2-1-1-0 strategy
"""

import json
import logging
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path.home() / '.backup-recovery/logs/orchestrator.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class BackupOrchestrator:
    """Main backup orchestration class implementing hybrid tiered strategy"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path.home() / '.backup-recovery/config.yaml')
        self.config = self._load_config()
        self.backup_id = self._generate_backup_id()
        self.stats = {
            'start_time': datetime.now(timezone.utc),
            'files_processed': 0,
            'files_failed': 0,
            'total_size': 0,
            'compressed_size': 0,
            'tiers_completed': []
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate backup configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ['profiles', 'aws', 'proton', 'local']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Missing required configuration section: {section}")
                    
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Configuration file parsing error: {e}")
            sys.exit(1)
            
    def _generate_backup_id(self) -> str:
        """Generate unique backup identifier"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        return f"backup-{timestamp}"
        
    def _discover_files(self, profile: Dict[str, Any]) -> List[Path]:
        """Discover files based on profile configuration"""
        discovered_files = []
        
        for path_config in profile.get('paths', []):
            base_path = Path(os.path.expandvars(path_config['path']))
            
            if not base_path.exists():
                logger.warning(f"Path does not exist: {base_path}")
                continue
                
            # Handle include patterns
            include_patterns = path_config.get('include', ['**/*'])
            exclude_patterns = path_config.get('exclude', [])
            
            for pattern in include_patterns:
                for file_path in base_path.glob(pattern):
                    if file_path.is_file():
                        # Check exclude patterns
                        excluded = any(file_path.match(excl) for excl in exclude_patterns)
                        if not excluded:
                            discovered_files.append(file_path)
                            
        logger.info(f"Discovered {len(discovered_files)} files for backup")
        return discovered_files
        
    def _classify_data(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Classify files into appropriate backup tiers"""
        classification = {
            'aws_primary': [],
            'proton_sensitive': [],
            'local_airgapped': []
        }
        
        # Load classification rules
        rules = self.config.get('classification', {})
        sensitive_keywords = rules.get('sensitive', {}).get('keywords', [])
        sensitive_extensions = rules.get('sensitive', {}).get('file_extensions', [])
        critical_patterns = rules.get('critical', {}).get('patterns', [])
        
        for file_path in files:
            file_str = str(file_path).lower()
            file_suffix = file_path.suffix.lower()
            
            # Check if sensitive
            is_sensitive = (
                any(keyword in file_str for keyword in sensitive_keywords) or
                file_suffix in sensitive_extensions
            )
            
            # Check if critical
            is_critical = any(
                file_path.match(pattern) for pattern in critical_patterns
            )
            
            if is_sensitive:
                classification['proton_sensitive'].append(file_path)
            
            # Critical files go to both AWS and local
            if is_critical:
                classification['aws_primary'].append(file_path)
                classification['local_airgapped'].append(file_path)
            else:
                # Default to AWS primary for non-sensitive, non-critical files
                if not is_sensitive:
                    classification['aws_primary'].append(file_path)
                    
        logger.info(f"File classification: AWS={len(classification['aws_primary'])}, "
                   f"Proton={len(classification['proton_sensitive'])}, "
                   f"Local={len(classification['local_airgapped'])}")
        
        return classification
        
    def _backup_to_aws(self, files: List[Path], profile: str) -> bool:
        """Execute AWS S3/Glacier backup"""
        try:
            logger.info(f"Starting AWS backup for {len(files)} files")
            
            # Import AWS backup manager
            from aws_backup_manager import AWSBackupManager
            
            aws_manager = AWSBackupManager(
                self.config['aws'],
                backup_id=self.backup_id
            )
            
            success = aws_manager.backup_files(files, profile)
            
            if success:
                self.stats['tiers_completed'].append('aws_primary')
                logger.info("AWS backup completed successfully")
            else:
                logger.error("AWS backup failed")
                
            return success
            
        except Exception as e:
            logger.error(f"AWS backup error: {e}")
            return False
            
    def _backup_to_proton(self, files: List[Path], profile: str) -> bool:
        """Execute Proton Drive backup for sensitive data"""
        try:
            logger.info(f"Starting Proton backup for {len(files)} sensitive files")
            
            # Import Proton sync manager
            from proton_sync_manager import ProtonSyncManager
            
            proton_manager = ProtonSyncManager(
                self.config['proton'],
                backup_id=self.backup_id
            )
            
            success = proton_manager.sync_files(files, profile)
            
            if success:
                self.stats['tiers_completed'].append('proton_sensitive')
                logger.info("Proton backup completed successfully")
            else:
                logger.error("Proton backup failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Proton backup error: {e}")
            return False
            
    def _backup_to_local(self, files: List[Path], profile: str) -> bool:
        """Execute local air-gapped backup"""
        try:
            logger.info(f"Starting local backup for {len(files)} critical files")
            
            # Import local backup manager
            from local_backup_manager import LocalBackupManager
            
            local_manager = LocalBackupManager(
                self.config['local'],
                backup_id=self.backup_id
            )
            
            success = local_manager.backup_files(files, profile)
            
            if success:
                self.stats['tiers_completed'].append('local_airgapped')
                logger.info("Local backup completed successfully")
            else:
                logger.error("Local backup failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Local backup error: {e}")
            return False
            
    def backup_profile(self, profile_name: str) -> bool:
        """Execute backup for specified profile"""
        logger.info(f"Starting backup for profile: {profile_name}")
        
        if profile_name not in self.config['profiles']:
            logger.error(f"Profile not found: {profile_name}")
            return False
            
        profile = self.config['profiles'][profile_name]
        
        # Discover files
        files = self._discover_files(profile)
        if not files:
            logger.warning("No files discovered for backup")
            return True
            
        # Classify files into tiers
        classified_files = self._classify_data(files)
        
        # Execute backups for each tier
        results = []
        
        if classified_files['aws_primary']:
            results.append(self._backup_to_aws(
                classified_files['aws_primary'], 
                profile_name
            ))
            
        if classified_files['proton_sensitive']:
            results.append(self._backup_to_proton(
                classified_files['proton_sensitive'], 
                profile_name
            ))
            
        if classified_files['local_airgapped']:
            results.append(self._backup_to_local(
                classified_files['local_airgapped'], 
                profile_name
            ))
            
        # Update statistics
        self.stats['end_time'] = datetime.now(timezone.utc)
        self.stats['files_processed'] = len(files)
        
        success = all(results) if results else False
        
        logger.info(f"Backup completed. Success: {success}")
        self._log_summary()
        
        return success
        
    def _log_summary(self):
        """Log backup operation summary"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        summary = {
            'backup_id': self.backup_id,
            'duration_seconds': duration,
            'files_processed': self.stats['files_processed'],
            'files_failed': self.stats['files_failed'],
            'tiers_completed': self.stats['tiers_completed'],
            'timestamp': self.stats['end_time'].isoformat()
        }
        
        logger.info(f"Backup Summary: {json.dumps(summary, indent=2)}")
        
        # Save summary to file
        summary_dir = Path.home() / '.backup-recovery/summaries'
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = summary_dir / f"{self.backup_id}-summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Backup Recovery Suite Orchestrator')
    parser.add_argument('--profile', required=True, help='Backup profile name')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test', action='store_true', help='Test mode (no actual backup)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        orchestrator = BackupOrchestrator(args.config)
        
        if args.test:
            logger.info("Test mode - no actual backup will be performed")
            return 0
            
        success = orchestrator.backup_profile(args.profile)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Backup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())