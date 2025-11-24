"""Rollout pipeline for Commit-0 specific generation."""

import argparse
import json
import re
import shutil
from pathlib import Path

from swe_play.utils.call_openhands import call_openhands_rollout
from swe_play.utils.convert_data import convert_data
from swe_play.utils.prompt_retriever import PromptRetriever


def replace_function_bodies_with_pass(project_dir: Path) -> None:
    """Replace NotImplementedError statements with 'pass' in Python files under /src directory.

    Args:
        project_dir: Path to the project directory
    """
    src_dir = project_dir / "src"
    if not src_dir.exists():
        print(
            f"Source directory {src_dir} does not exist, skipping NotImplementedError replacement"
        )
        return

    print(f"Replacing NotImplementedError statements with 'pass' in {src_dir}")

    # Find all Python files in src directory recursively
    python_files = list(src_dir.rglob("*.py"))

    if not python_files:
        print(f"No Python files found in {src_dir}")
        return

    files_modified = 0
    total_replacements = 0

    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            modified = False

            # Replace 'raise NotImplementedError' with 'pass'
            patterns_to_replace = [
                (r"raise\s+NotImplementedError\s*\([^)]*\)", "pass"),
                (r"raise\s+NotImplementedError\s*$", "pass"),
                (r"raise\s+NotImplementedError\s+", "pass"),
            ]

            for pattern, replacement in patterns_to_replace:
                if re.search(pattern, content, re.MULTILINE):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    modified = True

            if modified:
                with open(py_file, "w", encoding="utf-8") as f:
                    f.write(content)
                files_modified += 1
                total_replacements += 1
                print(f"  Modified {py_file.relative_to(project_dir)}")

        except Exception as e:
            print(f"  Error processing {py_file}: {e}")

    print(f"Completed NotImplementedError replacement: {files_modified} files modified")


def cleanup_test_files(project_dir: Path, all_task_data: dict) -> None:
    """Clean up test files by removing bash scripts and renaming Python test files for all tasks.

    Args:
        project_dir: Path to the project directory
        all_task_data: Dictionary containing all task information keyed by task_number
    """
    tests_dir = project_dir / "tests"
    if not tests_dir.exists():
        print(f"Tests directory {tests_dir} does not exist, skipping cleanup")
        return

    print(f"Cleaning up test files for all tasks in {tests_dir}")

    for task_number, task_data in all_task_data.items():
        task_title = task_data.get("task_title", "")

        # Convert task_number format for file operations (replace dots with underscores)
        task_number_file = task_number.replace(".", "_")

        # Remove bash test script
        bash_script = tests_dir / f"{task_number}.sh"
        if bash_script.exists():
            bash_script.unlink()

        # Remove bash test script
        markdown_script = tests_dir / f"{task_number}.md"
        if markdown_script.exists():
            markdown_script.unlink()

        # Rename Python test file using task title (without "test_" prefix)
        python_test_file = tests_dir / f"test_{task_number_file}.py"
        if python_test_file.exists() and task_title:
            # Clean task title for filename; strip special chars and replace spaces
            clean_title = re.sub(r"[^\w\s-]", "", task_title).strip()
            clean_title = re.sub(r"[-\s]+", "_", clean_title).lower()
            new_python_file = tests_dir / f"test_{clean_title}.py"

            # Avoid name conflicts
            counter = 1
            while new_python_file.exists() and new_python_file != python_test_file:
                new_python_file = tests_dir / f"{clean_title}_{counter}.py"
                counter += 1

            if new_python_file != python_test_file:
                python_test_file.rename(new_python_file)
                print(f"Renamed Python test file: {python_test_file} -> {new_python_file}")

    print("Completed test file cleanup for all tasks")


