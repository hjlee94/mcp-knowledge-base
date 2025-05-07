from llama_cpp import Llama
from .prompt import Prompt
from . import errors

class LlamaAgent:
    def __init__(self, name:str, model_path:str, prompt:Prompt=None, max_tokens:int=256, **kwargs) -> None:
        self.name = name
        
        self._llm = Llama(
            model_path=model_path,
            verbose=False,
            n_ctx=2048
            # n_gpu_layers=-1, # Uncomment to use GPU acceleration
            # seed=1337, # Uncomment to set a specific seed
        )

        self._llm_param = {}
        self.set_generation_mode()
        self._llm_param.update(kwargs)

        if not prompt:
            self.prompt = Prompt(system_prompt="You are a helpful assistant.")

        self._max_tokens = max_tokens

        #TODO : MCP Client

    def _list_tools(self):
        #TODO : list_tools request (MCP Client -> MCP Server )
        #TODO : add Tool Signatures to Prompt (if they exists)
        ...
    

    def __call__(self, question:str) -> str:
        # TODO : supports tool-calling
        if not self.prompt:
            raise errors.AgentException("You must set the prompt obejct for LlamaSpeaker")
        
        text = self.prompt.get_prompt(question=question, history_k=4)
        
        output = self._llm(text, max_tokens=self._max_tokens, 
                           **self._llm_param)

        choices = output['choices']
        answer = choices[0]['text'].strip()

        self.prompt.history.append_chat(question=question, answer=answer)

        return answer
