from typing import Optional, Any
from .types import BasePrompt, BaseMessage
import json

class History:
    def __init__(self, max_history:int=50) -> None:
        self._history:list[BaseMessage] = []
        self._max_history:int = max_history

    def append_message(self, msg:BaseMessage):
        self._history.append(msg)
        self._history = self._history[-self._max_history:]

    def get_chat_history(self, last:int=0) -> list[BaseMessage]:
        if last < 0:
            return []
        
        if last > 0:
            return self._history[-last:]
        
        return self._history
    
    def clear(self):
        self._history = []

class LLamaMessage(BaseMessage):
    def __init__(self, role:str, content:str='', tool_scheme:str=''):
        self.role:str = role
        self.content:str = content
        self.tool_scheme:str = tool_scheme

    def template(self, tool_enabled:bool=False) -> str:
        #* Llama CPP insert BOS token internally
        prompt = f"<|start_header_id|>{self.role}<|end_header_id|>"

        if tool_enabled and self.tool_scheme:
            prompt += f"{self.tool_scheme}"

        if self.content:
            prompt += f"{self.content}<|eot_id|>"

        return prompt

class LlamaPrompt(BasePrompt):
    ROLE_SYSTEM = 'system'
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_TOOL = 'ipython'

    def __init__(self) -> None:
        self.system_prompt:BaseMessage = LLamaMessage('system', "You are a helpful assistant.")
        self.history:History = History()

    def append_history(self, message:LLamaMessage):
        self.history.append_message(message)
    
    def set_system_prompt(self, system_prompt:LLamaMessage):
        self.system_prompt = system_prompt

    def get_system_prompt(self, system_prompt:str):
        return LLamaMessage(LlamaPrompt.ROLE_SYSTEM, system_prompt)

    def get_user_prompt(self, question:str, tool_scheme:str='') -> LLamaMessage:
        return LLamaMessage(LlamaPrompt.ROLE_USER, question, tool_scheme=tool_scheme)

    def get_assistant_prompt(self, answer:Optional[str]="") -> LLamaMessage:
        return LLamaMessage(LlamaPrompt.ROLE_ASSISTANT, answer)
    
    def get_tool_result_prompt(self, result:str) -> LLamaMessage:
        return LLamaMessage(LlamaPrompt.ROLE_TOOL, result)
    
    def get_generation_prompt(self, tool_enabled:bool=False, last:int=50) -> str:
        prompt = [self.system_prompt]
        prompt += self.history.get_chat_history(last=last)
        prompt += [self.get_assistant_prompt(answer='')] #* generation prompt
        print(prompt)
        return ''.join([p.template(tool_enabled=tool_enabled) for p in prompt])