def finish_commit0(
    project_name: str,
    project_dir: Path,
    log_dir: Path,
) -> None:
    """Fix an issue in the codebase using OpenHands.

    Takes a buggy codebase with a known issue and attempts to fix it using OpenHands.
    This completes the SWE-bench pipeline by having an agent solve the generated problem.

    Args:
        project_name: The name of the project
        project_dir: Path to the project directory containing the buggy code
        log_dir: Path to the log directory

    Raises:
        Exception: If OpenHands issue fixing fails
    """
    prompt_retriever = PromptRetriever()
    fix_issue_prompt = prompt_retriever.get_prompt(
        "finish-full-openhands",
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


def main(repo_path: str, runtime_folder: str, num_iterations: int = 1) -> None:
    project_dir = Path(repo_path)
    runtime_dir = Path(runtime_folder)

    with open(project_dir / "tasks.json", "r") as f:
        task = json.load(f)
    project_name = task["project_name"]

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

    # Find the last task with valid unit test and implementation logs
    last_valid_task = None

    for task_number, task_data in unit_tests_by_task.items():
        check_path_implementation = (
            runtime_dir / "converted_data" / f"{task_number}_implementation.json"
        )
        check_path_unit_test = runtime_dir / "converted_data" / f"{task_number}_unit_test.json"
        if check_path_implementation.exists() and check_path_unit_test.exists():
            last_valid_task = task_number
        else:
            continue

    if last_valid_task is None:
        print("❌ No tasks found with valid unit test and implementation logs.")
        return

    print(f"🎯 Executing pipeline for the last valid task: {last_valid_task}")
    print(f"🔄 Running {num_iterations} iteration(s)")

    # Only process the last valid task
    task_number = last_valid_task

    # Generate raw data once (same for all iterations)
    print(f"\n📦 Preparing raw data for project {project_name} and task {task_number}...")
    init_repo_dir = Path("/home/yiqiz2/SWE-Playground/generated") / f"{project_name}"
    gt_implementation_tests_dir = (
        runtime_dir / f"{project_name}_{task_number}_implementation" / "tests"
    )

    # Create the raw data directory (shared across all iterations)
    commit0_raw_dir = runtime_dir / "commit0_raw" / f"{project_name}"
    if commit0_raw_dir.exists():
        shutil.rmtree(commit0_raw_dir)
    shutil.copytree(init_repo_dir, commit0_raw_dir)
    commit0_raw_tests_dir = commit0_raw_dir / "tests"
    if commit0_raw_tests_dir.exists():
        shutil.rmtree(commit0_raw_tests_dir)
    shutil.copytree(gt_implementation_tests_dir, commit0_raw_tests_dir)

    # Replace all function bodies with pass while preserving docstrings in /src directory
    replace_function_bodies_with_pass(commit0_raw_dir)
    cleanup_test_files(commit0_raw_dir, unit_tests_by_task)
    print("✅ Raw data preparation completed!")

    # Run the pipeline for the specified number of iterations
    for iteration in range(1, num_iterations + 1):
        print(f"\n{'='*60}")
        print(f"🚀 Starting iteration {iteration}/{num_iterations}")
        print(f"{'='*60}")

        print(
            "\nRunning pipeline iteration "
            f"{iteration} for project {project_name} and task {task_number}..."
        )

        # Create iteration-specific commit0 directory from the shared raw data
        if num_iterations == 1:
            commit0_dir = runtime_dir / "commit0" / f"{project_name}"
            commit0_dir_openhands = runtime_dir / "commit0"
            log_dir = runtime_dir / f"log_{task_number}_commit0"
        else:
            commit0_dir = runtime_dir / f"commit0_iter{iteration}" / f"{project_name}"
            commit0_dir_openhands = runtime_dir / f"commit0_iter{iteration}"
            log_dir = runtime_dir / f"log_{task_number}_commit0_iter{iteration}"

        if commit0_dir.exists():
            shutil.rmtree(commit0_dir)
        shutil.copytree(commit0_raw_dir, commit0_dir)

        try:
            finish_commit0(project_name, commit0_dir_openhands, log_dir)
            if num_iterations == 1:
                convert_data(str(runtime_dir), str(log_dir), "commit0", "commit0")
            else:
                convert_data(str(runtime_dir), str(log_dir), "commit0", f"commit0_iter{iteration}")
            print(f"✅ Iteration {iteration} completed successfully!")
        except Exception as e:
            print(f"❌ Iteration {iteration} failed: {e}")
            print("Continuing with next iteration...")
            continue

    print(f"\n{'='*60}")
    print(
        f"🎉 All iterations completed! Ran {num_iterations} iteration(s) for project {project_name}"
    )
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Finish the project from scratch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.rollout.commit0 --repo-path /path/to/my_project
      --runtime-folder /path/to/runtime                        # Run once
  python -m swe_play.rollout.commit0 --repo-path /path/to/my_project
      --runtime-folder /path/to/runtime --num-iterations 5     # Run 5 times
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

    parser.add_argument(
        "--num-iterations",
        type=int,
        default=1,
        help="Number of times to run the data generation pipeline (default: 1)",
    )

    args = parser.parse_args()

    main(args.repo_path, args.runtime_folder, args.num_iterations)
