#!/usr/bin/env python3
"""
Script to extract tasks.md markdown file into structured JSON format.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class TasksMarkdownParser:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {
            "project_description": "",
            "task_instruction": "",
            "phases": [],
        }

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse the markdown file and return structured data."""
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Split content into sections
        sections = self._split_into_sections(content)

        # Extract project description and task instruction
        self._extract_header_sections(sections)

        # Extract detailed documentation
        self._extract_phases(sections)

        return self.data

    def _split_into_sections(self, content: str) -> List[str]:
        """Split content by main headers."""
        # Split by # headers but keep the headers
        sections = re.split(r"^(# .+)$", content, flags=re.MULTILINE)
        # Remove empty strings and combine headers with their content
        result = []
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                result.append(sections[i] + sections[i + 1])
            else:
                result.append(sections[i])
        return result

    def _extract_header_sections(self, sections: List[str]) -> None:
        """Extract project description and task instruction."""
        for section in sections:
            if section.startswith("# Project Description"):
                self.data["project_description"] = self._clean_text(
                    section.replace("# Project Description", "").strip()
                )
            elif section.startswith("# Task Instruction"):
                self.data["task_instruction"] = self._clean_text(
                    section.replace("# Task Instruction", "").strip()
                )

    def _extract_phases(self, sections: List[str]) -> None:
        """Extract phases and their modules/tasks."""
        for section in sections:
            if section.startswith("# Detailed Documentation"):
                self._parse_detailed_documentation(section)

    def _parse_detailed_documentation(self, content: str) -> None:
        """Parse the detailed documentation section."""
        # Split by ## Phase headers
        phase_sections = re.split(r"^(## Phase \d+: .+)$", content, flags=re.MULTILINE)

        for i in range(1, len(phase_sections), 2):
            if i + 1 < len(phase_sections):
                phase_header = phase_sections[i]
                phase_content = phase_sections[i + 1]

                phase_data = self._parse_phase(phase_header, phase_content)
                if phase_data:
                    self.data["phases"].append(phase_data)

    def _parse_phase(self, header: str, content: str) -> Optional[Dict[str, Any]]:
        """Parse a single phase."""
        # Extract phase number and title
        phase_match = re.match(r"## Phase (\d+): (.+)", header)
        if not phase_match:
            return None

        phase_num = int(phase_match.group(1))
        phase_title = phase_match.group(2).strip()

        # Extract goal
        goal_match = re.search(r"\*\*Goal:\*\* (.+)", content)
        goal = goal_match.group(1).strip() if goal_match else ""

        phase_data: Dict[str, Any] = {
            "phase_number": phase_num,
            "title": phase_title,
            "goal": goal,
            "modules": [],
        }

        # Parse modules
        module_sections = re.split(r"^(### Module \d+\.\d+: .+)$", content, flags=re.MULTILINE)

        for j in range(1, len(module_sections), 2):
            if j + 1 < len(module_sections):
                module_header = module_sections[j]
                module_content = module_sections[j + 1]

                module_data = self._parse_module(module_header, module_content)
                if module_data:
                    phase_data["modules"].append(module_data)

        return phase_data

    def _parse_module(self, header: str, content: str) -> Optional[Dict[str, Any]]:
        """Parse a single module."""
        # Extract module number and title
        module_match = re.match(r"### Module (\d+\.\d+): (.+)", header)
        if not module_match:
            return None

        module_num = module_match.group(1)
        module_title = module_match.group(2).strip()

        module_data: Dict[str, Any] = {
            "module_number": module_num,
            "title": module_title,
            "tasks": [],
        }

        # Parse tasks
        task_sections = re.split(r"^(#### Task \d+\.\d+\.\d+: .+)$", content, flags=re.MULTILINE)

        for k in range(1, len(task_sections), 2):
            if k + 1 < len(task_sections):
                task_header = task_sections[k]
                task_content = task_sections[k + 1]

                task_data = self._parse_task(task_header, task_content)
                if task_data:
                    module_data["tasks"].append(task_data)

        return module_data

    def _parse_task(self, header: str, content: str) -> Optional[Dict[str, Any]]:
        """Parse a single task."""
        # Extract task number and title
        task_match = re.match(r"#### Task (\d+\.\d+\.\d+): (.+)", header)
        if not task_match:
            return None

        task_num = task_match.group(1)
        task_title = task_match.group(2).strip()

        # Extract description
        desc_match = re.search(r"- \*\*Description:\*\* (.+?)(?=\n- \*\*|$)", content, re.DOTALL)
        description = self._clean_text(desc_match.group(1)) if desc_match else ""

        # Extract dependencies
        deps_match = re.search(r"- \*\*Dependencies:\*\* (.+?)(?=\n- \*\*|$)", content, re.DOTALL)
        dependencies_str = deps_match.group(1).strip() if deps_match else ""
        dependencies = [
            dep.strip()
            for dep in dependencies_str.split(",")
            if dep.strip() and dep.strip().lower() != "none"
        ]

        # Extract difficulty
        diff_match = re.search(r"- \*\*Difficulty:\*\* (\d+)/5", content)
        difficulty = int(diff_match.group(1)) if diff_match else None

        # Extract unit tests
        unit_tests = self._parse_unit_tests(content)

        task_data = {
            "task_number": task_num,
            "title": task_title,
            "description": description,
            "dependencies": dependencies,
            "difficulty": difficulty,
            "unit_tests": unit_tests,
        }

        return task_data

    def _parse_unit_tests(self, content: str) -> Dict[str, List[Dict[str, str]]]:
        """Parse unit tests section."""
        unit_tests: Dict[str, List[Dict[str, str]]] = {"code_tests": [], "visual_tests": []}

        # Find unit tests section
        tests_match = re.search(r"- \*\*Unit Tests:\*\*(.*?)(?=\n####|\Z)", content, re.DOTALL)
        if not tests_match:
            return unit_tests

        tests_content = tests_match.group(1)

        # Parse code tests
        code_tests_match = re.search(
            r"- \*\*Code Tests:\*\*(.*?)(?=\n  - \*\*Visual Tests:\*\*|\Z)",
            tests_content,
            re.DOTALL,
        )
        if code_tests_match:
            code_tests_content = code_tests_match.group(1)
            unit_tests["code_tests"] = self._parse_test_items(code_tests_content)

        # Parse visual tests
        visual_tests_match = re.search(r"- \*\*Visual Tests:\*\*(.*)", tests_content, re.DOTALL)
        if visual_tests_match:
            visual_tests_content = visual_tests_match.group(1)
            unit_tests["visual_tests"] = self._parse_test_items(visual_tests_content)

        return unit_tests

    def _parse_test_items(self, content: str) -> List[Dict[str, str]]:
        """Parse individual test items."""
        tests = []

        # Find test items with pattern: - **TestName:** Description
        test_matches = re.findall(
            r"- \*\*([^:]+):\*\* (.+?)(?=\n    - \*\*|\Z)", content, re.DOTALL
        )

        for test_name, test_description in test_matches:
            tests.append(
                {"name": test_name.strip(), "description": self._clean_text(test_description)}
            )

        return tests

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace and newlines
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def save_to_json(self, output_path: str, indent: int = 2) -> None:
        """Save the parsed data to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=indent, ensure_ascii=False)


def convert_md_to_json(
    md_file_path: str, json_file_path: Optional[str] = None, indent: int = 2
) -> str:
    """
    Convert markdown file to JSON format.

    Args:
        md_file_path (str): Path to the input markdown file
        json_file_path (str, optional): Path for the output JSON file.
                                       If None, auto-generates based on input filename.
        indent (int): JSON indentation level (default: 2)

    Returns:
        str: Path to the generated JSON file

    Raises:
        FileNotFoundError: If input markdown file doesn't exist
        Exception: If parsing or writing fails
    """
    # Check if input file exists
    if not Path(md_file_path).exists():
        raise FileNotFoundError(f"Input file '{md_file_path}' does not exist.")

    # Auto-generate output filename if not provided
    if json_file_path is None:
        md_path = Path(md_file_path)
        json_file_path = str(md_path.parent / f"{md_path.stem}.json")

    # Parse the markdown file
    parser = TasksMarkdownParser()
    parser.parse_file(md_file_path)
    parser.save_to_json(str(json_file_path), indent)

    return str(json_file_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract tasks.md to structured JSON")
    parser.add_argument("input_file", help="Path to the input markdown file")
    parser.add_argument("-o", "--output", default="tasks.json", help="Output JSON file path")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")

    args = parser.parse_args()

    try:
        output_path = convert_md_to_json(args.input_file, args.output, args.indent)
        print(f"Successfully extracted tasks to '{output_path}'")

        # Parse again to get summary
        parser_instance = TasksMarkdownParser()
        data = parser_instance.parse_file(args.input_file)

        # Print summary
        total_tasks = sum(
            len(module["tasks"]) for phase in data["phases"] for module in phase["modules"]
        )
        print(
            f"Summary: {len(data['phases'])} phases, "
            f"{sum(len(phase['modules']) for phase in data['phases'])} modules, "
            f"{total_tasks} tasks"
        )

        return 0
    except Exception as e:
        print(f"Error processing file: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
