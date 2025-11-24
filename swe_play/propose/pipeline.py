"""Project proposal and initialization pipeline."""

import argparse
import sys

from swe_play.propose.propose_projects import propose_projects
from swe_play.propose.propose_tasks import generate_unit_tests, propose_tasks
from swe_play.propose.setup_repo import create_docker_image, setup_repo


def create_project_pipeline(
    model: str = "claude-sonnet-4-20250514",
    output_folder: str = "generated",
    docker: bool = False,
) -> dict[str, str]:
    """Complete pipeline to propose and initialize a new project.

    Args:
        model: The LLM model to use for project proposal
               (default: claude-sonnet-4-20250514)
        output_folder: The folder to save the project
               (default: generated)
        docker: Whether to create a Docker image for the project
               (default: False)

    Returns:
        Dictionary containing project details:
        - project_description: The proposed project description
        - repo_name: The repository name
        - project_path: Path to the created project directory

    Raises:
        Exception: If any step in the pipeline fails.
    """
    print("Starting project proposal and initialization pipeline...")
    print("")

    # Step 1: Propose project
    print("Step 1: Proposing project...")
    project = propose_projects(num_projects=1, model=model)
    project_description = project[0]["project_description"]
    repo_name = project[0]["repo_name"]
    programming_language = project[0]["programming_language"]
    constraints = project[0]["constraints"]
    print(f"Proposed project: {project_description}")
    print(f"Repository name: {repo_name}")
    print(f"Programming language: {programming_language}")
    print("")

    # Step 2: Propose tasks
    print("Step 2: Proposing tasks...")
    tasks = propose_tasks(project_description, constraints, model=model)
    print("Tasks proposed successfully.")
    print("")

    # Step 3: Set up project repository
    print("Step 3: Setting up project repository...")
    project_path = setup_repo(
        project_description=project_description,
        constraints=constraints,
        repo_name=repo_name,
        programming_language=programming_language,
        tasks=tasks,
        output_folder=output_folder,
    )
    print(f"Project initialized at: {project_path}")
    print("")

    # Step 3.5 Create Docker image for the project
    if docker:
        print("Step 3.5: Creating Docker image for the project...")
        image_tag = create_docker_image(project_path=project_path)
        print(f"Docker image created successfully at: {image_tag}")
        print("")

    # Step 4: Generate unit tests documentation
    print("Step 4: Generating unit tests documentation...")
    generate_unit_tests(project_path=project_path, model=model)
    print("Unit tests documentation generated successfully.")
    print("")

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
  python -m swe_play.propose.pipeline                                # Default settings
  python -m swe_play.propose.pipeline --model claude-sonnet-4-20250514
  python -m swe_play.propose.pipeline --output <folder>              # Custom output folder
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="LLM model to use for project proposal (default: claude-sonnet-4-20250514)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="generated",
        help="Output folder to save the project (default: generated)",
    )

    parser.add_argument(
        "--docker",
        type=bool,
        default=False,
        help="Whether to create a Docker image for the project (default: False)",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting project creation pipeline...\n")
        result = create_project_pipeline(
            model=args.model, output_folder=args.output, docker=args.docker
        )

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
