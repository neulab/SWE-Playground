import json
import os
import re
from pathlib import Path


def convert_data(runtime_dir: str, save_dir: str, task_number: str) -> None:
    """
    Convert the data in the runtime directory to a JSON file.
    """
    completion_folder = Path(save_dir) / "log_completions"

    max_num = -1.0
    target_file = None
    pattern = re.compile(r"default-(\d+\.\d+)\.json")

    # Find the last completion file which contains the full response
    for fname in os.listdir(completion_folder):
        match = pattern.fullmatch(fname)
        if match:
            num = float(match.group(1))
            if num > max_num:
                max_num = num
                target_file = fname

    if target_file is None:
        raise FileNotFoundError("No matching file found in the folder.")

    target_path = completion_folder / target_file

    with open(target_path, "r") as f:
        data = json.load(f)

    formatted_messages = []
    for item in data["messages"]:
        item = {"content": item["content"][0]["text"], "role": item["role"]}
        formatted_messages.append(item)
    response = data["response"]["choices"][0]["message"]
    item = {"content": response["content"], "role": response["role"]}
    formatted_messages.append(item)
    del formatted_messages[2]

    # Save the formatted messages
    save_path = Path(runtime_dir) / "converted_data" / f"{task_number}.json"
    with open(save_path, "w") as f:
        wdata = {"messages": formatted_messages}
        json.dump(wdata, f, indent=4)
    print(f"Trajectories successfully converted and saved to {save_path}.")
