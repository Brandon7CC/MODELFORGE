# 🔨 MODEL FORGE
> Evaluate hosted [OpenAI GPT](https://platform.openai.com/docs/models) / Google Vertex AI [PaLM2](https://ai.google.dev/models/palm)/[Gemini](https://ai.google.dev/models/gemini) or local [Ollama](https://github.com/jmorganca/ollama) models against a task.

Distribute arbitrary tasks as YAML to local or hosted language models. In MODEL FORGE tasks are broken down by: **agents**, optional **postprocessor**, and **evaluators**. Tasks have a top level prompt -- the actual work to do. For example, you could use the following as a task prompt: "Implement a simple example of [`malloc`](https://man.freebsd.org/cgi/man.cgi?query=malloc&sektion=9) in C with the following signature: `void* malloc(size_t size)`". Next, you could include a postprocessor request to a local model to extract only the program's source code from the agent's response. Finally, your evaluator would be instructed to act as an expert in the task ideally with [CoT (Chain of Thought)](https://blog.research.google/2022/05/language-models-perform-reasoning-via.html) based examples examples included.

![MODEL FORGE overview](https://docs.google.com/drawings/d/e/2PACX-1vRRMnmfZVHKacgjdbmthm_I_Cm1pPbgf9Pk1crOPf44V0Uon3A3rSmlvGxHaZc_NUz5VirkEYD4furM/pub?w=2467&h=484)

## Requirements
* macOS / Linux (Ubuntu as a distro was tested)
* Python 3.10+
* Depending on use case:
  * OpenAI API key
  * Vertex AI service account credentails `.json`
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
```

## Supported Providers
* OpenAI models
* Google Vertex AI PALM2 / Gemini models
* OSS models via Ollama e.g. LLaMA, Orca2, Vicuna, Mixtral8x7b, Mistral, Phi2, etc

## Task
Tasks are defined in YAML form and can be broken down into three promary components: 
1. **Agents**: The model and system prompt chosen will do the actual implementation of your take.


For each of these roles you'll find some models work *much* better than others. Additionally, if using OSS models via Ollama do your best to find an "instruct" model (one fine tuned for instruction following).

### Agents
> You'll want to use the best "instruct" expert model you have access to as the agent. 

Agents do the actual heavy lifiting of the task's implemtation. This is done by defining a system prompt. For example, you may want to assess how well models from Google vs. OpenAI, vs. OSS compare. 

### Postprocessors
> From testing you'd ideally want to use a model similar in instruction following capability to GPT-3.5

Postprocessors are optional and take the answer returned by the the agent and manipulate it in some way according to a system prompt. An example of a good postprocessor might be to extract the code from a message or turn it into JSON form.

### Evaluators
> Here you'll want to use the best "instruct" expert model you have access to to evaluate the task with.

Evaluators are another crutial part of the MODEL FORGE task chain. Evaluators, like agents and postprocessors have a defined system prompt that allow them to perform an evaluation on the answer returned by the postprocessor (if one was defined) or the agent (otherwise). As an example: 

> "Act as an expert C software engineer working on kernel components. You're skilled in secure development and follow best practices. Has the user correctly 

Additionally, evaluators 



## Use cases
* Evaluate model(s) against a common task
* Produce examples of creative ways to solve a problem
  * Chain models together to enable a simple thought loop

## Example
Check out the wiki! 

### Insperation
This work was inspired by Google DeepMind's [FunSearch](https://deepmind.google/discover/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/) approach to finding a novel solution to the [cap set](https://en.wikipedia.org/wiki/Cap_set) problem. At the macro level this was done by developing [CoT (Chain of Thought)](https://blog.research.google/2022/05/language-models-perform-reasoning-via.html) based examples, repeatedly prompting PaLM2 to generate a large amounts of programs, and then evaluating those programs on several levels. 

![Google's FunSearch](https://lh3.googleusercontent.com/mIlL5zg4-gbYvIdCuBB5SmzPzbC1yUghYgIwYR89pEJpgc4f00OhDpd6SRM_MXNi1XSqJJpFe_yeFXHZShLr3syM0SFSxtuqJzdaEgX8fsvCW1SN=w1232-rw)