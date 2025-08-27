# Configuration Guide

Simple setup guide for the backup system.

## Basic Concept

The system backs up your files to multiple locations:
- **AWS S3** - Primary cloud storage for most files
- **Proton Drive** - Encrypted storage for sensitive files  
- **Local storage** - External drive or local directory for important files

## Storage Options

### AWS S3
- Most files go here by default
- Cost-effective cloud storage
- Built-in durability

### Proton Drive  
- Files with sensitive keywords/extensions
- End-to-end encrypted
- Limited to important sensitive files

### Local Storage
- Critical files also stored locally
- External drive or local directory
- Offline protection

## Configuration

Create your backup configuration file at `~/.backup-recovery/config.yaml`:

### Basic Configuration Example

```yaml
profiles:
  my-documents:
    name: "Personal Documents"
    paths:
      - path: "$HOME/Documents"
        include: ["**/*.pdf", "**/*.docx", "**/*.txt"]
        exclude: ["**/temp/**", "**/.DS_Store"]

aws:
  enabled: true
  region: "us-east-1" 
  bucket: "your-backup-bucket-name"

proton:
  enabled: false  # Set to true when ready

local:
  enabled: true
  backup_directory: "/path/to/external/drive/backups"

classification:
  sensitive:
    keywords: ["password", "financial", "tax", "medical"]
    file_extensions: [".key", ".pem", ".p12"]
  critical:
    patterns: ["**/Documents/Important/**", "**/Pictures/Family/**"]
```

## Running Backups

```bash
# Run backup with your profile
python backup_orchestrator.py --profile my-documents

# Test mode (no actual backup)
python backup_orchestrator.py --profile my-documents --test

# Verbose output for debugging
python backup_orchestrator.py --profile my-documents --verbose
```

## AWS Setup

1. Create an S3 bucket for your backups
2. Configure AWS credentials:
   ```bash
   aws configure
   ```
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID="your-key"
   export AWS_SECRET_ACCESS_KEY="your-secret"
   ```

## Local Storage Setup

For local backups, ensure your target directory exists:
```bash
mkdir -p /path/to/external/drive/backups
```

## Troubleshooting

### Common Issues

**Configuration file not found**
- Ensure `~/.backup-recovery/config.yaml` exists
- Check file permissions

**AWS credentials not configured**  
- Run `aws configure` or set environment variables
- Verify S3 bucket exists and is accessible

**Local backup directory not found**
- Create the directory: `mkdir -p /path/to/backup/directory`
- Ensure you have write permissions

## Checking Results

View backup summaries:
```bash
ls ~/.backup-recovery/summaries/
cat ~/.backup-recovery/summaries/backup-YYYYMMDD-HHMMSS-summary.json
```

Check logs:
```bash
tail ~/.backup-recovery/logs/orchestrator.log
```

Start simple with basic functionality, then expand as needed.