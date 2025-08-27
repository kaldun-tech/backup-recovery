# Testing Procedures

Simple testing approach to verify backup functionality.

## Basic Testing

### Test Backup Operation
```bash
# Run a test backup with verbose output
python backup_orchestrator.py --profile test --verbose

# Check if backup completed successfully
echo $?  # Should return 0 for success
```

### Verify Configuration
```bash
# Test mode - validates config without actual backup
python backup_orchestrator.py --profile production --test
```

### Check Backup Results
```bash
# View backup summary
ls ~/.backup-recovery/summaries/
cat ~/.backup-recovery/summaries/backup-YYYYMMDD-HHMMSS-summary.json

# Check logs for errors
tail ~/.backup-recovery/logs/orchestrator.log
```

## Restore Testing

### Manual Restore Verification
Since restore functionality is still in development, manually verify you can access your backed up files:

1. **AWS S3**: Use AWS CLI or console to download a few test files
2. **Local backups**: Check that files exist in your backup location
3. **Proton Drive**: Verify files are synced and accessible

### Simple Test Files
Create a small test directory to backup:
```bash
mkdir ~/backup-test
echo "test content $(date)" > ~/backup-test/test-file.txt
# Add this path to your backup profile for testing
```

## Automated Tests
```bash
# Run existing test suite
python -m pytest tests/ -v
```

## Troubleshooting Failed Tests
1. Check configuration file syntax
2. Verify credentials are set up correctly
3. Ensure target directories exist and are writable
4. Check network connectivity for cloud backups