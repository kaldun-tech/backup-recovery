# Backup Configurations

This directory contains backup configuration templates and examples for the backup-recovery tool.

## Configuration Files

- **simple-backup.yaml** - A well-documented template for backing up Documents and Pictures to an external drive. Start here if you're new to the tool.
- **test-config.yaml** - Test configuration used for development and CI/CD testing.

## Using Configurations

### 1. Start with a Template

Copy one of the template files and customize it:

```bash
cp simple-backup.yaml my-backup-config.yaml
```

### 2. Edit Your Configuration

Open your new config file and update:
- **paths**: Point to the directories you want to backup
- **backup_directory**: Point to your external drive or cloud storage
- **storage backend**: Choose local, AWS, or Proton (and enable only one)

### 3. Run Your Backup

```bash
backup-recovery --config my-backup-config.yaml
```

## Personal Configurations

**Important**: Do NOT commit personal or machine-specific configurations to Git.

Store your personal configs in the `local/` folder, which is ignored by Git:

```bash
cp simple-backup.yaml local/my-laptop-backup.yaml
# Edit local/my-laptop-backup.yaml with your personal paths
```

This way your configs stay on your local machine and won't accidentally be committed or exposed when you open source the project.

## Configuration Guide

### Paths Section

- `path`: Directory to backup (supports `$HOME` variable expansion)
- `include`: Glob patterns of files to backup (e.g., `**/*.pdf`)
- `exclude`: Glob patterns to skip (takes precedence over include)

### Storage Backends

Only enable ONE storage backend:

- **local**: Backup to an external drive or NAS
  - Update `backup_directory` to your drive path
  - `compression`: Reduces file size (slower backup)
  - `encryption`: Encrypts backups locally (recommended for sensitive data)

- **aws**: Backup to Amazon S3
  - Requires AWS credentials in `~/.aws/credentials`
  - Supports multiple regions and storage classes (e.g., Glacier for cost savings)

- **proton**: Backup to Proton Drive
  - Requires Proton account credentials

### File Classification (Optional)

Tag files as `sensitive` or `critical` for special handling:
- Sensitive files get encrypted automatically
- Critical files are always backed up and verified
- Leave empty `{}` if you don't need this feature

## Examples

### Backup important documents to external drive

```yaml
profiles:
  important-docs:
    name: "Important Documents"
    paths:
      - path: "$HOME/Documents/Important"
        include:
          - "**/*"
        exclude:
          - "**/.*"
          - "**/temp/**"

local:
  enabled: true
  backup_directory: "/mnt/d"  # Windows E: drive on WSL
  compression: true
  encryption: true
```

### Backup photos to AWS Glacier (cost-effective)

```yaml
profiles:
  photo-archive:
    name: "Photo Archive"
    paths:
      - path: "$HOME/Pictures"
        include:
          - "**/*.jpg"
          - "**/*.png"
          - "**/*.mp4"

aws:
  enabled: true
  bucket: "my-photo-backup"
  storage_class: "GLACIER"
```

## Platform-Specific Paths

### Linux

```yaml
path: "/home/username/Documents"
backup_directory: "/mnt/external"
```

### macOS

```yaml
path: "/Users/username/Documents"
backup_directory: "/Volumes/MyDrive"
```

### Windows (WSL)

```yaml
path: "/mnt/c/Users/username/Documents"  # C: drive
backup_directory: "/mnt/d"                # D: drive
```

## Troubleshooting

- **Files not being backed up?** Check `exclude` patterns - they take precedence
- **Backup directory not found?** Verify the mount path and that the drive is connected
- **AWS backup failing?** Ensure AWS credentials are configured and the bucket exists
