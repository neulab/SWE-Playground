# SWE-Playground

## Setup

### Repository Setup

1. **Create and activate your Python environment:**
    ```bash
    conda create -n swe-play python==3.12
    conda activate swe-play
    ```

2. **Install the package:**
    ```bash
    pip install -e .
    ```

3. **OpenHands Headless Setup**

    This repository leverages OpenHands in headless mode via python. To set up OpenHands for this, follow the [OpenHands Development setup instructions](https://docs.all-hands.dev/usage/how-to/headless-mode#with-python)

4. **Set Env variables**
    ```bash
    export OPENAI_API_KEY="your_api_key"
    export OPENAI_BASE_URL="your_api_endpoint"
    export OPENHANDS_CONFIG_PATH="path/to/openhands/config.toml"
    ```

## Project Proposal and Initialization Pipeline

Automated AI pipeline for generating and setting up new software engineering projects.

```bash
python -m swe_play.propose.project --max-tasks 20 --model claude-sonnet-4-20250514
```

📖 **[Detailed Pipeline Documentation](swe_play/propose/README.md)**

## Contributing

1. Install development dependencies: `pip install -e ".[dev]"`
2. Install pre-commit hooks: `pre-commit install`
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request
6. When merging a pull request, please use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.