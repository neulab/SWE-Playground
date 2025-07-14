# Project Proposal and Initialization Pipeline

Automated AI pipeline that generates project ideas, creates repository structures, and sets up development environments. The pipeline leverages OpenHands for repository setup and supports multiple programming languages.

## Overview

This module provides a complete workflow for:
1. **Project Proposal**: AI generates project ideas with descriptions and repository names
2. **Task Proposal**: Proposes step-by-step development tasks 
3. **Repository Setup**: Initializes project structure using language-specific templates
4. **Environment Configuration**: Sets up development environments with optional Docker support
5. **Unit Test Doc Generation**: Generates the documentation for unit tests based on the proposed tasks

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

```bash
# Run complete pipeline with default settings
python -m swe_play.propose.pipeline

# Customize model and enable Docker image creation
python -m swe_play.propose.pipeline --model claude-sonnet-4-20250514 --docker

# Specify custom output directory
python -m swe_play.propose.pipeline --output-folder my_projects --docker
```

### Python API

```python
from swe_play.propose.pipeline import create_project_pipeline
from swe_play.propose.propose_projects import propose_projects
from swe_play.propose.propose_tasks import propose_tasks

# Complete pipeline
result = create_project_pipeline(
    model="neulab/claude-sonnet-4-20250514",
    output_folder="generated",
    docker=True
)
print(f"Created: {result['repo_name']} at {result['project_path']}")

# Individual components
projects = propose_projects(model="neulab/claude-sonnet-4-20250514")
tasks = propose_tasks(project_description="Your project", model="neulab/claude-sonnet-4-20250514")
```

## Pipeline Components

### 1. Project Proposal (`propose_projects.py`)
- Generates creative project ideas using AI
- Creates repository names and descriptions
- Outputs structured project proposals

### 2. Task Generation (`propose_tasks.py`) 
- Breaks down projects into actionable development tasks
- Creates both Markdown and JSON task formats
- Provides step-by-step implementation guidance
- Generate unit test documentation for each task

### 3. Repository Setup (`setup_repo.py`)
- Initializes project structure from language templates
- Supports Python, JavaScript, C++, and Rust
- Integrates with OpenHands for automated setup
- Optional Docker image creation

### 4. Pipeline Orchestration (`pipeline.py`)
- Coordinates all components into a seamless workflow
- Provides both CLI and programmatic interfaces
- Handles error recovery and logging

## Project Structure

### Input Resources
```
swe_play/propose/
├── prompts/                    # Jinja2 templates for AI prompts
│   ├── propose-projects-*.jinja
│   ├── propose-tasks-*.jinja
│   ├── unit-test-*.jinja
│   └── setup-project-repo-*.jinja
└── repo_starter/              # Language-specific project templates
    ├── python/
    ├── javascript/
    ├── c++/
    └── rust/
```

### Generated Output
```
generated/
└── [repo-name]/
    ├── tasks.md              # Human-readable task list
    ├── tasks.json            # Machine-readable task data
    ├── Dockerfile            # Container configuration (if enabled)
    ├── src/                  # Source code structure
    ├── tests/                # Test framework setup
    ├── docs/                 # Documentation templates
    └── README.md             # Project documentation
```
