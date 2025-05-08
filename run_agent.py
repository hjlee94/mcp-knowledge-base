from myagent import Agent, LlamaCPP, LlamaPrompt
import asyncio

async def run_agent():
    model = LlamaCPP.from_path('./models/llama-8b-v3.1-F16.gguf')
    prompt = LlamaPrompt()
    agent = Agent(name="knowledge-agent", model=model, prompt=prompt)

    agent.register_mcp(path="./run_server.py")

    async with agent:
        # response = agent.chat("can you list which knowledges are in the vault?")
        response = agent.chat("can you show me the contents of the resource named Contrastive Learning? its uri is \"file://a/bb/c.md\"")
        print(response)


if __name__ == '__main__':
    asyncio.run(run_agent())
