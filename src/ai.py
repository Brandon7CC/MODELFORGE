"""
File: ai.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: This script provides abstractions for interacting with language models:
- Creating models with Ollama for custom system prompts
- Querying models: OpenAI, Google, and Ollama
"""

import subprocess
from langchain.llms import Ollama
import logging
from subprocess import run
from pathlib import Path
import uuid
import os
import datetime
import sys
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.preview.generative_models import GenerativeModel, ChatSession
from openai import OpenAI
import os
import shutil
from installers.wrapper import install_ollama, install_gcloud


def get_gcloud_project_id() -> str:
    result = run(["which", "gcloud"], capture_output=True)
    if result.returncode != 0:
        install_gcloud()
    # `gcloud config get-value project`
    result = run(["gcloud", "config", "get-value", "project"],
                 capture_output=True)
    if result.returncode != 0:
        print("Error getting project ID attempting reinstall")
        install_gcloud()
    return result.stdout.decode("utf-8").strip()


class ModelForge:

    @staticmethod
    def isModelProprietary(model: str):
        return any(name in model
                   for name in ["bison", "unicorn", "gemini", "gpt"])

    @staticmethod
    def isGoogleModel(model_name):
        model_name = str(model_name)
        # If the model is an instance of TextGenerationModel, then it's a Google model
        return isinstance(model_name, TextGenerationModel) or any(
            keyword in model_name
            for keyword in ["bison", "unicorn", "gemini"])

    @staticmethod
    def isOpenAI(model):
        # If the model is an instance of TextGenerationModel, then it's a Google model
        return "gpt" in model

    @staticmethod
    def destroy():
        """
        This method is called when the ModelForge is destroyed. It will delete any models that were created.
        """
        print("🗑️  MODELFORGE: deleting all models created by this run.")
        # We'll want to first list all models and then find the ones we created. They'll start with: `MODELFORGE-`
        result = run(["ollama", "list"], capture_output=True)
        if result.returncode != 0:
            print("Error listing models.")
            return
        # Get the list of models
        models = result.stdout.decode("utf-8").split("\n")
        # Filter out the ones we created
        models = [
            model.split("\t") for model in models
            if model.startswith("MODELFORGE-")
        ]
        # Delete the models
        for model in models:
            model = model[0]
            output = run(["ollama", "rm", model], capture_output=True)
            if output.returncode != 0:
                print(f"Error deleting model: {model}")

        print(
            f"✅ MODELFORGE: deleted the {len(models)} models created by this run."
        )

    @staticmethod
    def model_exists(model: str):
        # Validate the model. Do we have it in out agent's library?
        # To do this use `ollama list` and check the output.
        result = run(["ollama", "list"], capture_output=True)
        if model not in result.stdout.decode("utf-8"):
            return False

        return True

    def __init__(
        self,
        base_model: str,
        temperature: float,
        system_prompt: str,
        directory: Path = Path("/tmp/")
        if sys.platform.startswith("linux") else Path("/private/tmp/models"),
    ):
        """
        Custom models have the following:
        - A base model type supported by Ollama (e.g. vikuna / phi / orca2)
        - A temperature to use for the model (special sauce)
        - A defined System Prompt (special sauce)
        - and optionally a directory to save the model file to
        """

        # Model name will be constructed as:
        # MODELFORGE-<base_model>-<temperature>-<system_prompt_length>-<date_time>
        self.name = f"MODELFORGE-{base_model}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # LLM parameters
        self.base_model = base_model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.proprietary = ModelForge.isModelProprietary(base_model)

        if not self.proprietary:
            # Check to ensure `ollama` is installed. Exit gracefully if not.
            if not shutil.which("ollama") and not install_ollama():
                print(
                    "Local models hosted by Ollama are not available on this platform."
                )
                exit(1)

            # Ollama model file creation
            self.modelfile_path = directory.joinpath(
                f"{self.name}-Modelfile.txt")

            # Check to ensure that the base model exists. Exit gracefully if not.
            result = run(["ollama", "list"], capture_output=True)
            # Check that the model name is in the output
            if result.returncode != 0 or self.base_model not in result.stdout.decode(
                    "utf-8"):
                # Run `ollama pull <base_model>` to pull the model
                result = run(["ollama", "pull", self.base_model],
                             capture_output=True)
                if result.returncode != 0:
                    print(f"Error pulling model: {self.base_model}")

            self._create_modelfile()

    def __str__(self):
        return f"Base Model: {self.base_model}, Temp: {self.temp}, Name: {self.name}"

    def _create_modelfile(self):
        # Ensure the directory exists
        directory = os.path.dirname(self.modelfile_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Create the model file
        with open(self.modelfile_path, "w+") as file:
            file.write(f"FROM {self.base_model}\n\n")
            file.write(f"PARAMETER temperature {self.temperature}\n\n")
            file.write(f'SYSTEM """{self.system_prompt}"""\n\n')

    def create_model(self):
        """
        Creates a new model based on the base model name, with the given name, temperature, and system prompt.
        """
        if self.proprietary:
            return

        command = [
            "ollama", "create", self.name, "-f",
            str(self.modelfile_path)
        ]

        # Create the model
        result = run(command, capture_output=True)

        # Check that the model was created successfully
        if result.returncode != 0:
            print("Error creating model.")
            return
        # print(f"✅ MODELFORGE: created the {self.name} model successfully based on: {self.base_model}. Modelfile saved to {self.modelfile_path}")

    def delete_model(self):
        """
        Deletes the model with the given name.
        """
        if self.proprietary:
            return

        result = run(["ollama", "rm", self.name], capture_output=True)

        # Check that the model was deleted successfully
        if result.returncode != 0:
            print("Error deleting model.")
            return
        # Attempt to delete the model file
        try:
            self.modelfile_path.unlink()
        except FileNotFoundError:
            pass
        # print(f"🗑️  MODELFORGE: {self.name} based on: {self.base_model} deleted successfully.")

    def _query_model(self, prompt: str) -> str:
        model = LLM(self.name)
        print(model.query_llm(prompt))


class LLM:

    def __init__(self, modelForge: ModelForge):
        self.modelForge = modelForge
        self.base_model = modelForge.base_model
        model = modelForge.name
        self.isPropriatary = ModelForge.isModelProprietary(model)
        if not self.isPropriatary:
            self.llm = Ollama(model=model)
        elif ModelForge.isGoogleModel(self.base_model):
            # Check if `gcloud` is installed
            result = run(["which", "gcloud"], capture_output=True)
            if result.returncode != 0:
                install_gcloud()
            region = "us-central1" if "unicorn" in self.base_model else "us-west1"
            vertexai.init(project=get_gcloud_project_id(), location=region)
            if "gemini" in self.base_model:
                self.model = GenerativeModel("gemini-pro")
            else:  # PaLM 2 models: Gekco, Bison, Unicorn
                self.parameters = {
                    "candidate_count": 1,
                    "max_output_tokens": 1024,
                    "temperature": self.modelForge.temperature,
                    "top_k": 22,
                }
                self.model = TextGenerationModel.from_pretrained(
                    self.base_model)
        elif ModelForge.isOpenAI(self.base_model):
            api_key_path = "credentials/openai.key"
            if not os.path.exists(api_key_path):
                api_key_path = "../credentials/openai.key"
            if not os.path.exists(api_key_path):
                api_key = input("Please enter your OpenAI API key: ")
                os.environ["OPENAI_API_KEY"] = api_key
                os.makedirs(os.path.dirname(api_key_path), exist_ok=True)
                with open(api_key_path, "w") as file:
                    file.write(api_key)
            else:
                with open(api_key_path, "r") as file:
                    self.api_key = file.read()
                os.environ["OPENAI_API_KEY"] = self.api_key
            self.model = OpenAI()
        self.retry_limit = 3
        self.logger = logging.getLogger(__name__)
        # self.base_model = model

    def query_llm(self, prompt: str) -> str:
        if not prompt:
            return "Invalid prompt"

        retries = 0
        while retries < self.retry_limit:
            if not self.isPropriatary:
                try:
                    return self.llm(prompt)
                except Exception as e:  # Replace with the specific exception you expect
                    self.logger.error(f"Error querying LLM: {e}")
                    retries += 1
            elif ModelForge.isGoogleModel(self.base_model):
                google_model_prompt = f"""
                        [SYSTEM]
                        {self.modelForge.system_prompt}
                        [/SYSTEM]
                        [PROMPT]
                        {prompt}
                        [/PROMPT]
                        """
                if "gemini" in self.base_model:
                    try:
                        chat = self.model.start_chat()

                        def get_chat_response(chat: ChatSession,
                                              prompt: str) -> str:
                            response = chat.send_message(prompt)
                            return response.text

                        prompt = google_model_prompt
                        completion = get_chat_response(chat, prompt)
                        # print(f"Response from ✨ Gemini: \n{completion}")
                        retries = 0
                        return completion
                    except vertexai.generative_models._generative_models.ResponseBlockedError as e:  # Replace with the specific exception you expect
                        retries += 1
                        if retries >= self.retry_limit:
                            return "Error querying LLM after retries"
                    except Exception as e:
                        # Check if `gcloud` is installed
                        result = run(["which", "gcloud"], capture_output=True)
                        if result.returncode != 0:
                            install_gcloud()
                else:
                    retries = 0
                    while retries < self.retry_limit:
                        try:
                            response = self.model.predict(
                                google_model_prompt,
                                **self.parameters,
                            )
                            # print(f"Response 🌴 PaLM 2's {self.base_model}:\n {response.text}")
                            retries = 0
                            return response.text
                        except vertexai.generative_models._generative_models.ResponseBlockedError as e:  # Replace with the specific exception you expect
                            retries += 1
                            if retries >= self.retry_limit:
                                return "Error querying LLM after retries"
            elif ModelForge.isOpenAI(self.base_model):
                response = self.model.chat.completions.create(
                    model=self.base_model,
                    messages=[{
                        "role": "system",
                        "content": self.modelForge.system_prompt
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=self.modelForge.temperature,
                    max_tokens=2048,
                    top_p=0.5,
                    frequency_penalty=0.01,
                    presence_penalty=0.01)
                completion = response.choices[0].message.content
                # print(f"Response from 🔥 {self.base_model}:\n {completion}")
                return completion

        return "Error querying LLM after retries"

    def batch_query_llm(self, prompts: list) -> list:
        if not isinstance(prompts, list) or not all(
                isinstance(p, str) for p in prompts):
            return ["Invalid batch prompts"]

        return [self.query_llm(prompt) for prompt in prompts]


if __name__ == "__main__":
    llm = LLM(model="c-agent-dev-phi")
    prompt = "A program representing a buffer overflow bug."
    print(llm.batch_query_llm([prompt] * 1))