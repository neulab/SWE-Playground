# Rollout Pipeline for Automated Project Task Completion

Automated AI pipeline that executes project tasks sequentially, generating unit tests and implementing functionality using OpenHands. The pipeline validates implementations against unit tests, provides robust error handling with retry mechanisms, and optionally generates task-specific data for SWE-bench, SWT-Bench, and Commit-0 benchmarks.

## Overview

This module provides a complete workflow for:
1. **Unit Test Generation**: AI generates comprehensive unit tests for each task using OpenHands based on unit test documentation
2. **Task Implementation**: Implements functionality to satisfy the generated unit tests using OpenHands
3. **Test Integrity Checking**: Ensures unit tests aren't modified during implementation phase
4. **Validation**: Runs unit tests to verify implementation correctness
5. **Error Recovery**: Automatically retries failed tasks up to 3 times
6. **Data Conversion**: Converts OpenHands trajectories to JSON format for supervised fine-tuning (SFT)
7. **Task-Specific Data Generation** (optional): Generates SWE-bench, SWT-Bench, or Commit-0 benchmark data

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
   - Project must include `project_description` and `constraints` in `tasks.json`
   - Each task should have defined unit tests (`code_tests` and/or `visual_tests`) in `tasks.json`
   - Unit test documentation files should exist in `tests/{task_number}.md` (generated during proposal phase)

## Usage

### Command Line Interface

#### Main Rollout Pipeline

Run the complete rollout pipeline for a project:

```bash
# Run rollout pipeline for a project
python -m swe_play.rollout.rollout --repo-path /path/to/project

# Specify custom runtime directory
python -m swe_play.rollout.rollout --repo-path /path/to/project --runtime-folder custom_runtimes

# Run rollout and generate SWE-bench data
python -m swe_play.rollout.rollout --repo-path /path/to/project --swe

# Run rollout and generate SWT-Bench data
python -m swe_play.rollout.rollout --repo-path /path/to/project --swt

# Run rollout and generate Commit-0 data
python -m swe_play.rollout.rollout --repo-path /path/to/project --commit0

# Generate multiple benchmark data types
python -m swe_play.rollout.rollout --repo-path /path/to/project --swe --swt --commit0
```

**Arguments:**
- `--repo-path`: **Required**. The path of the project repository to process
- `--runtime-folder`: The folder to save the runtime data (default: `runtimes`)
- `--swe`: Generate SWE-bench data after completing the rollout (flag)
- `--swt`: Generate SWT-Bench data after completing the rollout (flag)
- `--commit0`: Generate Commit-0 data after completing the rollout (flag)

#### Task-Specific Data Generation (Standalone)

You can also run task-specific data generation modules independently:

**SWE-bench:**

```bash
python -m swe_play.rollout.swe_bench --repo-path /path/to/project --runtime-folder /path/to/runtime
```

**SWT-Bench:**

```bash
python -m swe_play.rollout.swt_bench --repo-path /path/to/project --runtime-folder /path/to/runtime
```

**Commit-0:**

```bash
python -m swe_play.rollout.commit0 --repo-path /path/to/project --runtime-folder /path/to/runtime --num-iterations 1
```

**Arguments for Commit-0:**
- `--num-iterations`: Number of iterations to run (default: `1`)

### Python API

```python
from swe_play.rollout.rollout import main, generate_unit_test, finish_task, run_unit_tests, check_unit_test_diff
from pathlib import Path

# Run complete rollout pipeline
main(
    repo_path="/path/to/project",
    runtime_folder="runtimes",
    generate_swe=False,
    generate_swt=False,
    generate_commit0=False
)

# Individual components
project_dir = Path("/path/to/project")
task_data = {
    "task_number": "1.2.3",
    "task_title": "Task Title",
    "task_description": "Task description",
    "all_tests": [...],
    "total_tests": 3
}
project_description = "Project description"
constraints = "Project constraints"

# Generate unit tests for specific task
generate_unit_test(
    task_number="1.2.3",
    task_data=task_data,
    project_dir=project_dir,
    project_description=project_description,
    save_dir=Path("runtime_dir/log_1.2.3_unit_test")
)

# Implement task
finish_task(
    task_number="1.2.3",
    task_description="Task description",
    constraints=constraints,
    project_dir=project_dir,
    save_dir=Path("runtime_dir/log_1.2.3_implementation")
)

# Run validation tests
all_tasks = ["1.2.3", "1.2.4"]
success = run_unit_tests(project_dir, all_tasks)

# Check test integrity
unit_test_dir = Path("runtime_dir/project_1.2.3_unit_test")
implementation_dir = Path("runtime_dir/project_1.2.3_implementation")
tests_unchanged = check_unit_test_diff(unit_test_dir, implementation_dir, all_tasks)
```

