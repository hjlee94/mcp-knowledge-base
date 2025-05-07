from typing import Callable, List

import yaml

class History:
    def __init__(self, max_history=50) -> None:
        self._history = []
        self._max_history = max_history

    def append_chat(self, question, answer):
        self._history.append(
            dict(q=question, a=answer)
        )

        self._history = self._history[self._max_history:]

    def get_chat_history(self, last=0):
        if last > 0:
            return self._history[-last:]
        
        return self._history
    
    def clear(self):
        self._history = []

class Prompt:
    def __init__(self, system_prompt:str) -> None:
        #<|begin_of_text|>
        self._system_prompt = f"<|start_header_id|>system<|end_header_id|>"
        self._system_prompt+= f"{system_prompt}<|eot_id|>"
        
        self.history = History()

    def get_user_prompt(self, question:str) -> str:
        prompt = f"<|start_header_id|>user<|end_header_id|>"
        prompt += f"{question}<|eot_id|>"
        return prompt

    def get_assistant_prompt(self, answer:str="") -> str:
        prompt = f"<|start_header_id|>assistant<|end_header_id|>"
        if answer:
            prompt += f"{answer}<|eot_id|>"

        return prompt

    def get_prompt(self, question:str, history_k:int=2) -> str:
        prompt = f"{self._system_prompt}"

        if history_k > 0:
            for h in self.history.get_chat_history(last=history_k):
                hq = h['q']; ha = h['a']

                prompt += self.get_user_prompt(question=hq)
                prompt += self.get_assistant_prompt(answer=ha)

        prompt += self.get_user_prompt(question=question)
        prompt += self.get_assistant_prompt()
        
        return prompt

