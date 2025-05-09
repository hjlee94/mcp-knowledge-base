from typing import Optional
import abc

class BasePrompt:
    @abc.abstractmethod
    def set_system_prompt(self, system_prompt:str):
        ...

    @abc.abstractmethod
    def append_user_prompt(self, question:str) -> str:
        ...

    @abc.abstractmethod
    def append_assistant_prompt(self, answer:str) -> str:
        ...

    @abc.abstractmethod
    def append_tool_result_prompt(self, result:str) -> str:
        ...
    
    @abc.abstractmethod
    def get_assistant_prompt(self, answer:Optional[str]="") -> str:
        ...
    
    @abc.abstractmethod
    def get_prompt(self, question:str, history_k:int=50) -> str:
        ...


class BaseModel:
    @abc.abstractmethod
    def generate(self, prompt:BasePrompt) -> str:
        '''generate a response based on the current prompt'''
        ...