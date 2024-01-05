"""
File: main.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Entry point for MODEL FORGE.
"""

import sys
from pipeline.tasks import Tasks
from renderers import custom_markdown
import time
import yaml
from os.path import expanduser
import datetime
import signal
import sys
import signal
from ai import ModelForge
import os

MAX_FAIL_LIMIT = 10


def signal_handler(sig, frame):
    print("Exiting and destroying resources...")
    ModelForge.destroy()
    sys.exit(0)


def save_to_file(tasks, filename):
    with open(filename, "w") as file:
        yaml.dump([task.to_dict() for task in tasks],
                  file)  # Ensure tasks are serializable


def route_tasks(tasks, results_file_path=None):
    if results_file_path is None:
        current_datetime = datetime.datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S")
        results_file = expanduser(
            f"~/modelforge/modelforge_result_{current_datetime}.yaml")
    else:
        results_file = results_file_path

    results_dir = os.path.dirname(results_file)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    for task in tasks:
        start_time = time.time()
        print(
            f"\n{task.name} with the {task.agent.base_model} model\nPROMPT: \n```\n{task.prompt}```"
        )

        for iteration in range(1, task.run_count + 1):
            iteration_start_time = time.time()
            print(
                f"Executing iteration {iteration}/{task.run_count} ==> {iteration/task.run_count*100}%"
            )
            validated = False
            invalid_responses = 0

            while not validated:
                signal.signal(signal.SIGINT, signal_handler)
                validated = task.execute_and_validate()
                if not validated:
                    invalid_responses += 1
                    print(
                        f"❌ Not validated. Trying again... Here's what was completed\n---\n{task.negative_results[-1]}\n---\n"
                    )
                    success_rate = round(
                        len(task.positive_results) /
                        (len(task.positive_results) +
                         len(task.negative_results)) * 100, 2)
                    print(f"\tSuccess rate: {success_rate}%")
                    if invalid_responses >= MAX_FAIL_LIMIT:
                        print(
                            "!!!! 🚨 WARNING -- Reached maximum invalid responses. Moving to the next task. !!!!"
                        )
                        break

            end_time = time.time()
            print(
                f"✅ ===> {round(end_time - iteration_start_time, 4)}s\n{task.positive_results[-1]}\n<===\n"
            )
            # Save after each iteration
            save_to_file(tasks, results_file)
            average_time = (end_time - start_time) / task.run_count
        print(f"\t⏰ Average time per iteration: {round(average_time, 4)}s")

    print("🤖 Done with all tasking!")
    for task in tasks:
        custom_markdown.render_code_list_as_markdown(task.positive_results)


def main():
    """
    1. Validate command line arguments
        - Path to AI researcher configuration YAML file
    2. Parse the comamnd line arguments
    3. Parse the tasks out of the config file
    4. Route the tasks to be
        - Executed
        - Processed
        - Validated
    5. Results will be outputted to STDOUT as well as `research_results_<DATE-Time>.yaml`
    """
    if len(sys.argv) < 2:
        print(
            "Please provide the path to the researcher_config.yaml file as a command line argument."
        )
        return

    config_file = sys.argv[1]
    tasks = Tasks(config_file).tasks
    # Grab the location to save the results file if provided
    if len(sys.argv) == 3:
        results_file_path = sys.argv[2]
        route_tasks(tasks, results_file_path=results_file_path)
    else:
        route_tasks(tasks)


if __name__ == "__main__":
    main()
