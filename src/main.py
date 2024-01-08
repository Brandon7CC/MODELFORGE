"""
File: main.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Entry point for MODEL FORGE.
"""

import os
import sys
import yaml
import time
import signal
import argparse
from datetime import datetime
from pipeline.tasks import Tasks
from renderers import custom_markdown
from modelforge import ModelForge

MAX_FAIL_LIMIT = 10


def signal_handler(sig, frame):
    print("Exiting and destroying resources...")
    ModelForge.destroy()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def get_results_filename(results_file_path=None):
    if results_file_path is None:
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.expanduser(
            f"~/modelforge/modelforge_result_{current_datetime}.yaml")
    return results_file_path


def ensure_directory_exists(filepath):
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_to_file(tasks, filename):
    with open(filename, "w") as file:
        yaml.dump([task.to_dict() for task in tasks], file)


def execute_task_iteration(task, iteration):
    print(
        f"Executing iteration {iteration}/{task.run_count} ==> {iteration/task.run_count*100}%"
    )
    invalid_responses = 0
    while True:
        validated = task.execute_and_validate()
        if validated:
            return task.positive_results[-1]
        invalid_responses += 1
        if invalid_responses >= MAX_FAIL_LIMIT:
            print(
                "!!!! 🚨 WARNING -- Reached maximum invalid responses. Moving to the next task. !!!!"
            )
            break
        if len(task.negative_results) > 0:
            print(
                f"❌ Not validated. Trying again... Here's what was completed\n---\n{task.negative_results[-1]}\n---\n"
            )
        else:
            print(
                f"❌ Not validated. Trying again... \n⚠️ WARNING: The LLM didn't return a valid reponse... try a different model or system prompt...---\n"
            )


def route_tasks(tasks, results_file_path=None):
    results_file = get_results_filename(results_file_path)
    ensure_directory_exists(results_file)

    for task in tasks:
        start_time = time.time()
        print(
            f"\n{task.name} with the {task.agent.base_model} model\nPROMPT: \n```\n{task.prompt}```"
        )
        for iteration in range(1, task.run_count + 1):
            iteration_start_time = time.time()
            positive_result = execute_task_iteration(task, iteration)
            print(
                f"✅ ===> {round(time.time() - iteration_start_time, 4)}s\n{positive_result}\n<===\n"
            )
            save_to_file(tasks, results_file)

        average_time = (time.time() - start_time) / task.run_count
        print(f"\t⏰ Average time per iteration: {round(average_time, 4)}s")

    print("🤖 Done with all tasking!")
    for task in tasks:
        custom_markdown.render_code_list_as_markdown(task.positive_results)


def main():
    parser = argparse.ArgumentParser(
        description="Process LM tasking YAML file.")
    parser.add_argument("config_file",
                        type=str,
                        help="Path to the researcher_config.yaml file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=
        f"research_results_{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml",
        help="File name to save the results to")

    args = parser.parse_args()

    tasks = Tasks(args.config_file).tasks
    route_tasks(tasks, results_file_path=args.output)


if __name__ == "__main__":
    main()
