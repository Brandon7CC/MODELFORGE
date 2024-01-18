"""
File: evaluator.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Models the evaluators described in the YAML configuration.
             Evaluators **MUST** return TRUE or FALSE. This is how we
             handle the evaluation of the agent's output.
"""


class Evaluator:
    def __init__(self, base_model, temperature, system_prompt):
        self.base_model = base_model
        self.temperature = temperature
        self.system_prompt = system_prompt


if __name__ == "__main__":
    evaluator_config = {
        "model": "phi",
        "temperature": 0.1,
        "system_prompt": "language: c",
    }
    evaluator = Evaluator(**evaluator_config)
    print(evaluator.base_model)
