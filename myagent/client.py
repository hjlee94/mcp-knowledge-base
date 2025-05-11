import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import types

from . import utils
from . import errors

class MCPClient:
    def __init__(self):
        self.session = None
        self.name = ''
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path:str):
        server_params = StdioServerParameters(
            command = "python",
            args=[server_script_path],
            env=None
        )

        # spawaning a process for running a mcp server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read, self.write = stdio_transport

        # init session using read/write pipes of the process spawned
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read, self.write))

        # connect server by sending initialize request
        init_result = await self.session.initialize()
        server_info = init_result.serverInfo
        self.name = f"{server_info.name}(v{server_info.version})"

    async def list_tools(self) -> list[types.Tool]:
        response = await self.session.list_tools()
        tools = response.tools
        return tools

    async def list_resources(self) -> list[types.Resource]:
        response = await self.session.list_resources()
        resources = response.resources
        return resources
    
    async def call_tool(self, name, args) -> tuple[bool, list[types.TextContent]]:
        response = await self.session.call_tool(name, args)
        return [response.isError, response.content]

    async def cleanup(self):
        await self.exit_stack.aclose()

class MCPClientMaanger:
    def __init__(self):
        self.server_path:list[str] = []
        self.clients:list[MCPClient] = []

        self.tool_map:dict[str, int] = dict()
        self.tool_info:dict[str, dict[str, str]] = dict()
        self.resource_map:dict[str, int] = dict()

    def register_mcp(self, server_path:str):
        '''
        register mcp client/server (server script path)
        it only supports stdio mcp server (for now)
        '''
        self.server_path.append(server_path)

    async def init_mcp_client(self):
        for path in self.server_path:
            c = MCPClient()
            await c.connect_to_server(path)

            self.clients.append(c)

    async def clean_mcp_client(self):
        for c in self.clients:
            await c.cleanup()

    def get_server_names(self):
        return list(filter(lambda x:x, [c.name for c in self.clients]))
    
    async def get_func_scheme(self) -> list[dict[str, str]]:
        func_scheme_list = []

        for idx, c in enumerate(self.clients):
            tools = await c.list_tools()

            for tool in tools:
                func_scheme_list.append(utils.tool2dict(tool))
                self.tool_map[tool.name] = idx
                
                func_info = self.tool_info.get(self.clients[idx].name, {})
                func_info[tool.name] = tool.description
                self.tool_info[self.clients[idx].name] = func_info

        return func_scheme_list

    async def get_resource_list(self) -> list[dict[str, str]]:
        resource_list = []

        for idx, c in enumerate(self.clients):
            resources = await c.list_resources()
            
            for rsrc in resources:
                resource_list.append(utils.resource2dict(rsrc))
                self.resource_map[utils.uri2path(rsrc.uri)] = idx

        return resource_list
    
    async def call_tool(self, name, param) -> tuple[bool, list[types.TextContent]]:
        idx = self.tool_map.get(name, -1)

        if idx < 0:
            raise errors.MCPException(f"Unknown tool name{name}")
        
        client = self.clients[idx]
        result = await client.call_tool(name, param)
        
        return result
        
async def test():
    client = MCPClient()
    path = './main.py'

    try:
        await client.connect_to_server(path)
        tools = await client.list_tools()
        print(tools)

        rsrc_list = await client.list_resources()
        for rsrc in rsrc_list[:5]:
            print(rsrc)

        res = await client.call_tool(name="list_knowledges", args={})
        if not res[0]:
            print(f"{len(res[1])} resources listed")

        rsrc = rsrc_list[1]
        res = await client.call_tool(name="get_knowledge_by_uri", args={'uri':rsrc.uri})
        print(res)
        
    finally:
        await client.cleanup()

if __name__ == '__main__':
    asyncio.run(test())
