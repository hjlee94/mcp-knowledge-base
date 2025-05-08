import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import types


class KnowledgeVaultClient:
    def __init__(self):
        self.session = None
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
        await self.session.initialize()

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

async def test():
    client = KnowledgeVaultClient()
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
