# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a backup-recovery Python project currently in initial setup phase. The repository contains:
- Basic README.md with project name
- Comprehensive Python .gitignore file configured for multiple Python package managers (pip, poetry, uv, pdm, pixi)
- Support for various Python development tools (pytest, mypy, ruff, etc.)

## Development Setup

Since this is a new Python project, the typical development workflow would involve:

1. **Virtual Environment**: Create a virtual environment using your preferred method:
   - `python -m venv .venv` (standard venv)
   - `poetry install` (if using Poetry)
   - `uv venv` (if using uv)
   - `pdm install` (if using PDM)

2. **Dependencies**: Add project dependencies via the appropriate configuration file:
   - `requirements.txt` for pip
   - `pyproject.toml` for modern Python packaging
   - `poetry.toml` if using Poetry

## Expected Architecture

Based on the project name "backup-recovery", this project will likely implement:
- Backup operations for files, databases, or system configurations
- Recovery/restore functionality
- Potentially scheduled backup jobs
- Configuration management for backup targets and destinations

## Git Workflow

- Main branch: `main` (current)
- Repository is WSL2-based Linux environment
- Standard Python gitignore already configured