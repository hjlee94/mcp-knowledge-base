from .types import BasePrompt
import json

class History:
    def __init__(self, max_history=50) -> None:
        self._history = []
        self._max_history = max_history

    def append_prompt(self, prompt):
        self._history.append(prompt)

        self._history = self._history[-self._max_history:]

    def get_chat_history(self, last=0):
        if last < 0:
            return []
        
        if last > 0:
            return self._history[-last:]
        
        return self._history
    
    def clear(self):
        self._history = []

class LlamaPrompt(BasePrompt):
    def __init__(self) -> None:
        self.set_system_prompt("You are a helpful assistant.")
        self.history = History()

    def set_system_prompt(self, system_prompt:str):
        # self._system_prompt = f"<|begin_of_text|>" #! duplicate??
        self._system_prompt = f"<|start_header_id|>system<|end_header_id|>"
        self._system_prompt += f"{system_prompt}<|eot_id|>"

    def append_user_prompt(self, question:str) -> str:
        prompt = f"<|start_header_id|>user<|end_header_id|>"
        prompt += f"{question}<|eot_id|>"

        self.history.append_prompt(prompt)

        return prompt

    def append_assistant_prompt(self, answer):
        prompt = self.get_assistant_prompt(answer=answer)
        self.history.append_prompt(prompt)
        return prompt

    def append_tool_result_prompt(self, result:str) -> str:
        prompt = f"<|start_header_id|>ipython<|end_header_id|>"
        prompt += f"{result}<|eot_id|>"
        
        self.history.append_prompt(prompt)

        return prompt

    def get_assistant_prompt(self, answer:str="") -> str:
        prompt = f"<|start_header_id|>assistant<|end_header_id|>"
        if answer:
            prompt += f"{answer}<|eot_id|>"

        return prompt
    
    def get_prompt(self, history_k:int=50) -> str:
        prompt = f"{self._system_prompt}"

        for p in self.history.get_chat_history(last=history_k):
            prompt += p

        prompt += self.get_assistant_prompt()
        
        return prompt

