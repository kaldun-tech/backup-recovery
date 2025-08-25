# Backup Automation Scripts

## Overview

Automation scripts implementing the hybrid 3-2-1-1-0 backup strategy with tiered storage optimization.

## Scripts

### Core Backup Operations
- `backup-orchestrator.py` - Main backup coordination and scheduling
- `aws-backup-manager.py` - AWS S3/Glacier operations and lifecycle management
- `proton-sync-manager.py` - Proton Drive selective synchronization
- `local-backup-manager.py` - External HDD and air-gapped storage

### Monitoring and Verification  
- `backup-verifier.py` - Automated backup integrity verification
- `cost-optimizer.py` - Storage cost analysis and optimization
- `health-checker.py` - System health monitoring and alerting
- `recovery-tester.py` - Automated disaster recovery testing

### Utilities
- `data-classifier.py` - Intelligent data classification and routing
- `retention-manager.py` - Automated retention policy enforcement  
- `encryption-manager.py` - Cross-platform encryption key management
- `notification-handler.py` - Multi-channel alert management

## Usage Examples

### Daily Backup Execution
```bash
# Run complete backup cycle
python backup-orchestrator.py --profile production

# AWS tier only
python aws-backup-manager.py --incremental

# Sensitive data sync
python proton-sync-manager.py --selective
```

### Recovery Operations
```bash
# List available backups
python backup-orchestrator.py --list-backups --all-tiers

# Emergency recovery
python backup-orchestrator.py --emergency-restore --backup-id latest

# Selective file recovery
python recovery-tester.py --restore-file /path/to/file --source aws-tier
```

### Monitoring and Maintenance
```bash
# System health check  
python health-checker.py --comprehensive

# Cost analysis
python cost-optimizer.py --report --month current

# Verify backup integrity
python backup-verifier.py --deep-check --tier all
```

## Configuration

Scripts use configuration from:
- `../configs/backup-profiles.yaml` - Backup profile definitions
- `~/.backup-recovery/config.yaml` - User-specific settings  
- Environment variables for sensitive credentials

## Requirements

See `requirements.txt` for Python dependencies. Key libraries:
- `boto3` - AWS SDK
- `cryptography` - Encryption operations
- `schedule` - Task scheduling
- `psutil` - System monitoring
- `pyyaml` - Configuration parsing