from mcp import types
import json

def tool2dict(tool:types.Tool) -> dict:
    return {
        'name':tool.name,
        'description':tool.description,
        'parameters':{
            'type':tool.inputSchema.get('type','object'),
            'required':tool.inputSchema.get('required',[]),
            'properties':{k:{'type':v['type']} for k,v in tool.inputSchema.get('properties',{}).items()}
        }
    }

def resource2dict(resource:types.Resource) -> dict:
    return {
        'uri':str(resource.uri),
        'name':resource.name,
        'mimeType':resource.mimeType,
    }

def param2dict(pram_s:str) -> dict:
    params = {}
    
    if not pram_s:
        return params
    
    param_list = pram_s.split(',')

    for p in param_list:
        k,v = p.strip().split('=')
        params[k] = v.strip('\'\"')

    return params

def result2dict(result:types.TextContent):
    return result.text

def uri2path(s):
    return str(s).replace('%20', ' ').lower()