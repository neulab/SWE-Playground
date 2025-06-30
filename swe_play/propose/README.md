# Project Proposal, Initialization and Unit Test Generation Pipeline

Automated pipeline that uses AI to propose project ideas, set up repository structures with tasks and generate unit tests.

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
python -m swe_play.propose.project --max-tasks 5 --model gpt-3.5-turbo
```

### Python API
```python
from swe_play.propose.project import create_project_pipeline, propose_project

# Full pipeline with default model
result = create_project_pipeline(max_tasks=5)
print(f"Created: {result['repo_name']} at {result['project_path']}")

# Custom model
result = create_project_pipeline(max_tasks=5, model="gpt-4")

# Just propose with custom model
project, repo, language = propose_project(model="claude-3-sonnet")
```

## How It Works

1. **Propose**: LLM generates project idea and repo name
2. **Initialize**: Copies template and generates tasks with OpenHands
3. **Generate Unit Tests**: Generate unit tests task by task with OpenHands

**Output Structure:**
```
generated/
└── [repo-name]/
    ├── tasks.md          # Generated tasks in Markdown format
    ├── tasks.json        # Generated tasks in JSON format
    ├── tests/            # Unit tests
    ├── src/              # Source code structure
    ├── assets/           # Assets for the project
    └── ...         
```
