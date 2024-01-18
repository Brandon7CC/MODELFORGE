"""
File: postprocessor.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Models the optional postprocessors described in the YAML configuration.
             Postprocessors are optional and may enrich or otherwise extract info
             from the agent's output before sending it off for evaluation.
"""


class Postprocessor:
    def __init__(self, base_model, temperature, system_prompt):
        self.base_model = base_model
        self.temperature = temperature
        self.system_prompt = system_prompt


if __name__ == "__main__":
    postprocessor_config = {
        "model": "orca2",
        "temperature": 0.1,
        "system_prompt": "You have one job: return the source code provided in the user's message.\n **ONLY** return the exact source code. Your response is not read by a human.",
    }
    postprocessor = Postprocessor(**postprocessor_config)
    print(postprocessor.base_model)
