from .prompt import BasePrompt
from .model import BaseModel
from .client import MCPClient
from . import errors

class Agent:
    def __init__(self, name:str, model:BaseModel, prompt:BasePrompt) -> None:
        self.name = name

        self.prompt = prompt
        self.llm = model

        self.server_list = []
        self.mcp_clients = []

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

        #TODO : System prompt with function signatures
        self.prompt.set_system_prompt("You are a helpful assistant.")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.clean_mcp_client()

    def chat(self, question:str) -> str:
        prompt = self.prompt.get_prompt(question)
        response = self.llm.generate(prompt)

        # self.prompt.history.append_chat(question=question, answer=answer)

        return response

