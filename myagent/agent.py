from .prompt import BasePrompt
from .model import BaseModel
from .client import MCPClient
from . import errors
from mcp import types
import json

def tool2json(tool:types.Tool) -> dict:
    return {
        'name':tool.name,
        'description':tool.description,
        'parameters':{
            'type':tool.inputSchema.get('type','object'),
            'required':tool.inputSchema.get('required',[]),
            'properties':{k:{'type':v['type']} for k,v in tool.inputSchema.get('properties',{}).items()}
        }
    }

class Agent:
    def __init__(self, name:str, model:BaseModel, prompt:BasePrompt) -> None:
        self.name:str = name

        self.llm:BaseModel = model
        self.prompt:BasePrompt = prompt

        self.server_list:list[str] = []
        self.mcp_clients:list[MCPClient] = []

    def register_mcp(self, path:str):
        '''
        register mcp client/server (server script path)
        it only supports stdio mcp server (for now)
        '''
        self.server_list.append(path)

    async def init_mcp_client(self):
        for server_path in self.server_list:
            client = MCPClient()
            await client.connect_to_server(server_path)
            self.mcp_clients.append(client)

    async def clean_mcp_client(self):
        for client in self.mcp_clients:
            await client.cleanup()

    def _list_tools(self):
        #TODO : list_tools request (MCP Client -> MCP Server )
        #TODO : add Tool Signatures to Prompt (if they exists)
        ...
    

    async def __aenter__(self):
        await self.init_mcp_client()

        tools = await self.mcp_clients[0].list_tools()
        func_scheme_list = []
        for tool in tools:
            func_scheme_list.append(tool2json(tool))

        #* Llama 3.2
#         system_prompt = f"""You are an expert in composing functions. You are given a question and a set of possible functions. 
# Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
# If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
# also point it out. You should only return the function call in tools call sections.

# If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]\n
# You SHOULD NOT include any other text in the response.

# Here is a list of functions in JSON format that you can invoke.\n\n{json.dumps(func_scheme_list)}\n
# """
        #* LLama 3.1
        system_prompt = f"""When you receive a tool call response, use the output to format an answer to the orginal user question.

You are a helpful assistant with tool calling capabilities.
Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.

Respond in the format {{"name": function name, "parameters": dictionary of argument name and its value}}. Do not use variables.

{json.dumps(func_scheme_list)}
"""
        self.prompt.set_system_prompt(system_prompt)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.clean_mcp_client()

    def chat(self, question:str) -> str:
        prompt = self.prompt.get_prompt(question)
        print(prompt)
        response = self.llm.generate(prompt)

        # self.prompt.history.append_chat(question=question, answer=answer)

        return response

