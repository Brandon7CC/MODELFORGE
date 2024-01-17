"""
File: tasks.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Creates tasks from the provided configuration file.
"""

from modelforge import LLM, ModelForge
from pipeline.evaluator import Evaluator
from pipeline.agent import Agent
from pipeline.postprocessor import Postprocessor
import yaml
import json


class Task:

    def __init__(self, name, run_count, prompt, agent_config,
                 postprocessor_config, evaluator_config):
        """
        Tasks will have a:
        - name
        - run_count
        - prompt
        - agent
        - (optional) postprocesor
        - evaluator
        """
        self.name = name
        self.prompt = prompt
        self.run_count = run_count

        # LLM agent to task
        self.agent = Agent(**agent_config)
        # The LLM evaluator to validate results produced by the agent
        self.evaluator = Evaluator(**evaluator_config)

        # Postprocessors are optional -- preparing agent output to be evaluated
        if postprocessor_config:
            self.postprocessor = Postprocessor(**postprocessor_config)
        else:
            self.postprocessor = None

        # Store the results of the evaulaton
        self.positive_results = []
        self.negative_results = []

    def to_dict(self):
        """
        Returns the dictionary representation of the tasks which have or will be completed
        """
        # self.positive_results = [
        #     return_text_as_markdown(result) for result in self.positive_results
        # ]
        # self.negative_results = [
        #     return_text_as_markdown(result) for result in self.negative_results
        # ]
        return {
            "task_name":
            self.name,
            "task_prompt":
            f"{self.prompt}",
            "agent_config":
            f"{self.agent.base_model} w/{self.agent.temperature} * {self.run_count}",
            "post_processor_config":
            f"{self.postprocessor.base_model} w/{self.postprocessor.temperature}"
            if self.postprocessor else "NONE",
            "evaluator_config":
            f"{self.evaluator.base_model} w/{self.evaluator.temperature}",
            "positive_results":
            self.positive_results,
            "negative_results":
            self.negative_results
        }

    def execute_and_validate(self, critique=None, past_solution=None):
        # We're now going to want to create a new model off of the base_model specified
        agent_forge = ModelForge(base_model=self.agent.base_model,
                                 temperature=self.agent.temperature,
                                 system_prompt=self.agent.system_prompt)
        agent_forge.create_model()
        # print(f"Created model: {agent_forge.name} based on {agent_forge.base_model}")
        agent_llm = LLM(agent_forge)
        template = f"{self.prompt}"
        if critique is not None:
            template = f"""You've previously failed this task. Here was your past solution:
            {"NOT PROVIDED" if past_solution is None else past_solution.strip()}
            ---
            Here's some help / background context:
            {critique}
            ---
            Here's the task again. Let's think step by step.
            {self.prompt}
            """.strip()
            # print(f"\n\n{template}\n\n")

        completion_to_process = agent_llm.query_llm(template)
        if completion_to_process is not None:
            completion_to_process = completion_to_process.strip()
        agent_forge.delete_model()
        # print(f"Deleted {agent_forge.name}")

        if self.postprocessor:
            # Postprocessing
            postprocessor_forge = ModelForge(
                base_model=self.postprocessor.base_model,
                temperature=self.postprocessor.temperature,
                system_prompt=self.postprocessor.system_prompt)
            postprocessor_forge.create_model()
            # print(f"Created model: {postprocessor_forge.name} based on {postprocessor_forge.base_model}")
            postprocessor_llm = LLM(postprocessor_forge)
            completion_for_eval = postprocessor_llm.query_llm(
                f"{completion_to_process}")
            if completion_for_eval is not None:
                completion_for_eval = completion_for_eval.strip()
            postprocessor_forge.delete_model()
        else:
            completion_for_eval = completion_to_process

        # Evaluate the completion_for_eval
        evaluator_forge = ModelForge(
            base_model=self.evaluator.base_model,
            temperature=self.evaluator.temperature,
            system_prompt=self.evaluator.system_prompt)
        evaluator_forge.create_model()
        evaluator_llm = LLM(evaluator_forge)
        json_template = """
        {
          "eval_result": false,
          "critique": "Your detailed notes go here"
        }
        """.strip()

        prompt_template = f"""Instructions: 
        - Respond only in JSON.
        - Use the `eval_result` tag to insert your TRUE/FALSE evaluation.
        - If your evaluation is FALSE, use the `critique` tag to add notes. 
        Here's your template:
        {json_template}
        --
        Here's the answer to evaluate according to your system prompt:
        {completion_for_eval}
        """.strip()

        eval_result = evaluator_llm.query_llm(prompt_template)
        if eval_result is not None:
            eval_result = eval_result.strip()
        evaluator_forge.delete_model()
        # Remove markdown formatting from the JSON string if it exists
        if "```json" in eval_result:
            eval_result = eval_result.replace("```json", "")
            eval_result = eval_result.replace("```", "")

        if eval_result is not None:
            # Serialize the eval_result into a dictionary (if it's valid JSON)
            # print(eval_result)
            try:
                response_data = json.loads(eval_result)
                validated = response_data.get("eval_result", False)

                # validated: bool = eval_result.split('\n')[0].lower() == "true"
                if validated:
                    self.positive_results.append(completion_for_eval)
                else:
                    self.negative_results.append(completion_for_eval)
                return response_data

            except json.JSONDecodeError:
                return {"eval_result": False}

        else:
            print("Error from the evaluator! No result returned...")


# A wrapper for a list of tasks to be completed.
# `Tasks` has a property `tasks` which is the list of tasks tracked for execution
class Tasks:

    def __init__(self, config_path):
        # Maintain a list of tasks to complete
        self.tasks = []
        # Load the AI research configuration from the YAML at the defined `config_path`
        self._load_config(config_path)

    def _load_config(self, config_path):
        """
        Process the AI researcher configuration file by populating the tasks list
        """

        # Open the YAML config file
        with open(config_path, 'r') as file:
            # Load the YAML into a dict
            config = yaml.safe_load(file)
            # Process each task in the config by making Task objects
            for task_config in config.get('tasks', []):
                self.tasks.append(
                    Task(name=task_config['name'],
                         run_count=task_config['run_count'],
                         prompt=task_config['prompt'],
                         agent_config=task_config['agent'],
                         postprocessor_config=task_config.get('postprocessor'),
                         evaluator_config=task_config['evaluator']))
