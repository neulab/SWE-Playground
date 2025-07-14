"""Rollout pipeline for automated project task completion and testing."""

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path

from swe_play.utils.call_openhands import call_openhands, call_openhands_rollout
from swe_play.utils.convert_data import convert_data
from swe_play.utils.prompt_retriever import PromptRetriever


def generate_unit_test(
    task_number: str, task_data: dict, project_dir: Path, project_description: str
) -> None:
    """Generate unit tests for a specific task using OpenHands.

    Args:
        task_number: The task number (e.g., "1.2.3")
        task_data: Dictionary containing task information including tests and descriptions
        project_dir: Path to the project directory where tests will be generated
        project_description: Description of the overall project

    Raises:
        Exception: If OpenHands unit test creation fails
    """
    unit_tests_dir = project_dir / "tests"

    test_prompt = f"Task {task_number}: {task_data['total_tests']} total tests\n"
    for test in task_data["all_tests"]:
        test_prompt += f"  - {test['type']}: {test['name']}\n"
    with open(unit_tests_dir / f"{task_number}.md", "r") as f:
        test_prompt += f"The detailed unit tests proposal:\n\n{f.read()}"

    prompt_retriever = PromptRetriever()
    unit_test_creation_prompt = prompt_retriever.get_prompt(
        "generate-unit-test-openhands",
        project_task=project_description,
        unit_test_prompt=test_prompt,
    )

    try:
        openhands_output = call_openhands(
            prompt=unit_test_creation_prompt, directory=str(project_dir)
        )
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        raise Exception(f"OpenHands unit tests creation failed: {e}")

    print("Continue generating...")
    unit_test_creation_continue_prompt = prompt_retriever.get_prompt(
        "generate-unit-test-continue-openhands",
        project_task=project_description,
        unit_test_prompt=test_prompt,
    )

    try:
        openhands_output = call_openhands(
            prompt=unit_test_creation_continue_prompt, directory=str(project_dir)
        )
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        raise Exception(f"OpenHands unit tests creation failed: {e}")


def finish_task(
    task_number: str,
    project_description: str,
    constraints: str,
    project_dir: Path,
    current_dir: Path,
) -> None:
    """Complete a task implementation using OpenHands.

    Args:
        task_number: The task number to complete (e.g., "1.2.3")
        project_description: Description of the overall project
        constraints: Project constraints and requirements
        project_dir: Path to the project directory
        current_dir: Path to the current runtime directory for output

    Raises:
        Exception: If OpenHands task completion fails
    """
    prompt_retriever = PromptRetriever()
    finish_task_prompt = prompt_retriever.get_prompt(
        "finish-task-openhands",
        task_number=task_number,
        project_description=project_description,
        constraints=constraints,
    )
    try:
        openhands_output = call_openhands_rollout(
            prompt=finish_task_prompt,
            directory=str(project_dir),
            output_dir=str(current_dir),
        )
        print("OpenHands successfully finish the task")
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        raise Exception(f"OpenHands setup failed: {e}")


