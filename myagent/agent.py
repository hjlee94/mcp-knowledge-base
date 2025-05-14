from typing import AsyncGenerator
from .prompt import BasePrompt
from .model import BaseModel
from .client import MCPClientMaanger
from .types import AgentResponse
from . import errors
from . import utils
import json
import re
import logging


SYSTEM_PROMPT = """You are a helpful assistant"""

#* Llama 3.2
TOOL_CALL_PROMPT = """You are an expert in composing functions. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(), func_name2(params_name1=params_value1, params_name2=params_value2...), func_name3(params)]
You SHOULD NOT include any other text in the response.

Here is a list of functions in JSON format that you can invoke.

{function_scheme}
"""

#* LLama 3.1
# TOOL_CALL_PROMPT = """When you receive a tool call response, use the output to format an answer to the orginal user question.

# You are a helpful assistant with tool calling capabilities.
# Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.

# Respond in the format {{"name": function name, "parameters": dictionary of argument name and its value}}. Do not use variables.

# {function_scheme}

# Here is a list of registered resources in the knowledge vault.

# {resource_list}
# # """

logger = logging.getLogger('agent')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

class Agent:
    def __init__(self, name:str, model:BaseModel, prompt:BasePrompt) -> None:
        self.name:str = name

        self.llm:BaseModel = model
        self.prompt:BasePrompt = prompt

        self.mcp_manager = MCPClientMaanger()

        self.func_scheme_prompt = ""
        self.resource_prompt = ""

        self.tool_pattern = re.compile(r'\[([A-Za-z0-9\_]+\(([A-Za-z0-9\_]+=\"?.+\"?,?\s?)*\),?\s?)+\]')
        self.func_pattern = re.compile(r'(?P<function>[A-Za-z0-9\_]+)\((?P<params>[A-Za-z0-9\_]+=\"?.+\"?,?\s?)*\)')

    @property
    def model_name(self):
        return self.llm.name
    
    @property
    def server_list(self):
        return self.mcp_manager.get_server_names()
    
    def register_mcp(self, path:str):
        self.mcp_manager.register_mcp(path)

    async def init_agent(self):
        await self.mcp_manager.init_mcp_client()

        func_scheme_list = await self.mcp_manager.get_func_scheme()
        resource_list = await self.mcp_manager.get_resource_list()

        self.func_scheme_prompt = json.dumps(func_scheme_list)
        self.resource_prompt = json.dumps(resource_list)
        
        p = self.prompt.get_system_prompt(SYSTEM_PROMPT)
        self.prompt.set_system_prompt(p)

    async def clean_agent(self):
        await self.mcp_manager.clean_mcp_client()

    async def __aenter__(self):
        await self.init_agent()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.clean_agent()

    def _is_tool_required(self, response:str):
        return self.tool_pattern.match(response)

    def get_func_props(self, response:str):
        for signature in response.strip('[]').split(','):
            signature = signature.strip()

            if res := self.func_pattern.findall(signature):
                name, param_string = res[0]
                yield name, utils.param2dict(param_string)

    async def get_result_tool(self, response:str) -> list[list[str]]:
        result_list = []

        for name, param in self.get_func_props(response):
            res = await self.mcp_manager.call_tool(name, param)
            is_err, content_list = res
            logger.debug(f"mcp function({name}) with param({param}) has results({content_list})")

            results = [c.text for c in content_list]

            result_list.append({'name':name, 'output':results})
        
        return result_list

    async def chat(self, question:str, **kwargs) -> list[AgentResponse]:
        response_list = []

        logger.debug(f"agent got question({question})")

        tool_scheme = TOOL_CALL_PROMPT.format(
            function_scheme=self.func_scheme_prompt
            )
        
        p = self.prompt.get_user_prompt(question=question, tool_scheme=tool_scheme)
        self.prompt.append_history(p)
        
        response = self.llm.generate(self.prompt.get_generation_prompt(tool_enabled=True), **kwargs)
        response = response.strip().lstrip('()<>\{\}`') #! remove noise (temporal)

        logger.debug(f"llm generated response ({response})")

        if self._is_tool_required(response):
            logger.debug(f"agent tool required")
            response_list.append(AgentResponse(type="tool-calling", data=response))

            p = self.prompt.get_assistant_prompt(answer=response)
            self.prompt.append_history(p)

            result = await self.get_result_tool(response)
            result = json.dumps(result, ensure_ascii=False)

            response_list.append(AgentResponse(type="tool-result", data=result))

            logger.debug(f"got result of each tool ({result})")

            p = self.prompt.get_tool_result_prompt(result=result)
            self.prompt.append_history(p)

            response = self.llm.generate(self.prompt.get_generation_prompt(tool_enabled=False, last=3), **kwargs)

            logger.debug(f"llm generated final response({response})")

        response_list.append(AgentResponse(type="text", data=response))

        p = self.prompt.get_assistant_prompt(answer=response)
        self.prompt.append_history(p)

        return response_list

