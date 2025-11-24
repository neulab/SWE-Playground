# Project Proposal and Initialization Pipeline

Automated AI pipeline that generates project ideas, creates repository structures, and sets up development environments. The pipeline leverages OpenHands for repository setup and supports multiple programming languages.

## Overview

This module provides a complete workflow for:
1. **Project Proposal**: AI generates project ideas with descriptions, repository names, programming languages, and constraints
2. **Task Proposal**: Proposes step-by-step development tasks in a structured markdown format
3. **Repository Setup**: Initializes project structure using language-specific templates via OpenHands
4. **Unit Test Documentation Generation**: Generates detailed unit test documentation for each task based on the proposed tasks

**Note:** Docker image creation is not currently supported, although Dockerfiles are prepared as part of the repository setup.

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

## Usage

### Command Line Interface

#### Complete Pipeline

Run the entire pipeline end-to-end:

```bash
# Run complete pipeline with default settings
python -m swe_play.propose.pipeline

# Customize model
python -m swe_play.propose.pipeline --model claude-sonnet-4-20250514

# Specify custom output directory
python -m swe_play.propose.pipeline --output my_projects
```

**Arguments:**
- `--model`: LLM model to use (default: `claude-sonnet-4-20250514`)
- `--output`: Output folder to save the project (default: `generated`)

**Note:** Docker image creation is not currently supported.

#### Individual Components

**1. Propose Projects Only:**

```bash
# Propose a single project (default)
python -m swe_play.propose.propose_projects

# Propose multiple projects
python -m swe_play.propose.propose_projects --num-projects 5

# Save to custom output folder
python -m swe_play.propose.propose_projects --output projects
```

**Arguments:**
- `--num-projects`: Number of projects to propose (default: `1`)
- `--model`: LLM model to use (default: `claude-sonnet-4-20250514`)
- `--output`: Output folder to save projects as JSON files (default: `None`)

**2. Propose Tasks for a Project:**

```bash
# Requires a project JSON file
python -m swe_play.propose.propose_tasks --project-file /path/to/project.json
```

**Arguments:**
- `--model`: LLM model to use (default: `claude-sonnet-4-20250514`)
- `--project-file`: Path to the project JSON file containing `project_description` and `constraints`

**3. Setup Repository:**

```bash
# Use absolute path here
python -m swe_play.propose.setup_repo \
    --project-file /path/to/project.json \
    --output generated
```

**Arguments:**
- `--project-file`: Path to the project JSON file containing all project details including tasks
- `--output`: Output folder to save the project (default: `generated`)
- `--model`: LLM model to use (default: `claude-sonnet-4-20250514`)

**Note:** Docker image creation is not currently supported.

### Python API

```python
from swe_play.propose.pipeline import create_project_pipeline
from swe_play.propose.propose_projects import propose_projects
from swe_play.propose.propose_tasks import propose_tasks, generate_unit_tests
from swe_play.propose.setup_repo import setup_repo

# Complete pipeline
result = create_project_pipeline(
    model="claude-sonnet-4-20250514",
    output_folder="generated",
    docker=False  # Docker creation is not currently supported
)
print(f"Created: {result['repo_name']} at {result['project_path']}")

# Individual components
# 1. Propose projects
projects = propose_projects(
    model="claude-sonnet-4-20250514",
    num_projects=1,
    output_folder="projects"
)

# 2. Propose tasks
tasks = propose_tasks(
    project_description=projects[0]["project_description"],
    constraints=projects[0]["constraints"],
    model="claude-sonnet-4-20250514"
)

# 3. Setup repository
project_path = setup_repo(
    project_description=projects[0]["project_description"],
    constraints=projects[0]["constraints"],
    repo_name=projects[0]["repo_name"],
    programming_language=projects[0]["programming_language"],
    tasks=tasks,
    output_folder="generated"
)

# 4. Generate unit test documentation
generate_unit_tests(
    project_path=project_path,
    model="claude-sonnet-4-20250514"
)
```

## Pipeline Components

### 1. Project Proposal (`propose_projects.py`)

Generates creative project ideas using AI.

**Functionality:**
- Creates project descriptions, repository names, programming languages, and constraints
- Supports proposing multiple projects at once
- Outputs structured project proposals as dictionaries or JSON files

**Returns:** List of dictionaries, each containing:
- `project_description`: Description of the project
- `repo_name`: Repository name
- `programming_language`: Programming language (Python, JavaScript, C++, Rust)
- `constraints`: Library/framework constraints to ensure core implementation

### 2. Task Generation (`propose_tasks.py`)

Breaks down projects into actionable development tasks.

**Functionality:**
- Generates structured markdown task documents with phases, modules, and individual tasks
- Each task includes description, dependencies, difficulty rating, and unit test specifications
- Handles response truncation automatically (asks model to continue if needed)
- Converts markdown tasks to structured JSON format

**Task Structure:**
- Organized into phases (max 5 phases)
- Each phase contains modules
- Each module contains individual tasks (format: X.Y.Z)
- Tasks include:
  - Description
  - Dependencies (task numbers)
  - Difficulty (1/5 to 5/5)
  - Unit Tests (code tests and visual tests)

**Returns:** Tasks in markdown format (string)

**Unit Test Documentation Generation:**
- `generate_unit_tests()`: Reads tasks.json and generates detailed unit test documentation
- Creates markdown files in `tests/{task_number}.md` for each task with unit tests
- Uses previous unit test documentation as context for consistency

