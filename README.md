# 🔨 MODEL FORGE
> Evaluate hosted [OpenAI GPT](https://platform.openai.com/docs/models) / Google Vertex AI [PaLM2](https://ai.google.dev/models/palm) / [Gemini](https://ai.google.dev/models/gemini) or local [Ollama models](https://ollama.ai/library) against a task.

Distribute arbitrary tasks as YAML to local or hosted language models. In MODEL FORGE tasks are broken down by: **agents**, optional **postprocessor**, and **evaluators**. Tasks have a top level prompt -- the actual work to do. For example, you could use the following as a task prompt: "Implement a simple example of [`malloc`](https://man.freebsd.org/cgi/man.cgi?query=malloc&sektion=9) in C with the following signature: `void* malloc(size_t size)`". Next, you could include a postprocessor request to a local model to extract only the program's source code from the agent's response. Finally, your evaluator would be instructed to act as an expert in the task ideally with [CoT (Chain of Thought)](https://blog.research.google/2022/05/language-models-perform-reasoning-via.html) based examples examples included.

![MODEL FORGE overview](https://docs.google.com/drawings/d/e/2PACX-1vRRMnmfZVHKacgjdbmthm_I_Cm1pPbgf9Pk1crOPf44V0Uon3A3rSmlvGxHaZc_NUz5VirkEYD4furM/pub?w=2467&h=484)

## Requirements
* macOS / Linux (Ubuntu as a distro was tested)
* Python 3.10+
* Depending on use case:
  * [OpenAI](https://openai.com/blog/openai-api) API key
  * Google Cloud Vertex AI [service account credentails `.json`](https://cloud.google.com/iam/docs/keys-create-delete#creating)
  * [Ollama](https://github.com/jmorganca/ollama) installed


## 🏎️ Quick start
1. Clone the repository
2. Setup a Python environment and install dependencies
3. Execute the entry point script: `python src/main.py`
```sh
git clone https://github.com/Brandon7CC/MODELFORGE
cd MODELFORGE/
python -m venv forge-env
source forge-env/bin/activate
pip install -r requirements.txt
python src/main.py -h
echo "Done! Next, you can try FizzBuzz with Ollama locally!\npython src/main.py task_configs/FizzBuzz.yaml
```

## Supported Providers
* [OpenAI](https://platform.openai.com/docs/models) text completion models. For example,
  * gpt-3.5-turbo
  * gpt-4
  * gpt-4-1106-preview
* Google Vertex AI [PALM2](https://ai.google.dev/models/palm) / [Gemini](https://ai.google.dev/models/gemini) text/code completion models. For example,
  * gemini-pro
  * text-unicorn@001
  * code-bison
* OSS [models via Ollama](https://ollama.ai/library) e.g. LLaMA, Orca2, Vicuna, Mixtral8x7b, Mistral, Phi2, etc


## Use cases
* Evaluate model(s) against a common task
* Produce examples of creative ways to solve a problem
  * Chain models together to enable a simple thought loop

## 👨‍💻 FizzBuzz!
FizzBuzz is a classic "can you code" question. It's simple, but can provide a level of insight into how a developer thinks through a problem. For example, in Python, the use of control flow, lambdas, etc. Here's the problem statement:
> Write a program to display numbers from 1 to n. For multiples of three, print "Fizz" instead of the number, and for the multiples of five, print "Buzz". For numbers which are multiples of both three and five, print "FizzBuzz".

Next, we'll make our task configuration file (this is already done for you in `task_configs/FizzBuzz.yaml`), but we'll walk you through it. To do so we'll **define a top level task** called "FizzBuzz", give it a prompt and the number of times we want he model to solve the problem.
```yaml
tasks:
  - name: FizzBuzz
    # If a run count is not provided then the task will only run until evaluator success.
    run_count: 5
    prompt: |
        Write a program to display numbers from 1 to n. For multiples of three, print "Fizz" 
        instead of the number, and for the multiples of five, print "Buzz". For numbers which 
        are multiples of both three and five, print "FizzBuzz".
        Let's think step by step.
```

Now we'll define our **"agent"** -- the model which will act as an expert to complete our task. Models can be any of the supported hosted / local Ollama models (e.g. Google's Gemini, OpenAI's GPT-4, or Mistral AI's Mixtral8x7b via Ollama).
```yaml
tasks:
  - name: FizzBuzz
    run_count: 5
    prompt: |
        ...
    agent: 
      # We'll generate a custom model for each base model
      base_model: mixtral:8x7b-instruct-v0.1-q4_1
      temperature: 0.98
      system_prompt: | 
        You're an expert Python developer. Follow these requirement **exactly**:
        - The code you produce is at the principal level;
        - You follow modern object oriented programming patterns;
        - You list your requirements and design a simple test before implementing.
        Review the user's request and follow these requirements.
```

**Optionally** we can create a **"postprocessor"**. We'll only want the code completed by the agent to be evaluated so here we're going to have our postprocessor model extract the source code from the agent's response.

```yaml
tasks:
  - name: FizzBuzz
    # If a run count is not provided then the task will only run until evaluator success.
    run_count: 5
    prompt: |
        ...
    agent: 
      # We'll generate a custom model for each base model
      base_model: gpt-4-1106-preview
      temperature: 0.98
      system_prompt: | 
        ...
    postprocessor:
      base_model: mistral
      temperature: 0.1
      system_prompt: |
        You have one job: return the source code provided in the user's message. 
        **ONLY** return the exact source code. Your response is not read by a human.
```

Lastly, you'll want an **"evaluator"** model which will act as an expert in reviewing the output from the agent/postprocessor. The job of the evaluator is to return TRUE / FALSE. Additionally, we can **fail up to 10 times** -- re-query the agent. **Here's were a bit of the magic comes in** -- we'll include a brief summary of the failed attempt -- a critique within the next query to the agent. This enables the agent to iterate on itself in a **much more effective** way. Here we'll want our evaluator to review the implementation of FizzBuzz.

```yaml
tasks:
  - name: FizzBuzz
    # If a run count is not provided then the task will only run until evaluator success.
    run_count: 5
    prompt: |
        ...
    agent: 
      # We'll generate a custom model for each base model
      base_model: codellama
      temperature: 0.98
      system_prompt: | 
        ...
    postprocessor:
      base_model: gemini-pro
      temperature: 0.1
      system_prompt: |
        ...
    # Evaluators have defined system prompts to only return true / false for their domain.
    evaluator:
      base_model: gpt-4-1106-preview
      temperature: 0.1
      system_prompt: |
        Assess if a given sample program correctly implements Fizz Buzz. 
        The program should display numbers from 1 to n. For multiples of three, it should 
        print "Fizz" instead of the number, for the multiples of five, it should print "Buzz", 
        and for numbers which are multiples of both three and five, it should print "FizzBuzz".
        Guidelines for Evaluation
          - Correctness: Verify that the program outputs "Fizz" for multiples of 3, "Buzz" for 
            multiples of 5, and "FizzBuzz" for numbers that are multiples of both 3 and 5. For
            all other numbers, it should output the number itself.
          - Range Handling: Check if the program correctly handles the range from 1 to n, where
            n is the upper limit provided as input.
          - Error Handling: Assess if the program includes basic error handling, such as ensuring
            the input is a positive integer.
```

### Insperation
This work was inspired by Google DeepMind's [FunSearch](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/) approach to finding a novel solution to the [cap set](https://en.wikipedia.org/wiki/Cap_set) problem. At the macro level this was done by developing [CoT (Chain of Thought)](https://blog.research.google/2022/05/language-models-perform-reasoning-via.html) based examples, repeatedly prompting PaLM2 to generate a large amounts of programs, and then evaluating those programs on several levels. 

![Google's FunSearch](https://lh3.googleusercontent.com/mIlL5zg4-gbYvIdCuBB5SmzPzbC1yUghYgIwYR89pEJpgc4f00OhDpd6SRM_MXNi1XSqJJpFe_yeFXHZShLr3syM0SFSxtuqJzdaEgX8fsvCW1SN=w1232-rw)