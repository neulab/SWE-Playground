"""Project proposal and initialization pipeline."""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from swe_play.utils.llm_client import create_llm_client
from swe_play.utils.prompt_retriever import PromptRetriever


def propose_tasks(
    project_description: str, constraints: str, model: str = "neulab/claude-sonnet-4-20250514"
) -> str:
    """Propose tasks for the project by calling OpenHands.

    Args:
        project_description: Description of the project to work on
        constraints: Constraints for the project
        model: The LLM model to use for task proposal

    Returns:
        Proposed tasks in markdown format

    Raises:
        Exception: If task proposal fails.
    """
    llm_client = create_llm_client(model=model)
    prompt_retriever = PromptRetriever()

    system_prompt = prompt_retriever.get_prompt("propose-tasks-system")
    user_prompt = prompt_retriever.get_prompt(
        "propose-tasks-user",
        project_description=project_description,
        constraints=constraints,
    )

    print("Calling LLM to propose tasks for the project...")
    response = llm_client.system_completion(
        system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7
    )

    # Check if we have a complete response with both opening and closing tags
    has_opening_tag = "<tasks>" in response
    has_closing_tag = "</tasks>" in response

    # Output window of claude-sonnet-4 (maybe similar for other models) is not long enough
    # So we need to ask the model to continue the response when the output is truncated
    # If we have opening tag but no closing tag, the response might be truncated
    # Then we need to ask the model to continue the response
    # Two times should be enough, and more typically mean error
    if has_opening_tag and not has_closing_tag:
        print("Response appears to be truncated, asking model to continue...")
        continue_user_prompt = prompt_retriever.get_prompt(
            "propose-tasks-user-continue",
            project_description=project_description,
            constraints=constraints,
            response=response,
        )
        continuation_response = llm_client.system_completion(
            system_prompt=system_prompt, user_prompt=continue_user_prompt, temperature=0.7
        )
        response += continuation_response
        if not has_closing_tag:
            raise Exception("Warning: Could not get complete response even after continuation")

    tasks_match = re.search(r"<tasks>(.*?)</tasks>", response, re.DOTALL)
    if not tasks_match:
        raise Exception(
            f"Invalid response format from LLM. Expected <tasks> tag. " f"Got: {response}"
        )

    tasks = tasks_match.group(1).strip()
    return tasks


def generate_unit_tests(project_path: str, model: str = "neulab/claude-sonnet-4-20250514") -> None:
    """Generate unit tests documentation for the project.

    Uses OpenHands to create documentation in the initialized repo.

    Args:
        project_path: The path to the project to create unit tests documentation for

    Returns:
        None

    Raises:
        Exception: If unit tests documentation generation fails.
    """
    unit_tests_dir = Path(project_path) / "tests"
    if unit_tests_dir.exists():
        shutil.rmtree(unit_tests_dir)
    unit_tests_dir.mkdir(parents=True, exist_ok=True)

    task = json.load(open(Path(project_path) / "tasks.json"))
    tasks_prompt = open(Path(project_path) / "tasks.md").read()
    unit_tests_by_task = {}
    project_description = task.get("project_description")

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

    # Then iterate over each task to generate unit tests documentation
    previous_unit_tests = ""
    for task_number, task_data in unit_tests_by_task.items():
        # Format the unit test prompt for the task
        print(f"Generating unit test documentation for task {task_number}...")
        unit_test_prompt = f"Task {task_number}: {task_data['total_tests']} total tests\n"
        for test in task_data["all_tests"]:
            unit_test_prompt += f"  - {test['type']}: {test['name']}\n"

        llm_client = create_llm_client(model=model)
        prompt_retriever = PromptRetriever()

        system_prompt = prompt_retriever.get_prompt("unit-test-system")
        user_prompt = prompt_retriever.get_prompt(
            "unit-test-user",
            project_description=project_description,
            tasks_prompt=tasks_prompt,
            previous_unit_tests=previous_unit_tests,
            unit_test_prompt=unit_test_prompt,
        )

        print("Calling LLM to generate unit tests documentation for the project...")
        response = llm_client.system_completion(
            system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7
        )

        with open(unit_tests_dir / f"{task_number}.md", "w") as f:
            f.write(response)
        previous_unit_tests += f"{unit_test_prompt}\n\n"


def main() -> None:
    """CLI entry point for proposing tasks for a project."""
    parser = argparse.ArgumentParser(
        description="Propose tasks for a project for SWE-agent training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.propose.propose_tasks                           # Default settings
  python -m swe_play.propose.propose_tasks --model gpt-4o            # Custom model
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default="neulab/claude-sonnet-4-20250514",
        help="LLM model to use for project proposal (default: neulab/claude-sonnet-4-20250514)",
    )

    parser.add_argument(
        "--project-file",
        type=str,
        default="",
        help="file of the proposed project (default: empty)",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting tasks proposal pipeline...\n")

        try:
            with open(args.project_file, "r") as f:
                project = json.load(f)
            project_description = project["project_description"]
            constraints = project["constraints"]
        except Exception as e:
            raise Exception(f"Failed to load project file: {e}")

        tasks = propose_tasks(project_description, constraints, model=args.model)

        print("✅ Successfully proposed tasks for the project!")
        print(f"📋 Tasks:\n{tasks}")

        with open(args.project_file, "w") as f:
            project["tasks"] = tasks
            json.dump(project, f)
        print(f"📁 Tasks saved to: {args.project_file}")

    except Exception as e:
        print(f"❌ Tasks proposal failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