### 3. Repository Setup (`setup_repo.py`)

Initializes project structure from language-specific templates using OpenHands.

**Functionality:**
- Copies language-specific starter templates (Python, JavaScript, C++, Rust)
- Writes tasks to `tasks.md` and converts to structured `tasks.json`
- Uses OpenHands to set up the project structure:
  - Creates appropriate configuration files (requirements.txt, package.json, CMakeLists.txt, Cargo.toml, etc.)
  - Sets up directory structure (src/, tests/, docs/, assets/)
  - Creates placeholder source files with `NotImplementedError` stubs
  - Prepares Dockerfile for containerized development (Dockerfile is created but Docker image creation is not currently supported)

**Supported Languages:**
- Python (environment.yml, Dockerfile)
- JavaScript (package.json, Dockerfile)
- C++ (CMakeLists.txt, Dockerfile)
- Rust (Cargo.toml, Dockerfile)

**Returns:** Path to the created project directory (string)

### 4. Pipeline Orchestration (`pipeline.py`)

Coordinates all components into a seamless workflow.

**Pipeline Steps:**
1. Propose project (calls `propose_projects()`)
2. Propose tasks (calls `propose_tasks()`)
3. Setup repository (calls `setup_repo()`)
4. Generate unit test documentation (calls `generate_unit_tests()`)

**Returns:** Dictionary with:
- `project_description`: The proposed project description
- `repo_name`: The repository name
- `project_path`: Path to the created project directory

## Project Structure

### Input Resources

```
swe_play/
├── propose/
│   ├── repo_starter/              # Language-specific project templates
│   │   ├── python/
│   │   │   ├── environment.yml
│   │   │   └── Dockerfile
│   │   ├── javascript/
│   │   │   ├── package.json
│   │   │   └── Dockerfile
│   │   ├── c++/
│   │   │   ├── CMakeLists.txt
│   │   │   └── Dockerfile
│   │   └── rust/
│   │       ├── Cargo.toml
│   │       └── Dockerfile
│   ├── propose_projects.py
│   ├── propose_tasks.py
│   ├── setup_repo.py
│   └── pipeline.py
└── prompts/                       # Jinja2 templates for AI prompts
    ├── propose-projects-system.jinja
    ├── propose-projects-user.jinja
    ├── propose-tasks-system.jinja
    ├── propose-tasks-user.jinja
    ├── propose-tasks-user-continue.jinja
    ├── unit-test-system.jinja
    ├── unit-test-user.jinja
    ├── setup-project-repo-openhands.jinja
    ├── fix-dockerfile-openhands.jinja
    └── common-project-prefix-system.jinja
```

### Generated Output

```
generated/
└── [repo-name]/
    ├── tasks.md                   # Human-readable task list (markdown)
    ├── tasks.json                 # Machine-readable task data (structured JSON)
    ├── Dockerfile                 # Container configuration
    ├── tests/                     # Unit test documentation
    │   ├── 1.1.1.md               # Unit test docs for task 1.1.1
    │   ├── 1.1.2.md               # Unit test docs for task 1.1.2
    │   └── ...
    ├── src/                       # Source code structure
    ├── tests/                     # Test framework setup (if applicable)
    ├── docs/                      # Documentation templates
    └── [language-specific files]  # requirements.txt, package.json, etc.
```

**tasks.json Structure:**

```json
{
    "project_id": "unique_id",
    "project_name": "repo-name",
    "project_description": "...",
    "project_instruction": "...",
    "phases": [
        {
            "phase_number": 1,
            "title": "Phase Name",
            "goal": "Phase goal",
            "modules": [
                {
                    "module_number": "1.1",
                    "title": "Module Name",
                    "tasks": [
                        {
                            "task_number": "1.1.1",
                            "title": "Task Title",
                            "description": "...",
                            "dependencies": ["1.1.1", ...],
                            "difficulty": "3/5",
                            "unit_tests": {
                                "code_tests": [
                                    {
                                        "name": "TestName",
                                        "description": "..."
                                    }
                                ],
                                "visual_tests": [...]
                            }
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Workflow Details

### Complete Pipeline Flow

1. **Project Proposal**: AI generates a project idea with all metadata
2. **Task Proposal**: AI breaks down the project into phases, modules, and individual tasks with unit test specifications
3. **Repository Setup**: 
   - Copy language-specific template
   - Write tasks.md and convert to tasks.json
   - Use OpenHands to set up project structure (config files, directories, placeholder code)
   - Prepare Dockerfile (Docker image creation is not currently supported)
4. **Unit Test Documentation**: Generate detailed unit test documentation files for each task

### Task Proposal Format

Tasks are organized hierarchically:
- **Phases** (e.g., "Phase 1: Foundation")
  - **Modules** (e.g., "Module 1.1: Core Data Structures")
    - **Tasks** (e.g., "Task 1.1.1: Implement Linked List")

Each task specifies:
- What needs to be implemented
- Prerequisites (dependencies)
- Difficulty level
- Unit tests that should pass when completed

### Repository Initialization

OpenHands is used to:
- Create appropriate configuration files for the programming language
- Set up standard directory structure
- Create placeholder source files with `NotImplementedError` stubs
- Ensure the project is buildable but tests don't pass initially
- Prepare Dockerfile for containerized development (Dockerfile is created, but Docker image creation is not currently supported)

The repository setup explicitly avoids implementing any functionality that would make unit tests pass, leaving that for the implementation phase.
