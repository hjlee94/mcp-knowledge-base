from myagent import Agent, LlamaCPP, LlamaPrompt
import asyncio

async def run_agent():
    model = LlamaCPP.from_path('./models/llama-8b-v3.1-F16.gguf')
    prompt = LlamaPrompt()
    agent = Agent(name="knowledge-agent", model=model, prompt=prompt)

    agent.register_mcp(path="./run_server.py")

    async with agent:
        response = agent.chat("who are you?")
        print(response)


if __name__ == '__main__':
    asyncio.run(run_agent())
