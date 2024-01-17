## MODEL FORGE
> Evaluate hosted [OpenAI GPT](https://platform.openai.com/docs/models) / Google Vertex AI [PaLM2](https://ai.google.dev/models/palm)/[Gemini](https://ai.google.dev/models/gemini) or local [Ollama](https://github.com/jmorganca/ollama) models against a task

Distribute arbitrary tasks to local or hosted language models. In MODEL FORGE tasks are broken down by: **agents**, (optional) **postprocessor**, and **evaluators**. Tasks have a top level prompt -- the actual work to do. For example: "Implement a simple example of [`malloc`](https://man.freebsd.org/cgi/man.cgi?query=malloc&sektion=9) in C with the following signature: `void* malloc(size_t size)`".

Agents do the actual heavy lifiting of the task's implemtation and you can define your own system prompt. For example, you may want to assess how well models from Google vs. OpenAI, vs. OSS compare. Currently we support:
* OpenAI GPT models
* Google PALM2 / Gemini models via Vertex AI
* OSS models via Ollama e.g. LLaMA, Orca2, Vicuna, Mixtral8x7b, Mistral, Phi2, etc


Postprocessors are optional and take the answer returned by the the agent and manipulate it in some way according to a system prompt. An example of a good postprocessor might be to extract the code from a message or turn it into JSON form.

Evaluators are 

## Use cases
* Evaluate model(s) against a common task
* Produce examples of creative ways to solve a problem
  * Chain models together to enable a simple thought loop

## Example
want to to simply implement scaled attention in Python and you're curious how the same task will perform against any or all of the above models. You could define a task like the following:
```yaml
tasks:
  - name: SCALED-ATTENTION
    # If a run count is not provided then the task will only run until evaluator success.
    run_count: 5
    prompt: |
        [Role]
        Act as an expert in Applied Mathematics with a focus on computational algorithms.
        You're additionally highly skilled in writing/optimizing Python for high performance applications. 
        [Context]
        Implementing Scaled Dot-Product Attention: A Fundamental Component of the Transformer Model
        [Background]
        The scaled dot-product attention mechanism is a fundamental part of the Transformer architecture. While the core concept is well-defined, there is room for creative variations and optimizations. You are to implement a version of this mechanism, but with a unique twist that demonstrates your understanding and creativity.
        [Pseudo_Code]
        ```py
        import numpy as np

        def softmax(x):
            e_x = np.exp(x - np.max(x))
            return e_x / e_x.sum(axis=0)

        def scaled_dot_product_attention(Q, K, V, scale_factor):
            dot_product = np.dot(Q, K.T)
            scaled_dot_product = dot_product / np.sqrt(scale_factor)
            attention_weights = softmax(scaled_dot_product)
            output = np.dot(attention_weights, V)
            return output

        # Test the function
        Q = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        K = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        V = np.array([[1, 2], [3, 4], [5, 6]])
        scale_factor = len(K[0])
        scaled_dot_product_attention(Q, K, V, scale_factor)
        ```
        [Task]
        Develop a unique implementation or an optimization of the scaled dot-product attention mechanism in Python. Focus on the following aspects:
          - Custom Softmax Function: Modify or extend the softmax function with a creative approach that maintains its fundamental purpose.
          - Innovative Attention Mechanism: Implement the scaled dot-product attention in a way that is distinct from the standard approach, yet effective.
          - Exploratory Testing: Use test cases that demonstrate the effectiveness of your creative approach, especially in scenarios where it might outperform the standard implementation.
        Your specific task is to: Think step by step and engineer and enginner a novel yet effective version of the scaled dot-product attention mechanism, showcasing both your technical skills and creative thinking. Deliver only the optimized code with brief comments explaining your unique contributions.
    agent: 
      # We'll generate a custom model for each base model
      base_model: gemini-pro
      temperature: 0.98
      system_prompt: | 
        You're an expert Python developer. Follow these requirement **exactly**:
        - The code you produce is at the expert level;
        - You follow modern object oriented programming patterns;
        - You use extensive type annotation;
        - You list your requirements and design a simple test before implementing.
        Review the user's request and follow your requirements.
    postprocessor:
      base_model: gpt-3.5-turbo
      temperature: 0.1
      system_prompt: |
        You have one job: return the source code provided in the user's message. 
        **ONLY** return the exact source code. Your response is not read by a human.
        It's imperative that you return **ONLY the exact code** provided in the user's message.
    # Evaluators have defined system prompts to only return true / false for their domain.
    evaluator:
      base_model: gpt-4-1106-preview
      temperature: 0.1
      system_prompt: |
        Act as a validator. You'll return only TRUE or FALSE. The criteria for an above-average solution are as follows:
        1. The solution correctly implements the scaled dot-product attention.
        2. The solution includes efficient use of matrix operations in Python.
        3. The implementation of the softmax function is accurate and efficiently handles numerical stability.

        The following is an example of what you may partially see. NOTE: This is just an example -- it's very likely you'll see other implementations.
        [example]
        ```py
        import numpy as np

        def softmax(x):
            e_x = np.exp(x - np.max(x))
            return e_x / e_x.sum(axis=0)

        def scaled_dot_product_attention(Q, K, V, scale_factor):
            dot_product = np.dot(Q, K.T)
            scaled_dot_product = dot_product / np.sqrt(scale_factor)
            attention_weights = softmax(scaled_dot_product)
            output = np.dot(attention_weights, V)
            return output

        # Test inputs
        Q = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        K = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        V = np.array([[1, 2], [3, 4], [5, 6]])
        scale_factor = len(K[0])

        # Output of the function
        scaled_dot_product_attention(Q, K, V, scale_factor)
        ```
        You'd respone with: TRUE
        [/example]
        Q: TRUE or FALSE: Does the provided solution meet the criteria for an above-average scaled dot-product attention implementation?
```
