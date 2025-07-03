"""Project proposal and initialization pipeline."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from swe_play.utils.call_openhands import call_openhands
from swe_play.utils.llm_client import create_llm_client
from swe_play.utils.prompt_retriever import PromptRetriever
from swe_play.utils.task2json import convert_md_to_json


def propose_project(model: str = "neulab/claude-sonnet-4-20250514") -> tuple[str, str, str]:
    """Propose a new project and repository name using the LLM.

    Args:
        model: The LLM model to use for project proposal.

    Returns:
        A tuple of (project_description, repo_name, programming_language)

    Raises:
        Exception: If project proposal fails or response format is invalid.
    """
    llm_client = create_llm_client(model=model)
    prompt_retriever = PromptRetriever()

    system_prompt = prompt_retriever.get_prompt("propose-next-project-system")
    user_prompt = prompt_retriever.get_prompt("propose-next-project-user")

    response = llm_client.system_completion(
        system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7
    )

    project_match = re.search(r"<proposed_project>(.*?)</proposed_project>", response, re.DOTALL)
    repo_match = re.search(r"<repo_name>(.*?)</repo_name>", response, re.DOTALL)
    language_match = re.search(
        r"<programming_language>(.*?)</programming_language>", response, re.DOTALL
    )

    if not project_match or not repo_match or not language_match:
        raise Exception(
            f"Invalid response format from LLM. Expected <proposed_project> and <repo_name> tags. "
            f"Got: {response}"
        )

    project_description = project_match.group(1).strip()
    repo_name = repo_match.group(1).strip()
    programming_language = language_match.group(1).strip()

    return project_description, repo_name, programming_language


def propose_tasks(
    project_description: str, repo_name: str, programming_language: str, project_id: str, max_tasks: int = 20
) -> str:
    """Propose tasks for the project by calling OpenHands.

    Args:
        project_description: Description of the project to work on
        repo_name: Name for the repository directory
        programming_language: Programming language to use for the project
        project_id: Project ID to use for the project
        max_tasks: Maximum number of tasks to generate (default: 20)

    Returns:
        Path to the created project directory

    Raises:
        Exception: If task proposal fails.
    """
    # Get the repo starter path based on the programming language
    current_dir = Path(__file__).parent.absolute()
    if programming_language.lower() == "python":
        repo_starter_path = current_dir / "repo_starter" / "python"
    elif programming_language.lower() == "c++":
        repo_starter_path = current_dir / "repo_starter" / "c++"
    elif programming_language.lower() == "rust":
        repo_starter_path = current_dir / "repo_starter" / "rust"
    elif programming_language.lower() == "javascript":
        repo_starter_path = current_dir / "repo_starter" / "javascript"
    else:
        raise Exception(f"Unsupported programming language: {programming_language}")
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
    task_proposal_prompt = prompt_retriever.get_prompt(
        "propose-tasks-openhands",
        project_task=project_description,
        max_tasks=max_tasks,
    )

    try:
        openhands_output = call_openhands(prompt=task_proposal_prompt, directory=str(project_dir))
        print(f"OpenHands task proposal completed for project: {repo_name}")
        print(f"OpenHands output: {openhands_output}")
        convert_md_to_json(str(project_dir / "tasks.md"), str(project_dir / "tasks.json"), project_name=repo_name, project_id=project_id)
    except Exception as e:
        # Clean up the directory if OpenHands fails
        shutil.rmtree(project_dir, ignore_errors=True)
        raise Exception(f"OpenHands task proposal failed: {e}")

    return str(project_dir)


def setup_project_repo(project_description: str, repo_name: str) -> str:
    """Setup a project repository by calling OpenHands.

    Args:
        project_description: Description of the project to work on

    Returns:
        Path to the created project directory

    Raises:
        Exception: If initialization fails.
    """
    current_dir = Path(__file__).parent.absolute()
    generated_dir = current_dir.parent.parent / "generated"
    project_dir = generated_dir / repo_name

    prompt_retriever = PromptRetriever()
    setup_prompt = prompt_retriever.get_prompt(
        "setup-project-repo-openhands",
        project_task=project_description,
    )

    try:
        openhands_output = call_openhands(prompt=setup_prompt, directory=str(project_dir))
        print(f"OpenHands setup completed for project: {repo_name}")
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        # Clean up the directory if OpenHands fails
        shutil.rmtree(project_dir, ignore_errors=True)
        raise Exception(f"OpenHands setup failed: {e}")

    return str(project_dir)


def generate_unit_tests(project_description: str, repo_name: str) -> None:
    """Generate unit tests for the project by calling OpenHands in the initialized repo.

    Args:
        repo_name: The name of the repository to create unit tests for

    Returns:
        None

    Raises:
        Exception: If unit tests creation fails.
    """
    current_dir = Path(__file__).parent.absolute()
    generated_dir = current_dir.parent.parent / "generated"
    project_dir = generated_dir / repo_name
    unit_tests_dir = project_dir / "tests"
    if unit_tests_dir.exists():
        shutil.rmtree(unit_tests_dir)
    unit_tests_dir.mkdir(parents=True, exist_ok=True)

    # Load task.json and extract all unit tests grouped by Task X.Y.Z
    task = json.load(open(project_dir / "tasks.json"))
    unit_tests_by_task = {}  # Dictionary to group tests by task number

    # Directly generate unit tests for the whole project frequently fails
    # Here we generate unit tests task by task
    # First group all unit tests by task number
    for phase in task.get("phases", []):
        for module in phase.get("modules", []):
            for task_item in module.get("tasks", []):
                task_number = task_item.get("task_number")
                unit_tests = task_item.get("unit_tests", {})
                code_tests = unit_tests.get("code_tests", [])
                visual_tests = unit_tests.get("visual_tests", [])

                # Only process tasks that have actual tests
                if code_tests or visual_tests:
                    # Combine all tests for this task X.Y.Z
                    all_tests_for_task = []
                    for test in code_tests:
                        all_tests_for_task.append(
                            {
                                "type": "code",
                                "name": test.get("name"),
                                "description": test.get("description"),
                            }
                        )
                    for test in visual_tests:
                        all_tests_for_task.append(
                            {
                                "type": "visual",
                                "name": test.get("name"),
                                "description": test.get("description"),
                            }
                        )

                    unit_tests_by_task[task_number] = {
                        "task_number": task_number,
                        "task_title": task_item.get("title"),
                        "task_description": task_item.get("description"),
                        "phase_number": phase.get("phase_number"),
                        "module_number": module.get("module_number"),
                        "all_tests": all_tests_for_task,
                        "total_tests": len(all_tests_for_task),
                    }

    # Then iterate over each task to generate unit tests
    for task_number, task_data in unit_tests_by_task.items():
        # Format the unit test prompt for the task
        print(f"Creating unit tests for task {task_number}...")
        test_prompt = f"Task {task_number}: {task_data['total_tests']} total tests\n"
        for test in task_data["all_tests"]:
            test_prompt += f"  - {test['type']}: {test['name']}\n"

        prompt_retriever = PromptRetriever()
        unit_tests_creation_prompt = prompt_retriever.get_prompt(
            "generate-unit-tests-openhands",
            project_task=project_description,
            unit_test_prompt=test_prompt,
        )

        try:
            openhands_output = call_openhands(
                prompt=unit_tests_creation_prompt, directory=str(project_dir)
            )
            print(f"OpenHands unit tests creation completed for project: {repo_name}")
            print(f"OpenHands output: {openhands_output}")
        except Exception as e:
            # Clean up the directory if OpenHands fails
            shutil.rmtree(project_dir, ignore_errors=True)
            raise Exception(f"OpenHands unit tests creation failed: {e}")


def create_docker_image(repo_name: str, project_id: str) -> None:
    """Create a Docker image for the project.

    Args:
        repo_name: The name of the repository to create Docker image for

    Returns:
        None

    Raises:
        Exception: If Docker image creation fails even after five times OpenHands fix attempt.
    """
    current_dir = Path(__file__).parent.absolute()
    generated_dir = current_dir.parent.parent / "generated"
    project_dir = generated_dir / repo_name
    dockerfile_path = project_dir / "Dockerfile"
    if not dockerfile_path.exists():
        raise Exception(f"Dockerfile not found in {dockerfile_path}")

    def attempt_docker_build() -> tuple[bool, str, str]:
        """Attempt to build the docker image and return result and output."""
        image_tag = f"swe-play/{repo_name.lower()}:{project_id}"
        try:
            result = subprocess.run(
                ["docker", "build", "-t", image_tag, "."],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout if e.stdout else "", e.stderr if e.stderr else ""

    iter_cnt = 0
    while True:
        success, stdout, stderr = attempt_docker_build()
        if success:
            print(f"Docker image built successfully for {repo_name} after {iter_cnt+1} attempts.")
            break
        iter_cnt += 1
        if iter_cnt >= 5:
            raise Exception(
                f"Failed to build Docker image for {repo_name} after {iter_cnt} attempts."
            )

        # Only last 1000 characters of stdout and stderr for fixing
        error_msgs = f"stdout:\n{stdout[-1000:]}\nstderr:\n{stderr[-1000:]}"
        prompt_retriever = PromptRetriever()
        initialization_prompt = prompt_retriever.get_prompt(
            "fix-dockerfile-openhands",
            error_msgs=error_msgs,
        )
        try:
            openhands_output = call_openhands(
                prompt=initialization_prompt, directory=str(project_dir)
            )
            print(f"OpenHands Dockerfile fix trial {iter_cnt} completed")
            print(f"OpenHands output: {openhands_output}")
        except Exception as e:
            raise Exception(f"OpenHands Dockerfile fix failed: {e}")


def create_project_pipeline(
    max_tasks: int = 20, model: str = "neulab/claude-sonnet-4-20250514"
) -> dict[str, str]:
    """Complete pipeline to propose and initialize a new project.

    Args:
        max_tasks: Maximum number of tasks to generate (default: 20)
        model: The LLM model to use for project proposal
               (default: neulab/claude-sonnet-4-20250514)

    Returns:
        Dictionary containing project details:
        - project_description: The proposed project description
        - repo_name: The repository name
        - project_path: Path to the created project directory

    Raises:
        Exception: If any step in the pipeline fails.
    """
    project_id = str(int(time.time()))
    print("Starting project proposal and initialization pipeline...")
    print("")

    # Step 1: Propose project
    print("Step 1: Proposing project...")
    project_description, repo_name, programming_language = propose_project(model=model)
    print(f"Proposed project: {project_description}")
    print(f"Repository name: {repo_name}")
    print(f"Programming language: {programming_language}")
    print("")

    # Step 2: Propose tasks
    print("Step 2: Proposing tasks...")
    project_path = propose_tasks(project_description, repo_name, programming_language, project_id, max_tasks)
    print("Tasks proposed successfully.")
    print("")

    # Step 3: Initialize project repository
    print("Step 3: Initializing project repository...")
    project_path = setup_project_repo(project_description, repo_name)
    print(f"Project initialized at: {project_path}")
    print("")

    # Step 3.5 Create Docker image for the project
    print("Step 3.5: Creating Docker image for the project...")
    create_docker_image(repo_name, project_id)
    print("Docker image created successfully.")
    print("")

    # Step 4: Create unit tests
    print("Step 4: Generating unit tests...")
    generate_unit_tests(project_description, repo_name)
    print("Unit tests generated successfully.")
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
        help="LLM model to use for project proposal " "(default: neulab/claude-sonnet-4-20250514)",
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