## Pipeline Components

### 1. Unit Test Generation (`generate_unit_test`)

Generates executable unit tests based on task specifications and unit test documentation.

**Functionality:**
- Reads unit test documentation from `tests/{task_number}.md` (generated during proposal phase)
- Uses OpenHands to create Python test files (`test_{task_number}.py`) and bash execution scripts (`{task_number}.sh`)
- Supports multiple test types (code tests, visual tests)
- Follows test-driven development principles

**Input:**
- Task number and task data with test specifications
- Project directory with unit test documentation
- Project description for context

**Output:**
- Python test files in `tests/test_{task_number}.py`
- Bash execution scripts in `tests/{task_number}.sh`
- OpenHands trajectory logs saved to `log_{task_number}_unit_test/`

### 2. Task Implementation (`finish_task`)

Implements functionality to satisfy generated unit tests using OpenHands.

**Functionality:**
- Uses OpenHands to implement code based on task description and constraints
- Works in a copy of the project directory to preserve test integrity
- Saves implementation artifacts to runtime directories

**Input:**
- Task number and description
- Project constraints
- Project directory (copy from unit test generation)

**Output:**
- Implemented functionality in source files
- OpenHands trajectory logs saved to `log_{task_number}_implementation/`

### 3. Test Integrity Checking (`check_unit_test_diff`)

Ensures unit tests aren't modified during implementation phase.

**Functionality:**
- Compares test files between unit test generation and implementation phases
- Uses `diff` to check Python test files and bash scripts
- Maintains test integrity and reliability
- Prevents test tampering or accidental modifications

**Returns:** `True` if tests are unchanged, `False` if modifications detected

**Action:** If modifications are detected, test files are restored from unit test generation directory

### 4. Test Validation (`run_unit_tests`)

Executes generated unit tests against implementations to verify correctness.

**Functionality:**
- Runs bash test scripts (`{task_number}.sh`) for each task in dependency order
- Tests are executed sequentially, accumulating completed tasks (all tasks up to current task)
- Provides detailed pass/fail feedback
- Validates all tasks from start to current task

**Input:**
- Project directory with implementations
- List of all task numbers to test (accumulated as tasks complete)

**Returns:** `True` if all tests pass, `False` otherwise

### 5. Data Conversion (`convert_data`)

Converts OpenHands trajectories to JSON format for supervised fine-tuning.

**Functionality:**
- Processes OpenHands completion logs from `log_completions/`
- Extracts conversation messages and formats them as JSON
- Creates structured data files for SFT training

**Output:**
- JSON files in `converted_data/{task_number}_{stage}.json`
- Format: `{"messages": [{"role": "...", "content": "..."}, ...]}`

### 6. Pipeline Orchestration (`main`)

Coordinates all components into a seamless workflow.

**Pipeline Flow:**
1. Load project configuration from `tasks.json`
2. Group tasks by task number, extracting unit test specifications
3. For each task with unit tests:
   - **Unit Test Generation**: Copy project directory and generate unit tests
   - **Task Implementation**: Copy unit test directory and implement task
   - **Test Integrity Check**: Verify tests weren't modified, restore if needed
   - **Validation**: Run all accumulated tests (tasks processed so far)
   - **Retry Logic**: If tests fail, retry up to 3 times (cleaning up directories between retries)
   - **Data Conversion**: Convert both unit test and implementation trajectories to JSON
   - **Progress**: Update project directory to implementation version for next task
4. Optionally generate task-specific benchmark data:
   - SWE-bench: Issue proposal, application, and fixing
   - SWT-Bench: Similar to SWE-bench with different prompts
   - Commit-0: Implement from scratch with cleaned codebase

**Task Processing Order:**
- Tasks are processed sequentially in the order they appear in `tasks.json`
- Each task builds on the previous implementation (project directory is updated)
- All tests up to the current task are re-run to ensure no regressions

**Retry Mechanism:**
- Failed tasks are retried up to 3 times
- Between retries, implementation and unit test directories are cleaned up
- If 3 retries fail, pipeline exits with the number of completed tasks

### 7. Task-Specific Data Generation

#### SWE-bench (`swe_bench.py`)

Generates SWE-bench style benchmark data (issue proposal and fixing).

**Process:**
1. **Propose Issue**: Uses LLM to generate technical issue description and user-friendly bug report
2. **Apply Issue**: Uses OpenHands to introduce the bug to the working codebase
3. **Fix Issue**: Uses OpenHands to fix the buggy codebase
4. **Validation**: Runs tests to verify fix

**Output:**
- Buggy codebase with introduced issues
- Issue descriptions and fix trajectories
- Converted data files in `converted_data/`

#### SWT-Bench (`swt_bench.py`)

Generates SWT-Bench style benchmark data (similar to SWE-bench but with different prompts and test cleanup).

