"""Project Proposal pipeline."""

import argparse
import json
import re
import sys
from pathlib import Path

from swe_play.utils.llm_client import create_llm_client
from swe_play.utils.prompt_retriever import PromptRetriever


def propose_projects(
    model: str = "claude-sonnet-4-20250514",
    num_projects: int = 1,
    output_folder: str | None = None,
) -> list[dict[str, str]]:
    """Propose diverse projects using the LLM.

    Args:
        model: The LLM model to use for project proposal.
        num_projects: The number of projects to propose.
        output_folder: The folder to save the proposed projects.

    Returns:
        A list of dictionaries, each containing:
        - project_description: Description of the project
        - repo_name: Repository name
        - programming_language: Programming language
        - constraints: Library/framework constraints to ensure core implementation

    Raises:
        Exception: If project proposal fails or response format is invalid.
    """
    llm_client = create_llm_client(model=model)
    prompt_retriever = PromptRetriever()

    system_prompt = prompt_retriever.get_prompt("propose-projects-system")
    user_prompt = prompt_retriever.get_prompt("propose-projects-user", num_projects=num_projects)

    print(f"Calling LLM to propose {num_projects} diverse projects...")
    response = llm_client.system_completion(
        system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.7
    )

    # Parse the response to extract all projects
    projects = []

    # Find all project blocks in the response
    project_pattern = (
        r"Project \d+:\s*<proposed_project>(.*?)</proposed_project>\s*"
        r"<repo_name>(.*?)</repo_name>\s*<programming_language>(.*?)</programming_language>\s*"
        r"<constraints>(.*?)</constraints>"
    )
    matches = re.findall(project_pattern, response, re.DOTALL)

    for match in matches:
        project_description = match[0].strip()
        repo_name = match[1].strip()
        programming_language = match[2].strip()
        constraints = match[3].strip()

        projects.append(
            {
                "project_description": project_description,
                "repo_name": repo_name,
                "programming_language": programming_language,
                "constraints": constraints,
            }
        )

    if output_folder is not None:
        if not Path(output_folder).exists():
            Path(output_folder).mkdir(parents=True, exist_ok=True)
        for project in projects:
            with open(Path(output_folder) / f"{project['repo_name']}.json", "w") as f:
                json.dump(project, f)

    return projects


def main() -> None:
    """CLI entry point for proposing projects."""
    parser = argparse.ArgumentParser(
        description="Propose diverse projects for SWE-agent training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m swe_play.propose.propose_projects                              # Default settings
  python -m swe_play.propose.propose_projects --model claude-sonnet-4-20250514
  python -m swe_play.propose.propose_projects --output projects            # Custom folder
        """,
    )

    parser.add_argument(
        "--num-projects",
        type=int,
        default=1,
        help="Number of projects to propose (default: 1)",
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
        default=None,
        help="Output folder to save the proposed projects (default: None)",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting projects proposal pipeline...\n")
        projects = propose_projects(
            model=args.model, num_projects=args.num_projects, output_folder=args.output
        )

        print(f"✅ Successfully proposed {len(projects)} diverse projects!")
        if args.output is not None:
            print(f"📁 Projects saved to: {args.output}")

    except Exception as e:
        print(f"❌ Project proposal failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
