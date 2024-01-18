"""
File: ai.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: This script provides abstractions for interacting with language models:
- Creating models with Ollama for custom system prompts
- Querying models: OpenAI, Google, and Ollama
"""

from langchain.llms import Ollama
import logging
from subprocess import run
from pathlib import Path
import os
import datetime
import sys
import vertexai
from vertexai.language_models import TextGenerationModel, CodeGenerationModel
from vertexai.preview.generative_models import GenerativeModel, ChatSession
from openai import OpenAI
import shutil
from installers.wrapper import install_ollama, install_gcloud
from google.oauth2 import service_account
import json
from abc import ABC, abstractmethod


class ModelForge:
    @staticmethod
    def isGoogleModel(model_name):
        model_name = str(model_name)
        # If the model is an instance of TextGenerationModel, then it's a Google model
        return isinstance(model_name, TextGenerationModel) or any(
            keyword in model_name
            for keyword in ["gecko", "otter", "bison", "unicorn", "gemini"]
        )

    @staticmethod
    def isOpenAI(model):
        # If the model is an instance of TextGenerationModel, then it's a Google model
        return "gpt" in model

    @staticmethod
    def isModelProprietary(model: str):
        return ModelForge.isGoogleModel(model) or ModelForge.isOpenAI(model)

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
            model.split("\t") for model in models if model.startswith("MODELFORGE-")
        ]
        # Delete the models
        for model in models:
            model = model[0]
            output = run(["ollama", "rm", model], capture_output=True)
            if output.returncode != 0:
                print(f"Error deleting model: {model}")

        print(f"✅ MODELFORGE: deleted the {len(models)} models created by this run.")

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
        if sys.platform.startswith("linux")
        else Path("/private/tmp/models"),
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
            self.modelfile_path = directory.joinpath(f"{self.name}-Modelfile.txt")

            # Check to ensure that the base model exists. Exit gracefully if not.
            result = run(["ollama", "list"], capture_output=True)
            # Check that the model name is in the output
            if result.returncode != 0 or self.base_model not in result.stdout.decode(
                "utf-8"
            ):
                # Run `ollama pull <base_model>` to pull the model
                result = run(["ollama", "pull", self.base_model], capture_output=True)
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

        command = ["ollama", "create", self.name, "-f", str(self.modelfile_path)]

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
            print("Error deleting model file.")
        # print(f"🗑️  MODELFORGE: {self.name} based on: {self.base_model} deleted successfully.")


# Base class for all models
class BaseModel(ABC):
    def __init__(self, modelForge):
        self.modelForge = modelForge
        self.base_model = modelForge.base_model

    @abstractmethod
    def query(self, prompt):
        pass


class OllamaModel(BaseModel):
    def __init__(self, modelForge):
        super().__init__(modelForge)
        self.llm = Ollama(model=modelForge.name)

    def query(self, prompt):
        return self.llm(prompt)


class LLM:
    def __init__(self, modelForge: ModelForge):
        self.modelForge = modelForge
        self.logger = logging.getLogger(__name__)
        self.retry_limit = 3
        self.model = self._initialize_model(modelForge)

    def _initialize_model(self, modelForge):
        if ModelForge.isModelProprietary(modelForge.name):
            if ModelForge.isGoogleModel(modelForge.base_model):
                return GoogleModel(modelForge)
            elif ModelForge.isOpenAI(modelForge.base_model):
                return OpenAIModel(modelForge)
        else:
            return OllamaModel(modelForge)

    def query_llm(self, prompt: str) -> str:
        if not prompt:
            return "Invalid prompt"
        print(
            f"\n🎆 **Querying the `{self.modelForge.base_model}` model... please hold...**"
        )

        for _ in range(self.retry_limit):
            try:
                return self.model.query(prompt)
            except Exception as e:
                self.logger.error(f"Error querying LLM: {e}")

        return "Error querying LLM after retries"

    def batch_query_llm(self, prompts: list) -> list:
        if not isinstance(prompts, list) or not all(
            isinstance(p, str) for p in prompts
        ):
            return ["Invalid batch prompts"]

        return [self.query_llm(prompt) for prompt in prompts]


