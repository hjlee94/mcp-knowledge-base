from typing import Optional, Literal
import abc
import pydantic

class BaseMessage:
    @abc.abstractmethod
    def template(self, tool_enabled:Optional[bool]=False) -> str:
        ...


class BasePrompt:
    @abc.abstractmethod
    def append_history(self, message:BaseMessage):
        ...
    
    @abc.abstractmethod
    def set_system_prompt(self, system_prompt:BaseMessage):
        ...

    @abc.abstractmethod
    def get_system_prompt(self, system_prompt:str):
        ...

    @abc.abstractmethod
    def get_user_prompt(self, question:str, tool_scheme:str='') -> BaseMessage:
        ...

    @abc.abstractmethod
    def get_assistant_prompt(self, answer:Optional[str]="") -> BaseMessage:
        ...
    
    @abc.abstractmethod
    def get_tool_result_prompt(self, result:str) -> BaseMessage:
        ...
    
    @abc.abstractmethod
    def get_generation_prompt(self, tool_enabled:bool=False, last:int=50) -> str:
        ...
    

class BaseModel:
    @abc.abstractmethod
    def generate(self, prompt:BasePrompt) -> str:
        '''generate a response based on the current prompt'''
        ...


class AgentResponse(pydantic.BaseModel):
    type: Literal["text", "tool-calling", "tool-result"]
    data: str