from myagent import Agent, LlamaCPP, LlamaPrompt
import asyncio

async def run_agent():
    # model = LlamaCPP.from_path('./models/llama-8b-v3.1-F16.gguf')
    model = LlamaCPP.from_path('./models/llama-3.2-3B-Instruct.gguf')
    prompt = LlamaPrompt()
    agent = Agent(name="knowledge-agent", model=model, prompt=prompt)

    agent.register_mcp(path="./run_server.py")

    async with agent:
        while (prompt := input('(prompt) ')) != 'bye':
            response = await agent.chat(prompt)

            for r in response:
                if r.type == 'text':
                    print(f"(assistant) {r.data}")
                elif r.type == 'tool-calling':
                    print(f"(assistant) tool calling {r.data}")
                elif r.type == 'tool-result':
                    print(f"(assistant) tool result {r.data}")

if __name__ == '__main__':
    asyncio.run(run_agent())
