from .prompt import BasePrompt
from .model import BaseModel
from .client import MCPClient, MCPClientMaanger
from . import errors
from . import utils
import json
import re
import logging

#* Llama 3.2
SYSTEM_PROMPT = """You are an expert in composing functions. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]
You SHOULD NOT include any other text in the response.

Here is a list of functions in JSON format that you can invoke.

{function_scheme}

Here is a list of registered resources in the knowledge vault.

{resource_list}
"""
#* LLama 3.1
# SYSTEM_PROMPT = """When you receive a tool call response, use the output to format an answer to the orginal user question.

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
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

class Agent:
    def __init__(self, name:str, model:BaseModel, prompt:BasePrompt) -> None:
        self.name:str = name

        self.llm:BaseModel = model
        self.prompt:BasePrompt = prompt

        self.mcp_manager = MCPClientMaanger()

        self.tool_pattern = re.compile(r'\[([A-Za-z0-9\_]+\(([A-Za-z0-9\_]+=\"?.+\"?,?\s?)*\),?\s?)+\]')
        self.func_pattern = re.compile(r'(?P<function>[A-Za-z0-9\_]+)\((?P<params>[A-Za-z0-9\_]+=\"?.+\"?,?\s?)*\)')

    def register_mcp(self, path:str):
        self.mcp_manager.register_mcp(path)

    async def __aenter__(self):
        await self.mcp_manager.init_mcp_client()

        func_scheme_list = await self.mcp_manager.get_func_scheme()
        resource_list = await self.mcp_manager.get_resource_list()
        
        self.prompt.set_system_prompt(SYSTEM_PROMPT.format(
             function_scheme=json.dumps(func_scheme_list),
             resource_list=json.dumps(resource_list)
        ))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.mcp_manager.clean_mcp_client()

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

    async def chat(self, question:str) -> str:
        logger.debug(f"agent got question({question})")
        self.prompt.append_user_prompt(question)
        response = self.llm.generate(self.prompt.get_prompt())
        response = response.lstrip('()<>\{\}') #! remove noise (temporal)

        logger.debug(f"llm generated response ({response})")

        if self._is_tool_required(response):
            logger.debug(f"agent tool required")
            self.prompt.append_assistant_prompt(response)

            result = await self.get_result_tool(response)
            result = json.dumps(result, ensure_ascii=False)

            logger.debug(f"got result of each tool ({result})")

            self.prompt.append_tool_result_prompt(result)

            response = self.llm.generate(self.prompt.get_prompt())

            logger.debug(f"llm generated final response({response})")

        return response

