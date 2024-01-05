"""
File: agent.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Models the agents described in the YAML configuration.
             Agents execute tasks.
"""

class Agent:
    def __init__(self, base_model, temperature, system_prompt):
        self.base_model = base_model
        self.temperature = temperature
        self.system_prompt = system_prompt

if __name__ == "__main__":
    agent_config = {
        'base_model': 'gemini-pro',
        'temperature': 0.1,
        'system_prompt': 'An example of a buffer overflow bug.',
        'run_count': 10
    }
    llm_agent = Agent(**agent_config)
    print(llm_agent.base_model)
