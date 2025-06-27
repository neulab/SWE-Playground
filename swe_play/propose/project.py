"""Project proposal and initialization pipeline."""

import argparse
import re
import shutil
import sys
from pathlib import Path

from swe_play.utils.call_openhands import call_openhands
from swe_play.utils.llm_client import create_llm_client
from swe_play.utils.prompt_retriever import PromptRetriever


def propose_project(model: str = "neulab/claude-sonnet-4-20250514") -> tuple[str, str]:
    """Propose a new project and repository name using the LLM.

    Args:
        model: The LLM model to use for project proposal.

    Returns:
        A tuple of (project_description, repo_name)

    Raises:
        Exception: If project proposal fails or response format is invalid.
    """
    llm_client = create_llm_client(model=model)
    prompt_retriever = PromptRetriever()

    system_prompt = prompt_retriever.get_prompt("propose-next-project-system")
    user_prompt = prompt_retriever.get_prompt("propose-next-project-user")

    response = llm_client.system_completion(
        system_prompt=system_prompt, user_prompt=user_prompt, temperature=1.0
    )

    project_match = re.search(r"<proposed_project>(.*?)</proposed_project>", response, re.DOTALL)
    repo_match = re.search(r"<repo_name>(.*?)</repo_name>", response, re.DOTALL)

    if not project_match or not repo_match:
        raise Exception(
            f"Invalid response format from LLM. Expected <proposed_project> and <repo_name> tags. "
            f"Got: {response}"
        )

    project_description = project_match.group(1).strip()
    repo_name = repo_match.group(1).strip()

    return project_description, repo_name


def initialize_project_repo(project_description: str, repo_name: str, max_tasks: int = 20) -> str:
    """Initialize a project repository by copying the starter template and calling OpenHands.

    Args:
        project_description: Description of the project to work on
        repo_name: Name for the repository directory
        max_tasks: Maximum number of tasks to generate (default: 20)

    Returns:
        Path to the created project directory

    Raises:
        Exception: If initialization fails.
    """
    current_dir = Path(__file__).parent
    repo_starter_path = current_dir / "repo_starter"
    generated_dir = current_dir.parent.parent / "generated"
    project_dir = generated_dir / repo_name

    generated_dir.mkdir(exist_ok=True)

    if project_dir.exists():
        raise Exception(f"Project directory already exists: {project_dir}")

    try:
        shutil.copytree(repo_starter_path, project_dir)
        print(f"Copied repo_starter template to: {project_dir}")
    except Exception as e:
        raise Exception(f"Failed to copy repo_starter template: {e}")

    prompt_retriever = PromptRetriever()
    initialization_prompt = prompt_retriever.get_prompt(
        "initialize-project-repo-and-tasks-openhands",
        project_task=project_description,
        max_tasks=max_tasks,
    )

    try:
        openhands_output = call_openhands(prompt=initialization_prompt, directory=str(project_dir))
        print(f"OpenHands initialization completed for project: {repo_name}")
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        # Clean up the directory if OpenHands fails
        shutil.rmtree(project_dir, ignore_errors=True)
        raise Exception(f"OpenHands initialization failed: {e}")

    return str(project_dir)


def create_project_pipeline(
    max_tasks: int = 20, model: str = "neulab/claude-sonnet-4-20250514"
) -> dict[str, str]:
    """Complete pipeline to propose and initialize a new project.

    Args:
        max_tasks: Maximum number of tasks to generate (default: 20)
        model: The LLM model to use for project proposal (default: neulab/claude-sonnet-4-20250514)

    Returns:
        Dictionary containing project details:
        - project_description: The proposed project description
        - repo_name: The repository name
        - project_path: Path to the created project directory

    Raises:
        Exception: If any step in the pipeline fails.
    """
    print("Starting project proposal and initialization pipeline...")

    # Step 1: Propose project
    print("Step 1: Proposing project...")
    project_description, repo_name = propose_project(model=model)
    print(f"Proposed project: {project_description}")
    print(f"Repository name: {repo_name}")

    # Step 2: Initialize project repository
    print("Step 2: Initializing project repository...")
    project_path = initialize_project_repo(project_description, repo_name, max_tasks)
    print(f"Project initialized at: {project_path}")

    return {
        "project_description": project_description,
        "repo_name": repo_name,
        "project_path": project_path,
    }


def main() -> None:
    """CLI entry point for the project pipeline."""
    parser = argparse.ArgumentParser(
        description="Create a new project with automatic proposal and initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.propose.project                           # Default settings
  python -m swe_play.propose.project --max-tasks 3            # Custom task count
  python -m swe_play.propose.project --model gpt-4           # Custom model
  python -m swe_play.propose.project --max-tasks 5 --model gpt-3.5-turbo  # Both options
        """,
    )

    parser.add_argument(
        "--max-tasks",
        type=int,
        default=20,
        help="Maximum number of tasks to generate for the project (default: 20)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="neulab/claude-sonnet-4-20250514",
        help="LLM model to use for project proposal (default: neulab/claude-sonnet-4-20250514)",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting project creation pipeline...\n")
        result = create_project_pipeline(max_tasks=args.max_tasks, model=args.model)

        print("\n✅ Pipeline completed successfully!")
        print(f"📋 Project: {result['project_description']}")
        print(f"📁 Repository: {result['repo_name']}")
        print(f"📍 Path: {result['project_path']}")
        print(f"\nYou can find your new project at: {result['project_path']}")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
