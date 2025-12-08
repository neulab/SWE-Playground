"""Repositroy Setup pipeline."""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from swe_play.propose.propose_tasks import generate_unit_tests
from swe_play.utils.call_openhands import call_openhands
from swe_play.utils.prompt_retriever import PromptRetriever
from swe_play.utils.task2json import convert_md_to_json


def setup_repo(
    project_description: str,
    constraints: str,
    repo_name: str,
    programming_language: str,
    tasks: str,
    output_folder: str,
) -> str:
    """Setup a project repository by calling OpenHands.

    Args:
        project_description: Description of the project to work on
        repo_name: Name for the repository directory
        programming_language: Programming language to use for the project
        tasks: Proposed tasks in markdown format
        output_folder: Output folder to save the project

    Returns:
        Path to the created project directory

    Raises:
        Exception: If initialization fails.
    """
    # Generate a unique project ID
    project_id = str(int(time.time()))

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
    Path(output_folder).mkdir(exist_ok=True)
    project_dir = (Path(output_folder) / repo_name).absolute()
    if project_dir.exists():
        raise Exception(f"Project directory already exists: {project_dir}")

    try:
        shutil.copytree(repo_starter_path, project_dir)
        print(f"Copied repo_starter template to: {project_dir}")
    except Exception as e:
        raise Exception(f"Failed to copy repo_starter template: {e}")

    # Write tasks to tasks.md and convert to tasks.json
    tasks_file = project_dir / "tasks.md"
    with open(tasks_file, "w") as f:
        f.write(tasks)
    convert_md_to_json(
        str(tasks_file),
        str(project_dir / "tasks.json"),
        project_name=repo_name,
        project_id=project_id,
        constraints=constraints,
    )
    print("Tasks written and converted successfully")

    prompt_retriever = PromptRetriever()
    setup_prompt = prompt_retriever.get_prompt(
        "setup-project-repo-openhands",
        project_description=project_description,
        constraints=constraints,
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


def create_docker_image(project_path: str) -> str:
    """Create a Docker image for the project.

    Args:
        project_path: The path of the project to create Docker image for

    Returns:
        docker_tag: The tag of the created Docker image

    Raises:
        Exception: If Docker image creation fails even after five times OpenHands fix attempt.
    """
    project_dir = Path(project_path)
    dockerfile_path = project_dir / "Dockerfile"
    if not dockerfile_path.exists():
        raise Exception(f"Dockerfile not found in {dockerfile_path}")

    tasks_file = project_dir / "tasks.json"
    with open(tasks_file, "r") as f:
        tasks = json.load(f)
    repo_name = tasks["project_name"]
    project_id = tasks["project_id"]

    image_tag = f"stephenzhu0218/swe-playground:swe-play_{repo_name.lower()}_{project_id}"

    def attempt_docker_build() -> tuple[bool, str, str]:
        """Attempt to build the docker image and return result and output."""
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
            print(f"Docker image built successfully for {repo_name} after {iter_cnt + 1} attempts.")
            try:
                # Push to Docker Hub
                subprocess.run(
                    ["docker", "push", image_tag],
                    cwd=str(project_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Image pushed to Docker Hub: {image_tag}")

                # Clean up local Docker images
                subprocess.run(
                    ["docker", "rmi", image_tag],
                    cwd=str(project_dir),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Cleaned up local image: {image_tag}")

            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to tag/push to Docker Hub: {e}")
                print("Continuing without Docker Hub push...")
            break

        iter_cnt += 1
        if iter_cnt >= 5:
            raise Exception(
                f"Failed to build Docker image for {repo_name} after {iter_cnt} attempts."
            )

        # Only last 1000 characters of stdout and stderr for fixing
        error_msgs = f"stdout:\n{stdout[-1000:]}\nstderr:\n{stderr[-1000:]}"
        prompt_retriever = PromptRetriever()
        fix_dockerfile_prompt = prompt_retriever.get_prompt(
            "fix-dockerfile-openhands",
            error_msgs=error_msgs,
        )
        try:
            openhands_output = call_openhands(
                prompt=fix_dockerfile_prompt, directory=str(project_dir)
            )
            print(f"OpenHands Dockerfile fix trial {iter_cnt} completed")
            print(f"OpenHands output: {openhands_output}")
        except Exception as e:
            raise Exception(f"OpenHands Dockerfile fix failed: {e}")

    return image_tag


def main() -> None:
    """CLI entry point for setting up the project repository."""
    parser = argparse.ArgumentParser(
        description="Set up the project repository for SWE-agent training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.propose.setup_repo                                 # Default settings
  python -m swe_play.propose.setup_repo --project-file /path/project.json
  python -m swe_play.propose.setup_repo --output /path/output           # Custom folder
  python -m swe_play.propose.setup_repo --docker                        # Create Docker image
        """,
    )

    parser.add_argument(
        "--project-file",
        type=str,
        default="",
        help="file of the proposed project (default: empty)",
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

    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help=(
            "LLM model to use for test documentation generation "
            "(default: claude-sonnet-4-20250514)"
        ),
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting project repo setup pipeline...\n")

        try:
            with open(args.project_file, "r") as f:
                project = json.load(f)
            project_description = project["project_description"]
            constraints = project["constraints"]
            repo_name = project["repo_name"]
            programming_language = project["programming_language"]
            tasks = project["tasks"]
        except Exception as e:
            raise Exception(f"Failed to load project file: {e}")

        project_path = setup_repo(
            project_description=project_description,
            constraints=constraints,
            repo_name=repo_name,
            programming_language=programming_language,
            tasks=tasks,
            output_folder=args.output,
        )

        print("\n✅ Successfully setup the project repository!")
        print(f"📁 Project repo setup at: {project_path}")

        if args.docker:
            image_tag = create_docker_image(project_path=project_path)
            print(f"📁 Docker image created at: {image_tag}")

        # Move test documentation after repository setup
        generate_unit_tests(project_path=project_path, model=args.model)

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
