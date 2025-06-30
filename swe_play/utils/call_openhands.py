"""Utility for calling OpenHands agent."""

import os
import subprocess
from typing import Any


def call_openhands_raw(
    prompt: str, config_file_path: str | None = None, directory: str | None = None, **kwargs: Any
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
    # Hence directly modify the config file
    # Copy config file to and modify workspace_base
    with open(config_file_path, "r") as f:
        config_content = f.read()
        config_content = config_content.replace(
            'workspace_base = "./workspace"', f'workspace_base = "{directory}"'
        )
    temp_config_file_path = os.path.join(openhands_dir, "config_temp.toml")
    with open(temp_config_file_path, "w") as f:
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
        temp_config_file_path,
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
        # Clean up temporary config file
        if os.path.exists(temp_config_file_path):
            os.remove(temp_config_file_path)
        return result
    except subprocess.CalledProcessError as e:
        # Clean up temporary config file
        if os.path.exists(temp_config_file_path):
            os.remove(temp_config_file_path)
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
