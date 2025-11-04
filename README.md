# Backup Recovery Suite

A comprehensive backup and recovery solution implementing a hybrid 3-2-1-1-0 backup strategy with support for multiple storage tiers including AWS S3, Proton Drive, and local air-gapped storage.

## Architecture

The system implements a tiered backup strategy:
- **Tier 1 (AWS)**: Primary cloud storage with intelligent tiering
- **Tier 2 (Proton Drive)**: Encrypted storage for sensitive data  
- **Tier 3 (Local)**: Air-gapped storage for critical files

## Quick Start

### Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p ~/.backup-recovery/logs ~/.backup-recovery/summaries
```

### Configuration

Copy and customize the configuration template:

```bash
cp configs/backup-profiles.yaml configs/local/my-config.yaml
# Edit configs/local/my-config.yaml with your settings
```

📖 **For detailed configuration guidance**: See [Configuration Guide](docs/CONFIGURATION_GUIDE.md) for data organization, AWS storage strategies, and hardware setup.

### Run Backup

```bash
cd scripts
python backup_orchestrator.py --profile my-profile --config ../configs/local/my-config.yaml
```

### Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Run tests with test profile
python scripts/backup_orchestrator.py --profile test-profile --config configs/test-config.yaml --test

# Run tests with coverage
python -m pytest tests/ -v --cov=scripts --cov-report=html
```

## Project Structure

- `scripts/` - Main Python modules
  - `backup_orchestrator.py` - Main orchestration script
  - `*_backup_manager.py` - Storage tier implementations
- `configs/` - Configuration templates and files
- `tests/` - Test suite
- `docs/` - Documentation
- `cloudformation/` - AWS infrastructure templates

## Development Status

Core functionality implemented and ready for testing. The system provides:

- ✅ Multi-tier backup orchestration
- ✅ Local backup with metadata tracking
- ✅ Configuration-driven file discovery and classification
- ✅ Comprehensive test suite
- 🔄 AWS S3 integration (placeholder)
- 🔄 Proton Drive integration (placeholder)
- 🔄 Scheduling and automation