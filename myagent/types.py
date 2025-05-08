from typing import Optional
import abc

class BasePrompt:
    @abc.abstractmethod
    def set_system_prompt(self, system_prompt:str):
        ...

    @abc.abstractmethod
    def get_user_prompt(self, question:str) -> str:
        ...
    
    @abc.abstractmethod
    def get_assistant_prompt(self, answer:Optional[str]="") -> str:
        ...
    
    @abc.abstractmethod
    def get_prompt(self, question:str, history_k:int=2) -> str:
        ...


class BaseModel:
    @abc.abstractmethod
    def generate(self, prompt:BasePrompt) -> str:
        '''generate a response based on the current prompt'''
        ...