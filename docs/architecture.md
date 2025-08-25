# Architecture Overview

## System Design

The Backup Recovery Suite implements a hybrid 3-2-1-1-0 backup strategy with tiered storage optimization:
- **3 copies** of critical data
- **2 different media types** (cloud + local)  
- **1 offsite copy** (geographic distribution)
- **1 air-gapped copy** (ransomware protection)
- **0 recovery failures** (verified backups)

## Components

### Core Engine
- **Backup Manager**: Orchestrates backup operations
- **Recovery Manager**: Handles restore and recovery processes  
- **Storage Abstraction Layer**: Unified interface for all storage backends
- **Scheduler**: Manages automated backup jobs

### Storage Backends (Tiered Strategy)

#### Tier 1: AWS Primary Backup
- **S3 Intelligent-Tiering**: Automatic cost optimization
- **Glacier Lifecycle**: 30-day → Flexible Retrieval → Deep Archive (90-day)
- **Cross-region replication**: Geographic distribution
- **Cost**: $1-8/TB monthly depending on access patterns

#### Tier 2: Proton Drive (Sensitive Data)
- **Zero-access encryption**: Client-side key generation
- **Swiss privacy protection**: GDPR compliant
- **Selective backup**: Critical/sensitive files only
- **Cost**: $25.98/TB monthly (premium security)

#### Tier 3: Local Air-Gapped Storage
- **External HDDs**: Quarterly rotation cycle
- **Offline storage**: Ransomware protection
- **Cost-effective**: $2.50/TB monthly (3-year amortization)
- **Recovery speed**: Minutes for local access

### Platform Adapters
- **Windows Adapter**: VSS integration, NTFS features, Windows services
- **Linux Adapter**: Extended attributes, systemd integration, filesystem snapshots

## Data Flow

```
Source Files → Backup Engine → Encryption → Storage Backend(s)
                     ↓
              Metadata Database
                     ↓
              Progress/Status Updates
```

## Security Model

- End-to-end encryption with user-controlled keys
- Secure credential management 
- Transport layer security for cloud operations
- Local encryption for physical storage

## Scalability Considerations

- Incremental backup strategies to minimize data transfer
- Parallel operations for large datasets  
- Configurable retention policies
- Deduplication to optimize storage usage