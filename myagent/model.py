from typing_extensions import Self
from llama_cpp import Llama
from .types import BaseModel


class LlamaCPP(BaseModel):
    def __init__(self, model:Llama):
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

        return cls(model=model)

    def generate(self, prompt:str, **kwargs) -> str:
        output = self.model(prompt, max_tokens=self.max_tokens, **kwargs)
        choices = output['choices']
        response = choices[0]['text'].strip()
        return response