**Process:**
- Similar to SWE-bench but uses SWT-specific prompts
- Includes test file cleanup (removes bash scripts, renames Python test files)
- Generates different issue formats for SWT-Bench benchmark

**Output:**
- Buggy codebase with introduced issues
- Cleaned test files
- SWT-Bench formatted data

#### Commit-0 (`commit0.py`)

Generates Commit-0 style benchmark data (implement from scratch).

**Process:**
1. **Raw Data Preparation**:
   - Starts from initial project repository (without implementations)
   - Copies test files from completed implementation
   - Replaces `NotImplementedError` with `pass` in all source files
   - Cleans up test files (removes bash scripts, renames test files)
2. **Implementation**: Uses OpenHands to implement functionality from scratch
3. **Iterations**: Can run multiple iterations for data augmentation

**Input Requirements:**
- Requires completed rollout with valid unit test and implementation logs
- Processes only the last valid task that has both unit test and implementation data

**Output:**
- Multiple implementation attempts from scratch
- Converted data files for each iteration

## Project Structure

### Input Requirements

```
project_directory/
├── tasks.json                 # Task definitions and project metadata
│   ├── project_name
│   ├── project_description
│   ├── constraints
│   └── phases[...]
│       └── modules[...]
│           └── tasks[...]
│               └── unit_tests
│                   ├── code_tests
│                   └── visual_tests
├── tests/                     # Unit test documentation directory
│   ├── 1.1.1.md              # Unit test docs (from proposal phase)
│   ├── 1.1.2.md
│   └── ...
├── src/                       # Source code directory
├── docs/                      # Documentation directory
└── README.md                  # Project documentation
```

### Runtime Output

```
runtime_folder/
└── runtime_[timestamp]/
    ├── [project_name]_[task_number]_unit_test/        # Unit test generation artifacts
    │   ├── src/                                        # Source code (unchanged)
    │   └── tests/                                      # Generated test files
    │       ├── test_{task_number}.py                  # Python test file
    │       └── {task_number}.sh                       # Bash execution script
    ├── [project_name]_[task_number]_implementation/   # Implementation artifacts
    │   ├── src/                                        # Implemented source code
    │   └── tests/                                      # Test files (same as unit_test)
    ├── log_{task_number}_unit_test/                   # OpenHands unit test logs
    │   ├── log_completions/                           # Completion logs
    │   └── trajectories/                               # Trajectory data
    ├── log_{task_number}_implementation/              # OpenHands implementation logs
    │   ├── log_completions/                           # Completion logs
    │   └── trajectories/                               # Trajectory data
    ├── converted_data/                                 # Processed data for SFT
    │   ├── {task_number}_unit_test.json               # Unit test trajectory (JSON)
    │   ├── {task_number}_implementation.json          # Implementation trajectory (JSON)
    │   └── ...
    ├── commit0_raw/                                    # Commit-0 raw data (if generated)
    │   └── [project_name]/
    │       ├── src/                                    # Source with pass instead of NotImplementedError
    │       └── tests/                                  # Test files from implementation
    ├── commit0/                                        # Commit-0 iterations (if generated)
    │   └── [project_name]/
    │       ├── src/                                    # Implemented from scratch
    │       └── tests/
    └── ...                                             # Additional benchmark-specific directories
```

## Pipeline Details

### Task Processing Flow

1. **Task Selection**: Iterates through tasks in `tasks.json`, processing only tasks with unit tests
2. **Unit Test Generation**: Creates isolated copy of project, generates executable tests
3. **Task Implementation**: Creates copy from unit test directory, implements functionality
4. **Test Validation**: Runs all tests from first task to current task (ensures no regressions)
5. **Success**: Converts trajectories to JSON, updates project directory to implementation version
6. **Failure**: Cleans up directories, retries up to 3 times

### Test Execution Strategy

Tests are executed cumulatively:
- When testing task `1.2.3`, all tests for tasks `1.1.1`, `1.1.2`, `1.2.1`, `1.2.2`, and `1.2.3` are run
- This ensures no regressions in previously completed tasks
- The `all_tasks` list grows as tasks are completed successfully

### Error Handling

- **Test Generation Failure**: Raises exception, stops pipeline
- **Implementation Failure**: Retries up to 3 times, then exits
- **Test Failure**: Retries implementation up to 3 times
- **Test Modification Detected**: Automatically restores original test files
- **Benchmark Generation Failure**: Logs warning but continues (doesn't stop pipeline)

### Data Format

**Converted Data JSON Structure:**
```json
{
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
}
```

Each converted file contains the conversation trajectory from OpenHands, formatted for supervised fine-tuning. For training, we filter out failed actions and consecutive duplicate messages from these trajectories to ensure robustness.
