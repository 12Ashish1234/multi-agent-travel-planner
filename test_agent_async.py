import asyncio
from google.adk.agents.invocation_context import InvocationContext
from planner_agent.agent import root_agent

async def main():
    ctx = InvocationContext()
    ctx.chat_history.append({"role": "user", "content": "I want to visit Tokyo for 3 days"})
    async for event in root_agent.run_async(ctx):
        if event.content:
            print("Content:", event.content.text)

if __name__ == "__main__":
    asyncio.run(main())
