# Backup Recovery Suite - Configuration Guide

This guide walks you through setting up your backup strategy, organizing your data, and configuring the system for your specific needs.

## Quick Reference

- **Start here if**: You want to get backing up immediately
- **Skip to**: [Quick Setup](#quick-setup) 
- **Come back to**: Data organization and optimization later

## Data Organization Strategy

### Understanding the 3-2-1-1-0 Strategy

Our system implements an enhanced backup strategy:
- **3** copies of your data (original + 2 backups)
- **2** different storage media (cloud + physical drives)  
- **1** offsite backup (cloud storage)
- **1** offline backup (air-gapped storage)
- **0** errors after verification

### Data Classification Tiers

#### Tier 1: AWS S3 (Primary Cloud Storage)
**Best for**: General documents, work files, photos
- Automatic lifecycle management
- Cross-region replication available
- Cost-effective for bulk storage

#### Tier 2: Proton Drive (Sensitive Data)
**Best for**: Passwords, financial data, medical records, private communications
- End-to-end encryption
- Zero-access architecture
- Currently requires third-party tools (rclone)

#### Tier 3: Air-Gapped Local (Critical Data)
**Best for**: Irreplaceable files, financial records, family photos
- Complete network isolation when offline
- Ransomware protection
- Physical control of your data

## AWS Storage Strategy

### Option 1: Intelligent Tiering (Recommended for Beginners)
```yaml
aws:
  storage_class: "INTELLIGENT_TIERING"
  lifecycle_enabled: false
```

**Pros**: Automatic cost optimization, simple setup
**Cons**: Small monitoring fee per object
**Best for**: Mixed access patterns, getting started

### Option 2: Direct to Glacier (Maximum Cost Savings)
```yaml
aws:
  storage_class: "GLACIER"
  retrieval_tier: "Expedited"  # 1-5 minutes, costs extra
```

**Pros**: Lowest storage cost ($0.0036/GB/month)
**Cons**: Retrieval fees, minimum 90-day commitment
**Best for**: True cold storage, rarely accessed data

### Option 3: Lifecycle Policies (Balanced Approach)
```yaml
aws:
  storage_class: "STANDARD"
  lifecycle:
    standard_ia_days: 30
    glacier_days: 90
    deep_archive_days: 365
```

**Pros**: Best cost optimization over time
**Cons**: More complex management
**Best for**: Long-term archival with predictable access patterns

## Data Organization Workflow

### Phase 1: Discovery and Audit (Week 1)

#### Find Your Large Files
```bash
# Find files larger than 100MB
find ~ -type f -size +100M 2>/dev/null | sort -h

# Get file type breakdown
find ~ -type f | grep -E '\.(pdf|docx|jpg|png|mp4|zip)$' | \
  sed 's/.*\.//' | sort | uniq -c | sort -nr
```

#### Calculate Storage Needs
```bash
# Total size by directory
du -sh ~/Documents ~/Pictures ~/Projects 2>/dev/null

# Identify largest directories  
du -h ~ 2>/dev/null | sort -hr | head -20
```

### Phase 2: Classification (Week 2)

Create a classification matrix for each file/directory:

| File/Directory | Can Recreate? | Losing It Hurts? | Contains PII? | Access Frequency | Classification |
|---------------|---------------|------------------|---------------|------------------|----------------|
| Family Photos | No | Yes | Maybe | Rare | Critical + Sensitive |
| Work Projects | Mostly | Yes | No | Daily | Important |
| Downloads | Yes | No | No | Never | Delete/Bulk |
| Financial Docs | No | Yes | Yes | Monthly | Critical + Sensitive |

### Phase 3: Staging and Testing (Week 3)

Start with a small, representative dataset:

1. **Pick one critical directory** (e.g., `~/Documents/Financial`)
2. **Test the full backup pipeline**
3. **Verify restore functionality**  
4. **Measure backup times and costs**
5. **Expand gradually**

## Hardware Requirements

### Air-Gapped Storage Setup

#### Recommended Drive Configuration
- **Minimum**: 2 external drives for rotation
- **Capacity**: 2-4TB each (depends on your data volume)
- **Type**: External SSDs for speed/durability, or HDDs for cost
- **Rotation**: Quarterly (Q1/Q3 = Drive A, Q2/Q4 = Drive B)

#### Physical Security
```
Drive A: Active backup drive (connected quarterly)
Drive B: Offsite storage (bank safe deposit box, trusted friend)
Drive C: (Optional) Annual archive drive (long-term cold storage)
```

#### Drive Preparation
```bash
# Format drive with encryption
sudo cryptsetup luksFormat /dev/sdX
sudo cryptsetup luksOpen /dev/sdX backup-drive

# Create filesystem
sudo mkfs.ext4 /dev/mapper/backup-drive

# Mount with proper permissions
sudo mkdir /mnt/backup-drive
sudo mount /dev/mapper/backup-drive /mnt/backup-drive
sudo chown $USER:$USER /mnt/backup-drive
```

## Configuration Templates

### Quick Setup (Start Here)

Copy the test configuration and customize:

```bash
cp configs/test-config.yaml configs/my-config.yaml
```

Edit the key sections:

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
  storage_class: "INTELLIGENT_TIERING"

local:
  enabled: true
  backup_directory: "/mnt/backup-drive/backups"
  encryption: true
```

### Advanced Configuration

For complex setups with multiple profiles:

```yaml
profiles:
  critical-files:
    tier: [1, 3]  # AWS + Air-gapped
    paths:
      - path: "$HOME/Documents/Financial"
      - path: "$HOME/Documents/Legal"
      - path: "$HOME/Pictures/Family"
    retention:
      daily: 30
      monthly: 84  # 7 years

  work-projects:
    tier: [1]  # AWS only
    paths:
      - path: "$HOME/Projects"
      - path: "$HOME/Documents/Work"
    retention:
      daily: 7
      weekly: 12

  sensitive-data:
    tier: [2]  # Proton Drive only
    paths:
      - path: "$HOME/.ssh"
      - path: "$HOME/Documents/Personal"
    encryption: "client-side"
    access_frequency: "rare"
```

## Migration Planning

### Existing Data Migration

#### Option 1: Gradual Migration
1. Start with most critical data (financial docs, family photos)
2. Add one category per week
3. Monitor costs and performance
4. Adjust configuration based on learnings

#### Option 2: Bulk Import
1. Organize all data first
2. Configure all profiles
3. Run initial backup during off-peak hours
4. Verify everything before deleting local copies

### Cost Estimation

#### AWS Costs (Monthly)
```
Storage: 1TB @ Intelligent Tiering = ~$23
Requests: 10,000 PUT requests = ~$0.05
Data Transfer: Minimal (uploads only) = ~$0

Total: ~$25/month for 1TB
```

#### Proton Drive Costs
```
Free: 1GB
Plus: 500GB for $3.99/month
Unlimited: 500GB for $7.99/month (includes other Proton services)
```

#### Hardware Costs (One-time)
```
2x 4TB External SSDs: ~$400-600
2x 4TB External HDDs: ~$200-300
Encryption software: Free (LUKS/VeraCrypt)
```

## Testing and Validation

### Initial Setup Testing

1. **Dry Run Mode**
   ```bash
   python backup-orchestrator.py --profile test --config my-config.yaml --test
   ```

2. **Small Dataset Test**
   ```bash
   mkdir ~/test-backup-data
   echo "test content" > ~/test-backup-data/test.txt
   # Update config to point to test directory
   # Run actual backup
   ```

3. **Restore Test**
   ```bash
   # Restore to different location
   # Compare restored files with originals
   # Verify file integrity
   ```

### Performance Benchmarking

Track these metrics during initial runs:
- **Backup duration** per GB
- **Network bandwidth** usage  
- **AWS costs** per backup
- **Drive space** utilization
- **Error rates** and retry frequency

## Troubleshooting

### Common Issues

#### "Configuration file not found"
```bash
# Check file exists and has correct permissions
ls -la configs/my-config.yaml
# Fix permissions if needed
chmod 644 configs/my-config.yaml
```

#### "AWS credentials not configured"
```bash
# Install AWS CLI and configure
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

#### "External drive not mounted"
```bash
# Check drive detection
lsblk
# Mount manually
sudo mount /dev/sdX1 /mnt/backup-drive
```

#### "Backup taking too long"
- Check network speed: `speedtest-cli`
- Reduce concurrent uploads in config
- Use compression for large text files
- Consider bandwidth throttling

### Performance Optimization

#### Network Optimization
```yaml
advanced:
  max_concurrent_uploads: 2  # Reduce if network is slow
  chunk_size_mb: 64  # Larger chunks for fast connections
  compression: true  # Enable for text files
  bandwidth_limit_mbps: 10  # Throttle if needed
```

#### Storage Optimization
```yaml
aws:
  multipart_threshold: 64  # MB, for large files
  multipart_chunksize: 8   # MB per chunk
  storage_class: "STANDARD_IA"  # If you access files monthly
```

## Security Considerations

### Encryption Strategy

#### Client-Side Encryption (Recommended)
- Encrypt before uploading to cloud
- You control the encryption keys
- Even cloud provider can't access your data

#### Cloud-Managed Encryption
- Easier to manage
- Cloud provider controls keys
- Good for non-sensitive data

### Key Management

#### For Air-Gapped Drives
```bash
# Generate strong encryption password
openssl rand -base64 32

# Store in password manager
# Never store alongside the encrypted drive
```

#### For Cloud Storage
```yaml
aws:
  encryption:
    type: "client-side"
    key_management: "local"  # vs "aws-kms"
    key_file: "/secure/path/to/encryption.key"
```

## Maintenance Schedule

### Daily
- Monitor backup success/failure notifications
- Check available disk space

### Weekly  
- Review backup logs for errors
- Verify recent backups completed successfully

### Monthly
- Test restore process with sample files
- Review AWS costs and optimize if needed
- Rotate air-gapped drives (if monthly rotation)

### Quarterly
- Full restore test of critical files
- Rotate air-gapped drives (recommended schedule)
- Review and update data classification
- Update software and dependencies

### Annually
- Complete disaster recovery test
- Review backup strategy effectiveness
- Update hardware (drive health checks)
- Archive old backups to deep storage

## Advanced Topics

### Automation and Scheduling

#### Using systemd (Linux)
```bash
# Create service file
sudo tee /etc/systemd/system/backup-recovery.service << EOF
[Unit]
Description=Backup Recovery Suite
After=network.target

[Service]
Type=oneshot
User=your-username
ExecStart=/path/to/.venv/bin/python /path/to/scripts/backup-orchestrator.py --profile production --config /path/to/config.yaml
EOF

# Create timer
sudo tee /etc/systemd/system/backup-recovery.timer << EOF
[Unit]
Description=Daily Backup
Requires=backup-recovery.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl enable backup-recovery.timer
sudo systemctl start backup-recovery.timer
```

#### Using cron
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/.venv/bin/python /path/to/scripts/backup-orchestrator.py --profile production --config /path/to/config.yaml
```

### Monitoring and Alerting

#### Email Notifications
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "app-password"
    recipients: ["admin@example.com"]
  failure_alerts: true
  success_summary: true
```

#### Metrics Collection
```yaml
monitoring:
  prometheus:
    enabled: true
    port: 9090
  log_level: "INFO"
  retention_days: 30
```

This guide should get you started with a robust backup strategy. Remember: start small, test thoroughly, and expand gradually!