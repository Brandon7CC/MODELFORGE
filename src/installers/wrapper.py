"""
File: wrapper.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: This script provides wrapper functions for installing Ollama and gcloud.
"""

import os
from pathlib import Path
import subprocess

import os
from pathlib import Path
import subprocess


def is_read_only():
    # Target directory to check
    target_directory = "/usr/local/bin"

    # Check if target directory is writable
    if not os.access(target_directory, os.W_OK):
        # print(f"Error: '{target_directory}' is not writable.")
        return True
    return False


def execute_command(command):
    result = subprocess.Popen(command,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    stdout, stderr = result.communicate()
    if result.returncode != 0:
        return False
    return True


def install_ollama():
    if is_read_only():
        print("Error: Cannot install Ollama. The file system is read-only.")
        return False

    # Get the directory in which this script is located
    script_dir = Path(__file__).parent.resolve()
    # Construct the path to the setup script
    setup_filepath = script_dir.joinpath("ollama_setup.sh")

    # Check if the setup file exists
    if not setup_filepath.exists():
        print(f"Setup script not found at {setup_filepath}")
        return False

    os.chmod(setup_filepath, 0o755)

    # Try executing the script via a shell command
    command = f"bash {setup_filepath}"
    return execute_command(command)


def install_gcloud():
    if is_read_only():
        # Install using nix
        command = ["nix-env", "-iA", "nixpkgs.google-cloud-sdk"]
        if not execute_command(command):
            return False

        # Initilize gcloud
        # gcloud init
        # gcloud auth application-default login
        print("INIT!!!!!!")
        command = ["gcloud", "init"]
        if not execute_command(command):
            return False
        command = ["gcloud", "auth", "application-default", "login"]
        if not execute_command(command):
            return False

    setup_filepath = "src/installers/gcloud_setup.sh"
    os.chmod(setup_filepath, 0o755)
    os.system(f"./{setup_filepath}")

    # # Save the current directory
    # current_dir = os.getcwd()
    # # Change to the current directory of this file
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # os.chmod("gcloud_setup.sh", 0o755)
    # # Install `gcloud` from the `gcloud_setup.sh` file
    # os.system("./gcloud_setup.sh")
    # # Change back to the original directory
    # os.chdir(current_dir)


if __name__ == "__main__":
    # install_ollama()
    install_gcloud()