class OpenAIModel(BaseModel):
    def __init__(self, modelForge: ModelForge):
        super().__init__(modelForge)
        self._initialize_openai_model(modelForge)

    def _initialize_openai_model(self, modelForge):
        if not os.environ.get("OPENAI_API_KEY"):
            api_key = input("Please enter your OpenAI API key: ")
            os.environ["OPENAI_API_KEY"] = api_key

        self.model = OpenAI()

    def query(self, prompt):
        response = self.model.chat.completions.create(
            model=self.base_model,
            messages=[
                {"role": "system", "content": self.modelForge.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.modelForge.temperature,
            max_tokens=2048,
            top_p=0.5,
            frequency_penalty=0.01,
            presence_penalty=0.01,
        )
        completion = response.choices[0].message.content
        return completion


class GoogleModel(BaseModel):
    def __init__(self, modelForge: ModelForge):
        super().__init__(modelForge)
        self._initialize_google_model(modelForge)

    def _initialize_google_model(self, modelForge):
        # Set environment and credentials for Google Cloud
        self._set_google_credentials()
        region = "us-west1" if "gemini" in modelForge.base_model else "us-central1"
        credentials = service_account.Credentials.from_service_account_file(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        vertexai.init(
            project=self._get_gcloud_project_id(),
            location=region,
            credentials=credentials,
        )
        # Initialize model
        if "gemini" in modelForge.base_model:
            self.model = GenerativeModel("gemini-pro")
        else:
            self.parameters = self._get_model_parameters(modelForge)
            self.model = self._get_google_text_model(modelForge)

    def _set_google_credentials(self):
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            key_path = input(
                "Please enter your GCP service account credentials (JSON) path: "
            )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    def _get_gcloud_project_id(self):
        # Get the client secrets JSON file path from the environment variable
        client_secrets_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        # Read the JSON file if it exists
        if client_secrets_path:
            with open(client_secrets_path, "r") as f:
                client_secrets = f.read()
                # Get the gcloud project ID from the JSON file `project_id` key
                project_id = json.loads(client_secrets)["project_id"]
                return project_id
        else:
            print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")

    def _get_model_parameters(self, modelForge):
        parameters = {
            "candidate_count": 1,
            "max_output_tokens": 1024,
            "temperature": modelForge.temperature,
            "top_k": 22,
        }
        return parameters

    def _get_google_text_model(self, modelForge):
        if "code" in modelForge.base_model:
            return CodeGenerationModel.from_pretrained(modelForge.base_model)
        else:
            return TextGenerationModel.from_pretrained(modelForge.base_model)

    def _get_chat_response(self, chat: ChatSession, prompt: str) -> str:
        response = chat.send_message(prompt)
        return response.text

    def query(self, prompt):
        google_model_prompt = f"""
                [SYSTEM]
                {self.modelForge.system_prompt}
                [/SYSTEM]
                [PROMPT]
                {prompt}
                [/PROMPT]
                """
        if "gemini" in self.base_model:
            chat = self.model.start_chat()
            completion = self._get_chat_response(chat, google_model_prompt)
            # print(f"Response from ✨ Gemini: \n{completion}")
            return completion
        else:  # This would be a PaLM2 model
            # Pop the `top_k` parameter if we're talking to a 🦬 `code-bison`
            if "code-bison" in self.base_model:
                self.parameters.pop(
                    "top_k"
                )  # Remove the `top_k` parameter from the parameters
            response = self.model.predict(
                google_model_prompt,
                **self.parameters,
            )
            # print(
            #     f"Response 🌴 PaLM 2's {self.base_model}:\n {response.text}"
            # )
            return response.text
