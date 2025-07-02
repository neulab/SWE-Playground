# Project Proposal, Initialization and Unit Test Generation Pipeline

Automated pipeline that uses AI to propose project ideas and step by step tasks, set up repository structures, and generate unit tests. The pipeline also configures all Docker-related files and builds a Docker image for the project.

## Setup

Set environment variables:
```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="your_api_endpoint"
export OPENHANDS_CONFIG_PATH="path/to/config"
```

Activate conda environment: `conda activate swe-play`

## Usage

### Command Line
```bash
# Default settings
python -m swe_play.propose.project

# Both options
python -m swe_play.propose.project --max-tasks 20 --model claude-sonnet-4-20250514
```

### Python API
```python
from swe_play.propose.project import create_project_pipeline, propose_project

# Full pipeline with default model
result = create_project_pipeline(max_tasks=20)
print(f"Created: {result['repo_name']} at {result['project_path']}")

# Custom model
result = create_project_pipeline(max_tasks=20, model="claude-sonnet-4-20250514")

# Just propose with custom model
project, repo, language = propose_project(model="claude-sonnet-4-20250514")
```

## How It Works

1. **Propose**: LLM generates project idea, repo name and tasks
2. **Initialize**: Copies template and setup repository sturctures with OpenHands
3. **Generate Unit Tests**: Generate unit tests task by task with OpenHands

**Output Structure:**
```
generated/
└── [repo-name]/
    ├── tasks.md          # Generated tasks in Markdown format
    ├── tasks.json        # Generated tasks in JSON format
    ├── Dockerfile        # Dockerfile for Docker image creation
    ├── tests/            # Unit tests
    ├── src/              # Source code structure
    ├── assets/           # Assets for the project
    └── ...         
```
