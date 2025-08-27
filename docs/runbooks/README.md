# Troubleshooting Guide

Basic troubleshooting and restore procedures for the backup system.

## Common Issues

### Backup Failed
1. Check logs: `~/.backup-recovery/logs/orchestrator.log`
2. Verify configuration: `~/.backup-recovery/config.yaml`
3. Ensure target directories/credentials are accessible
4. Run with `--verbose` flag for detailed output

### AWS Connection Issues
- Verify AWS credentials are configured
- Check internet connectivity
- Ensure S3 bucket exists and has proper permissions

### Local Backup Issues
- Verify external drive is mounted
- Check available disk space
- Ensure backup target directory exists

## Restore Procedures

### List Available Backups
```bash
# Check backup summaries
ls ~/.backup-recovery/summaries/

# View specific backup details
cat ~/.backup-recovery/summaries/backup-20240101-120000-summary.json
```

### Restore from AWS (Placeholder)
```bash
# This functionality is not yet implemented
python backup_orchestrator.py --restore --backup-id backup-20240101-120000 --source aws
```

### Manual Recovery
For now, restore operations need to be done manually using the AWS CLI or console, as the restore functionality is still in development.

## Log Locations
- Main logs: `~/.backup-recovery/logs/orchestrator.log`
- Backup summaries: `~/.backup-recovery/summaries/`
- Configuration: `~/.backup-recovery/config.yaml`