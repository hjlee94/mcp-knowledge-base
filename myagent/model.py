from typing_extensions import Self
from llama_cpp import Llama
from .types import BaseModel
import os


class LlamaCPP(BaseModel):
    def __init__(self, name:str, model:Llama):
        self.name = name
        self.model = model
        self.max_tokens = 1024

    @classmethod
    def from_path(cls, model_path:str, n_ctx:int=131072, **kwargs) -> Self:
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            verbose=False,
            **kwargs
        )

        return cls(name = os.path.basename(model_path), model=model)

    def generate(self, prompt:str, **kwargs) -> str:
        if 'max_tokens' not in kwargs:
            kwargs['max_tokens'] = self.max_tokens

        output = self.model(prompt, **kwargs)
        choices = output['choices']
        response = choices[0]['text'].strip()
        return response