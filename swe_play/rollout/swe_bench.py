"""Rollout pipeline for SWE-bench specific generation."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from swe_play.utils.call_openhands import call_openhands_rollout
from swe_play.utils.convert_data import convert_data
from swe_play.utils.llm_client import create_llm_client
from swe_play.utils.prompt_retriever import PromptRetriever


def propose_issue(
    task_data: dict,
    project_description: str,
    project_dir: Path,
    task_number: str,
    model: str = "claude-sonnet-4-20250514",
) -> tuple[str, str]:
    """Generate both technical issue and user-friendly description for a specific task.

    Args:
        task_data: Dictionary containing task information including tests and descriptions
        project_description: Description of the overall project
        project_dir: Path to the project directory
        task_number: The task number
        model: The LLM model to use for issue proposal

    Returns:
        tuple[str, str]: (technical_issue, user_description) where:
            - technical_issue: Technical description for applying the bug to code
            - user_description: User-friendly bug report like a GitHub issue

    Raises:
        Exception: If OpenHands issue proposal fails
    """
    unit_tests_dir = project_dir / "tests"

    test_prompt = f"Task {task_number}: {task_data['total_tests']} total tests\n"
    for test in task_data["all_tests"]:
        test_prompt += f"  - {test['type']}: {test['name']}\n"
    with open(unit_tests_dir / f"{task_number}.md", "r") as f:
        test_prompt += f"The detailed unit tests proposal:\n\n{f.read()}"

    task_number = task_number.replace(".", "_")
    code_file = project_dir / "tests" / f"test_{task_number}.py"
    if not code_file.exists():
        raise Exception(f"Code file {code_file} does not exist")
    with open(code_file, "r") as f:
        test_code = f.read()

    llm_client = create_llm_client(model=model)
    prompt_retriever = PromptRetriever()

    system_prompt = prompt_retriever.get_prompt("propose-issue-system")
    user_prompt = prompt_retriever.get_prompt(
        "propose-issue-user",
        project_description=project_description,
        test_code=test_code,
        test_prompt=test_prompt,
    )

    print("Calling LLM to propose issues in SWE-bench format...")
    response = llm_client.system_completion(
        system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7
    )

    # Extract technical issue for applying bug
    issue_pattern = r"<issue>(.*?)</issue>"
    issue_matches = re.findall(issue_pattern, response, re.DOTALL)

    # Extract user-friendly description for fixing bug
    description_pattern = r"<description>(.*?)</description>"
    description_matches = re.findall(description_pattern, response, re.DOTALL)

    if not issue_matches or not description_matches:
        raise Exception("LLM response missing required <issue> or <description> tags")

    technical_issue = issue_matches[0].strip()
    user_description = description_matches[0].strip()

    return technical_issue, user_description


def apply_issue(
    issue_description: str,
    project_dir: Path,
    project_description: str,
    task_data: dict,
    task_number: str,
) -> None:
    """Apply an issue to the codebase using OpenHands.

    Takes a generated issue description and applies it to the working codebase,
    introducing the described bug/problem to create a SWE-bench style problem.

    Args:
        issue_description: The natural language description of the issue to apply
        project_dir: Path to the project directory where issue should be applied
        project_description: Description of the overall project
        task_data: Dictionary containing task information
        task_number: The task number (e.g., "1.2.3")

    Raises:
        Exception: If OpenHands issue application fails
    """
    prompt_retriever = PromptRetriever()
    apply_issue_prompt = prompt_retriever.get_prompt(
        "apply-issue-openhands",
        issue_description=issue_description,
        project_description=project_description,
        task_number=task_number,
        task_description=task_data.get("task_description", ""),
    )

    try:
        openhands_output = call_openhands_rollout(
            prompt=apply_issue_prompt,
            directory=str(project_dir),
        )
        print("OpenHands successfully applied the issue")
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        raise Exception(f"OpenHands issue application failed: {e}")


def fix_issue(
    issue_description: str,
    project_name: str,
    project_dir: Path,
    log_dir: Path,
) -> None:
    """Fix an issue in the codebase using OpenHands.

    Takes a buggy codebase with a known issue and attempts to fix it using OpenHands.
    This completes the SWE-bench pipeline by having an agent solve the generated problem.

    Args:
        issue_description: The natural language description of the issue to fix
        project_name: The name of the project
        project_dir: Path to the project directory containing the buggy code
        log_dir: Path to the log directory

    Raises:
        Exception: If OpenHands issue fixing fails
    """
    prompt_retriever = PromptRetriever()
    fix_issue_prompt = prompt_retriever.get_prompt(
        "fix-issue-openhands",
        issue_description=issue_description,
        workspace_dir_name=project_name,
    )

    try:
        openhands_output = call_openhands_rollout(
            prompt=fix_issue_prompt,
            directory=str(project_dir),
            output_dir=str(log_dir),
        )
        print("OpenHands completed the fix attempt")
        print(f"OpenHands output: {openhands_output}")
    except Exception as e:
        raise Exception(f"OpenHands issue fixing failed: {e}")


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
            # Debug: Show what files actually exist in the tests directory
            tests_dir = project_dir / "tests"
            if tests_dir.exists():
                existing_files = list(tests_dir.iterdir())
                print(f"Tests directory {tests_dir} exists but does not contain {task}.sh")
                print(f"Available files in tests directory: {existing_files}")
            else:
                print(f"Tests directory {tests_dir} does not exist")
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
    project_dir = Path(repo_path)
    runtime_dir = Path(runtime_folder)

    with open(project_dir / "tasks.json", "r") as f:
        task = json.load(f)
    project_name = task["project_name"]
    project_description = task["project_description"]

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
    # Then iterate over each task to fix
    for task_number, task_data in unit_tests_by_task.items():
        check_path_fix = runtime_dir / "converted_data" / f"{task_number}_fix.json"
        if check_path_fix.exists():
            print(f"⚠️  Skipping task {task_number} because it already has a fix.")
            continue

        check_path_implementation = (
            runtime_dir / "converted_data" / f"{task_number}_implementation.json"
        )
        check_path_unit_test = runtime_dir / "converted_data" / f"{task_number}_unit_test.json"
        if not check_path_implementation.exists() or not check_path_unit_test.exists():
            break

        # First visit the current task when running unit tests
        all_tasks.insert(0, task_number)

        print(f"\nRunning pipeline for task {task_number}...")

        iter_cnt = 1
        max_retries = 3

        while iter_cnt <= max_retries:
            print(f"Trial {iter_cnt} for task {task_number}...")

            # Propose issue
            gt_implementation_dir = runtime_dir / f"{project_name}_{task_number}_implementation"
            issue, description = propose_issue(
                task_data, project_description, gt_implementation_dir, task_number
            )

            # Apply issue to create buggy version
            issue_dir = runtime_dir / f"{project_name}_{task_number}_issue"
            if issue_dir.exists():
                shutil.rmtree(issue_dir)
            shutil.copytree(gt_implementation_dir, issue_dir)
            apply_issue(issue, issue_dir, project_description, task_data, task_number)

            # Verify that issue was successfully applied by running tests (they should fail)
            print(f"Verifying issue application for task {task_number}...")
            tests_pass = run_unit_tests(issue_dir, [task_number])

            if not tests_pass:
                print(
                    "✅ Issue successfully applied for task "
                    f"{task_number} - tests are now failing as expected"
                )

                # Now attempt to fix the issue using OpenHands
                print(f"Attempting to fix issue for task {task_number}...")
                fix_dir = runtime_dir / f"{project_name}_{task_number}_fix" / f"{project_name}"
                fix_dir_openhands = runtime_dir / f"{project_name}_{task_number}_fix"
                if fix_dir.exists():
                    shutil.rmtree(fix_dir)
                shutil.copytree(issue_dir, fix_dir)
                log_dir = runtime_dir / f"log_{task_number}_fix"

                # Remove the tests directory from fix_dir before running fix_issue
                fix_tests_dir = fix_dir / "tests"
                if fix_tests_dir.exists() and fix_tests_dir.is_dir():
                    shutil.rmtree(fix_tests_dir)

                fix_issue(description, project_name, fix_dir_openhands, log_dir)

                # Restore tests directory for validation
                fix_tests_dir = fix_dir / "tests"
                if fix_tests_dir.exists():
                    shutil.rmtree(fix_tests_dir)
                shutil.copytree(issue_dir / "tests", fix_dir / "tests")

                # Validate that the fix worked
                print(f"Validating fix for task {task_number}...")
                fix_tests_pass = run_unit_tests(fix_dir, [task_number])

                if fix_tests_pass:
                    print(
                        f"🎉 Issue successfully fixed for task {task_number} - all tests now pass!"
                    )
                    convert_data(str(runtime_dir), str(log_dir), task_number, "fix")
                    tasks_cnt += 1
                else:
                    print(f"⚠️  Fix attempt failed for task {task_number} - tests still failing")
                    if iter_cnt >= max_retries:
                        print(
                            "⚠️  Maximum retries reached for task "
                            f"{task_number}. Skipping this task."
                        )
                        break
                    iter_cnt += 1
                break
            else:
                print(
                    "❌ Issue application failed for task "
                    f"{task_number} - tests still pass (trial {iter_cnt}/{max_retries})"
                )
                if iter_cnt >= max_retries:
                    print(f"⚠️  Maximum retries reached for task {task_number}. Skipping this task.")
                    break
                iter_cnt += 1

    print(f"SWE-bench pipeline completed successfully. Totally {tasks_cnt} tasks finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Propose issues and fix them in the project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.rollout.swe_bench --repo-path /path/to/my_project
      --runtime-folder /path/to/runtime     # Run rollout for my_project
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
