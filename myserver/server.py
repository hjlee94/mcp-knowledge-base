from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import *
import glob, os

from .types import MarkdownResource
from .utils import uri2path
from .config import VAULT_PATH

from mcp.server.fastmcp.server import logger

class KnowledgeVaultServer:
    def __init__(self):
        self.app = FastMCP("knowledge-vault")
        
        self.resource_map = {}

        self._init_resources()
        self._init_tools()

    def _init_resources(self):
        file_list = glob.glob(os.path.join(VAULT_PATH, '*/*/*.md'))

        self.resource_map = {}
        for path in file_list:
            path = path.lower() #! XOS file system is case-insensitive
            uri = f"file://{os.path.relpath(path, start=VAULT_PATH)}".lower()

            rsrc = MarkdownResource(
                uri=uri, #! It converts the whitespace to %20
                name=os.path.basename(path).split('.')[0],
                mime_type="text/markdown",
                size=os.path.getsize(path)
            )
            self.resource_map[uri] = rsrc
            self.app.add_resource(rsrc)
            
    def _init_tools(self):
        
        @self.app.tool()
        async def list_knowledges() -> list[dict[str, str]]:
            '''List the names and URIs of all knowledges written in the the vault
            '''
            return [{'name':rsrc.name, 'uri':rsrc.uri, 'size':rsrc.size} for rsrc in self.resource_map.values()]
        
        @self.app.tool()
        async def get_knowledge_by_uri(uri:str) -> str:
            '''get contents of the knowledge resource by uri
            '''
            # logger.info(str(self.resource_map))
            uri = uri2path(uri)
            rsrc = self.resource_map.get(uri, None)
            if not rsrc:
                raise ValueError(f"Not registered resource URI")
            
            return await rsrc.read()

    def run(self):
        self.app.run(transport='stdio')