def check_unit_test_diff(
    unit_test_tests_dir: Path, implementation_tests_dir: Path, all_tasks: list[str]
) -> bool:
    """Check if unit tests have been modified between unit test and implementation phases.

    Compares test files between the unit test generation phase and the implementation phase
    to ensure tests haven't been inadvertently modified during implementation.

    Args:
        unit_test_tests_dir: Path to the unit test directory
        implementation_tests_dir: Path to the implementation test directory
        all_tasks: List of all task numbers to check

    Returns:
        True if no differences found in unit tests, False otherwise

    Raises:
        Exception: If diff command execution fails
    """
    flag = True

    for task_number in all_tasks:
        task_number_str = task_number.replace(".", "_")

        bash_script_path_unit_test = unit_test_tests_dir / "tests" / f"{task_number}.sh"
        bash_script_path_implementation = implementation_tests_dir / "tests" / f"{task_number}.sh"
        python_file_path_unit_test = unit_test_tests_dir / "tests" / f"test_{task_number_str}.py"
        python_file_path_implementation = (
            implementation_tests_dir / "tests" / f"test_{task_number_str}.py"
        )

        try:
            result_bash = subprocess.run(
                [
                    "diff",
                    "-u",
                    str(bash_script_path_unit_test),
                    str(bash_script_path_implementation),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            result_python = subprocess.run(
                [
                    "diff",
                    "-u",
                    str(python_file_path_unit_test),
                    str(python_file_path_implementation),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result_bash.returncode != 0 or result_python.returncode != 0:
                print(f"Differences found in unit tests of Task {task_number}.")
                flag = False
        except Exception as e:
            raise Exception(f"Error running diff: {e}")

    if flag:
        print("No differences found in unit tests of all tasks.")

    return flag


def run_unit_tests(project_dir: Path, all_tasks: list[str]) -> bool:
    """Run the unit tests for all tasks in the specified project directory.

    Args:
        project_dir: The Path to the project directory
        all_tasks: List of all task numbers to test

    Returns:
        True if all tests pass, False otherwise

    Raises:
        Exception: If test script does not exist
    """
    for task in all_tasks:
        test_script = project_dir / "tests" / f"{task}.sh"
        if not test_script.exists():
            raise Exception(f"Test script {test_script} does not exist.")

        result = subprocess.run(
            ["bash", str(test_script)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"Unit test for task {task} successfully executed and passed.")
        else:
            print(f"Unit test failed for task {task}.")
            return False

    return True


def main(repo_path: str, runtime_folder: str) -> None:
    """Main rollout pipeline for automated project task completion.

    Executes a complete rollout pipeline that:
    1. Loads project configuration and task definitions
    2. For each task with unit tests:
       - Generates unit tests using OpenHands
       - Implements the task using OpenHands
       - Validates implementation against unit tests
       - Retries up to 3 times if tests fail
    3. Continues until all tasks are completed or maximum retries exceeded

    Args:
        repo_path: The path of the project repository to process
        runtime_folder: The folder to save the runtime data

    Raises:
        Exception: If project configuration cannot be loaded or critical failures occur
    """
    project_dir = Path(repo_path)
    runtime_dir = Path(runtime_folder) / f"runtime_{str(int(time.time()))}"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    with open(project_dir / "tasks.json", "r") as f:
        task = json.load(f)
    project_name = task["project_name"]
    project_description = task["project_description"]
    constraints = task["constraints"]

    unit_tests_by_task = {}  # Dictionary to group tests by task number

    for phase in task["phases"]:
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

    all_tasks: list[str] = []
    tasks_cnt = 0
    # Then iterate over each task to generate unit tests
    for task_number, task_data in unit_tests_by_task.items():
        # First visit the current task when running unit tests
        all_tasks.insert(0, task_number)

        print(f"\nRunning pipeline for task {task_number}...")

        iter_cnt = 1
        while True:
            print(f"Trial {iter_cnt} for task {task_number}...")
            # Generate unit test
            # Copy the project directory to the runtime_dir
            project_dir_unit_test = runtime_dir / f"{project_name}_{task_number}_unit_test"
            save_dir = runtime_dir / f"log_{task_number}"
            shutil.copytree(project_dir, project_dir_unit_test)
            print("Calling Openhands to generate unit test...")
            generate_unit_test(task_number, task_data, project_dir_unit_test, project_description)

            # Rollout data
            # First we employ OpenHands to finish the task
            project_dir_implementation = (
                runtime_dir / f"{project_name}_{task_number}_implementation"
            )

            shutil.copytree(project_dir_unit_test, project_dir_implementation)
            print("Calling Openhands to finish the task...")
            finish_task(
                task_number,
                project_description,
                constraints,
                project_dir_implementation,
                save_dir,
            )
            # Then run the unit tests to check correctness
            # Call the function to check for unit test modifications
            res_diff = check_unit_test_diff(
                project_dir_unit_test, project_dir_implementation, all_tasks
            )
            if not res_diff:
                # Copy the unit tests from unit_test to implementation
                unit_test_tests_dir = project_dir_unit_test / "tests"
                implementation_tests_dir = project_dir_implementation / "tests"
                shutil.rmtree(implementation_tests_dir)
                shutil.copytree(unit_test_tests_dir, implementation_tests_dir)

            # Then run the unit tests to check correctness
            res_test = run_unit_tests(project_dir_implementation, all_tasks)
            if res_test:
                tasks_cnt += 1
                convert_data(str(runtime_dir), str(save_dir), task_number)
                break
            else:
                print("Unit test failed for the current task. Conduct another trial.")
                iter_cnt += 1
                if iter_cnt > 3:
                    print(
                        f"Three trials failed for the current task. "
                        f"Project exits with {tasks_cnt} tasks finished."
                    )
                    exit(0)
                shutil.rmtree(project_dir_implementation)
                shutil.rmtree(project_dir_unit_test)

        project_dir = project_dir_implementation

    print(f"Rollout pipeline completed successfully. Totally {tasks_cnt} tasks finished.")


if __name__ == "__main__":
    """CLI entry point for the rollout pipeline.
    
    Parses command line arguments and executes the rollout pipeline for a specified
    project repository. The pipeline processes tasks sequentially, generating unit tests
    and implementing functionality using OpenHands.
    """
    parser = argparse.ArgumentParser(
        description="Run OpenHands to generate unit tests and finish the project task by task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.rollout.rollout --repo-path /path/to/my_project    # Run rollout for my_project
        """,
    )

    parser.add_argument(
        "--repo-path",
        type=str,
        required=True,
        help="The path of the project repository",
    )

    parser.add_argument(
        "--runtime-folder",
        type=str,
        default="runtimes",
        help="The folder to save the runtime data",
    )

    args = parser.parse_args()

    main(args.repo_path, args.runtime_folder)
