"""Utility for calling OpenHands agent."""

import os
import re
import subprocess
from typing import Any


def call_openhands_raw(
    prompt: str,
    config_file_path: str | None = None,
    directory: str | None = None,
    output_dir: str | None = None,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Call the OpenHands agent with a given prompt and configuration and return the raw
    subprocess.CompletedProcess result.

    Args:
        prompt: The task prompt to send to the OpenHands agent.
        config_file_path: Path to the config file. If None, will use OPENHANDS_CONFIG_PATH env var.
        directory: Working directory for the OpenHands agent. If provided, adds -d flag.
        **kwargs: Additional arguments to pass to subprocess.run().

    Returns:
        The subprocess.CompletedProcess result.

    Raises:
        ValueError: If no config file path is provided and OPENHANDS_CONFIG_PATH env var is not set.
        subprocess.CalledProcessError: If the OpenHands command fails.
    """
    # Get config file path from env var if not provided
    if config_file_path is None:
        config_file_path = os.getenv("OPENHANDS_CONFIG_PATH")
        if config_file_path is None:
            raise ValueError(
                "Config file path is required. Set OPENHANDS_CONFIG_PATH environment variable "
                "or pass config_file_path parameter."
            )

    # Change working directory to the repo of OpenHands
    current_cwd = os.getcwd()
    openhands_dir = os.path.dirname(config_file_path)
    os.chdir(openhands_dir)

    # Cannot pass working space to OpenHands via arguments
    # Hence directly modify the config file to set workspace_base
    with open(config_file_path, "r") as f:
        config_content = f.read()
        # Use regex to find and replace workspace_base regardless of the original value
        config_content = re.sub(
            r'workspace_base\s*=\s*"[^"]*"', f'workspace_base = "{directory}"', config_content
        )

        if output_dir is not None:
            config_content = re.sub(
                r'save_trajectory_path\s*=\s*"[^"]*"',
                f'save_trajectory_path = "{output_dir}/trajectories"',
                config_content,
            )
            config_content = re.sub(
                r'log_completions_folder\s*=\s*"[^"]*"',
                f'log_completions_folder = "{output_dir}/log_completions"',
                config_content,
            )
        else:
            config_content = re.sub(
                r'save_trajectory_path\s*=\s*"[^"]*"',
                'save_trajectory_path = "./trajectories"',
                config_content,
            )
            config_content = re.sub(
                r'log_completions_folder\s*=\s*"[^"]*"',
                'log_completions_folder = "./log_completions"',
                config_content,
            )

    with open(config_file_path, "w") as f:
        f.write(config_content)

    # Build the command
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "openhands.core.main",
        "-t",
        prompt,
        "--config-file",
        config_file_path,
    ]

    # # Add directory flag if provided
    # if directory is not None:
    #     cmd.extend(["-d", directory])

    # Set default kwargs
    default_kwargs: dict[str, bool] = {"text": True, "capture_output": True, "check": True}
    default_kwargs.update(kwargs)

    # Execute the command
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=True, **kwargs)
        return result
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode, e.cmd, output=e.stdout, stderr=e.stderr
        ) from e
    finally:
        # Always restore original working directory
        os.chdir(current_cwd)


def call_openhands(
    prompt: str, config_file_path: str | None = None, directory: str | None = None
) -> str:
    """Call OpenHands agent and return just the stdout output.

    Args:
        prompt: The task prompt to send to the OpenHands agent.
        config_file_path: Path to the config file. If None, will use OPENHANDS_CONFIG_PATH env var.
        directory: Working directory for the OpenHands agent. If provided, adds -d flag.

    Returns:
        The stdout output from the OpenHands command.

    Raises:
        ValueError: If no config file path is provided and OPENHANDS_CONFIG_PATH env var is not set.
        subprocess.CalledProcessError: If the OpenHands command fails.
    """
    print("Repo directory:", directory)
    result = call_openhands_raw(prompt, config_file_path, directory)
    return result.stdout


def call_openhands_rollout(
    prompt: str,
    config_file_path: str | None = None,
    directory: str | None = None,
    output_dir: str | None = None,
) -> str:
    """Call OpenHands agent and return just the stdout output.

    Args:
        prompt: The task prompt to send to the OpenHands agent.
        config_file_path: Path to the config file. If None, will use OPENHANDS_CONFIG_PATH env var.
        directory: Working directory for the OpenHands agent. If provided, adds -d flag.

    Returns:
        The stdout output from the OpenHands command.

    Raises:
        ValueError: If no config file path is provided and OPENHANDS_CONFIG_PATH env var is not set.
        subprocess.CalledProcessError: If the OpenHands command fails.
    """
    print("Repo directory:", directory)
    result = call_openhands_raw(prompt, config_file_path, directory, output_dir)
    return result.stdout
