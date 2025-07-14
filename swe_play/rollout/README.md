# Rollout Pipeline for Automated Project Task Completion

Automated AI pipeline that executes project tasks sequentially, generating unit tests and implementing functionality using OpenHands. The pipeline validates implementations against unit tests and provides robust error handling with retry mechanisms.

## Overview

This module provides a complete workflow for:
1. **Unit Test Generation**: AI generates comprehensive unit tests for each task using OpenHands
2. **Task Implementation**: Implements functionality to satisfy the generated unit tests
3. **Validation**: Runs unit tests to verify implementation correctness
4. **Error Recovery**: Automatically retries failed tasks up to 3 times
5. **Progress Tracking**: Monitors task completion and provides detailed logging
6. **Runtime Management**: Organizes execution artifacts in timestamped runtime directories

## Setup

### Prerequisites

1. **Activate the conda environment:**
   ```bash
   conda activate swe-play
   ```

2. **Set required environment variables:**
   ```bash
   export OPENAI_API_KEY="your_api_key"
   export OPENAI_BASE_URL="your_api_endpoint"
   export OPENHANDS_CONFIG_PATH="path/to/openhands/config.toml"
   ```

3. **Project Structure Requirements:**
   - Project must have a `tasks.json` file with task definitions
   - Project must include `project_description` and `constraints` in tasks.json
   - Each task should have defined unit tests (code_tests and/or visual_tests)

## Usage

### Command Line Interface

```bash
# Run rollout pipeline for a project
python -m swe_play.rollout.rollout --repo-path /path/to/project

# Specify custom runtime directory
python -m swe_play.rollout.rollout --repo-path /path/to/project --runtime-folder custom_runtimes

# Example with absolute path
python -m swe_play.rollout.rollout --repo-path /home/user/my_project --runtime-folder /tmp/rollout_runs
```

### Python API

```python
from swe_play.rollout.rollout import main, generate_unit_test, run_unit_tests

# Run complete rollout pipeline
main(repo_path="/path/to/project", runtime_folder="runtimes")

# Individual components
from pathlib import Path
project_dir = Path("/path/to/project")
task_data = {...}  # Task information from tasks.json

# Generate unit tests for specific task
generate_unit_test(
    task_number="1.2.3",
    task_data=task_data,
    project_dir=project_dir,
    project_description="Your project description"
)

# Run validation tests
success = run_unit_tests(project_dir, ["1.2.3", "2.1.1"])
```

## Pipeline Components

### 1. Unit Test Generation (`generate_unit_test`)
- Creates comprehensive unit tests based on task specifications
- Uses OpenHands to generate both Python test files and bash execution scripts
- Supports multiple test types (code tests, visual tests)
- Follows test-driven development principles

### 2. Task Implementation (`finish_task`)
- Implements functionality to satisfy generated unit tests
- Uses OpenHands with project context and constraints
- Saves implementation artifacts to runtime directories
- Handles complex multi-step task implementations

### 3. Test Validation (`run_unit_tests`)
- Executes generated unit tests against implementations
- Provides detailed pass/fail feedback
- Supports bash script execution for test automation
- Validates all tasks in dependency order

### 4. Test Integrity Checking (`check_unit_test_diff`)
- Ensures unit tests aren't modified during implementation
- Compares test files between generation and implementation phases
- Maintains test integrity and reliability
- Prevents test tampering or accidental modifications

### 5. Pipeline Orchestration (`main`)
- Coordinates all components into a seamless workflow
- Manages retry logic for failed tasks (up to 3 attempts)
- Tracks progress and completion statistics
- Handles runtime directory organization and cleanup

## Project Structure

### Input Requirements
```
project_directory/
├── tasks.json                 # Task definitions and project metadata
├── src/                       # Source code directory
├── tests/                     # Test directory (created if missing)
├── docs/                      # Documentation directory
└── README.md                  # Project documentation
```

### Runtime Output
```
runtime_folder/
└── runtime_[timestamp]/
    ├── [project]_[task]_unit_test/      # Unit test generation artifacts
    ├── [project]_[task]_implementation/ # Implementation artifacts
    ├── log_[task]/                      # OpenHands execution logs
    └── converted_data/                  # Processed runtime data for SFT
```
