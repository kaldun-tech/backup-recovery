# Implementation Strategy

Simple backup approach using multiple storage locations for redundancy.

## Basic Concept

Following a simplified 3-2-1 strategy:
- **3 copies** of important data
- **2 different storage types** (cloud + local)
- **1 offsite** backup

## Storage Tiers

### AWS S3 - Primary Cloud Storage
- Most files go here by default
- Cost-effective for bulk storage
- Built-in durability and availability

### Proton Drive - Sensitive Data
- Files with sensitive content (based on keywords/file types)
- End-to-end encrypted
- Limited to important sensitive files only

### Local Storage - Critical Files
- Important files also backed up locally
- External drive or local directory
- Air-gapped from internet threats

## Implementation Approach

1. **Start simple**: Get AWS backups working first
2. **Add classification**: Route sensitive files to Proton Drive
3. **Add local backups**: Copy critical files locally
4. **Test restore**: Verify you can get your files back

## Data Classification

Files are automatically routed based on:
- **Sensitive keywords** in filename/path → Proton Drive
- **Critical patterns** → AWS + Local (redundant)  
- **Everything else** → AWS only

## Configuration

Set up your backup profiles in `~/.backup-recovery/config.yaml` with:
- Paths to backup
- Classification rules
- Storage credentials

Keep it simple - start with basic functionality and add complexity only as needed.