# Backup Automation Scripts

## Overview

Automation scripts implementing the hybrid 3-2-1-1-0 backup strategy with tiered storage optimization.

## Scripts

### Core Backup Operations
- `backup_orchestrator.py` - Main backup coordination and scheduling
- `aws_backup_manager.py` - AWS S3/Glacier operations and lifecycle management
- `proton_sync_manager.py` - Proton Drive selective synchronization
- `local_backup_manager.py` - External HDD and air-gapped storage

## Usage Examples

### Daily Backup Execution
```bash
# Run complete backup cycle
python backup_orchestrator.py --profile production

# AWS tier only
python aws_backup_manager.py --incremental

# Sensitive data sync
python proton_sync_manager.py --selective
```

### Recovery Operations
```bash
# List available backups
python backup_orchestrator.py --list-backups --all-tiers

# Emergency recovery
python backup_orchestrator.py --emergency-restore --backup-id latest
```

## Configuration

Scripts use configuration from:
- `../configs/simple-backup.yaml` - Backup profile template (copy and customize)
- `../configs/local/` - User-specific personal configurations (Git-ignored)
- `~/.backup-recovery/config.yaml` - User-specific settings
- Environment variables for sensitive credentials

**Note**: Store your personal backup configurations in `../configs/local/` to keep them out of version control.

## Requirements

See `requirements.txt` for Python dependencies. Key libraries:
- `boto3` - AWS SDK
- `cryptography` - Encryption operations
- `schedule` - Task scheduling
- `psutil` - System monitoring
- `pyyaml` - Configuration parsing