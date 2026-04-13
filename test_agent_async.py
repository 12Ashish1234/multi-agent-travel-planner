import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types
from planner_agent.agent import root_agent


async def main():
    runner = Runner(
        app_name="test_travel_planner",
        agent=root_agent,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    session = await runner.session_service.create_session(
        app_name="test_travel_planner", user_id="test_user"
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text="I want to visit Tokyo for 3 days")]
    )
    async for event in runner.run_async(
        session_id=session.id, user_id="test_user", new_message=message
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    print("Response:", part.text)


if __name__ == "__main__":
    asyncio.run(main())
