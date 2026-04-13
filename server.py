import logging
import os
import uuid

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agentexecutor import TravelPlannerAgentExecutor
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from planner_agent.agent import root_agent as travel_planner_agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception raised when a required API key is absent."""

    pass


def create_app():
    """Creates the Multi-Agent Travel Planner A2A agent server."""
    host = "localhost"
    port = 8000  # Port 8000 matches what the Next.js frontend proxy expects

    try:
        # ------------------------------------------------------------------
        # API-key validation
        # ------------------------------------------------------------------
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError(
                    "GOOGLE_API_KEY environment variable not set and "
                    "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )

        # ------------------------------------------------------------------
        # Agent Card — describes the Travel Planner agent's capabilities
        # ------------------------------------------------------------------
        capabilities = AgentCapabilities(streaming=True)

        # Four skills matching the travel planner agent's capabilities
        skill_plan_trip = AgentSkill(
            id="plan_trip",
            name="Plan Trip Itinerary",
            description=(
                "Generate a comprehensive day-by-day travel itinerary for any "
                "destination. Concurrently researches flight options, hotel "
                "accommodations, and sightseeing activities, then synthesizes "
                "them into a beautifully formatted Markdown travel guide."
            ),
            tags=["travel", "itinerary", "planning", "trip"],
            examples=[
                "Plan a 5-day trip to Tokyo from New York in March",
                "I want to visit Paris for a week, departing from London on June 10th with a budget of $2000",
            ],
        )

        skill_flights = AgentSkill(
            id="find_flights",
            name="Find Flight Options",
            description=(
                "Research and recommend the best flight options for a given "
                "route and travel date, including airline, duration, layovers, "
                "and estimated pricing."
            ),
            tags=["flights", "travel", "booking", "airlines"],
            examples=[
                "Find flights from Mumbai to Dubai on December 15th",
                "What are the best flight options from NYC to London?",
            ],
        )

        skill_hotels = AgentSkill(
            id="find_hotels",
            name="Find Hotel Accommodations",
            description=(
                "Recommend top-rated hotel accommodations for a destination "
                "based on stay duration, including ratings, pricing per night, "
                "and key amenities."
            ),
            tags=["hotels", "accommodation", "travel", "booking"],
            examples=[
                "Find hotels in Bali for a 7-night stay",
                "What hotels are recommended in Rome for a budget trip?",
            ],
        )

        skill_sightseeing = AgentSkill(
            id="find_sightseeing",
            name="Find Sightseeing & Activities",
            description=(
                "Discover top attractions, local experiences, hidden gems, and "
                "dining recommendations for any travel destination."
            ),
            tags=["sightseeing", "attractions", "activities", "dining", "travel"],
            examples=[
                "What are the top things to do in Amsterdam?",
                "Recommend local dining and attractions in Bangkok",
            ],
        )

        agent_card = AgentCard(
            name="trip_planner_agent",
            description=(
                "Multi-Agent Trip Planner powered by Google ADK. Uses a "
                "parallel-to-sequential architecture to concurrently research "
                "flights, hotels, and sightseeing options, then synthesizes "
                "them into a cohesive Markdown travel itinerary."
            ),
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill_plan_trip, skill_flights, skill_hotels, skill_sightseeing],
        )

        # ------------------------------------------------------------------
        # ADK Runner + TravelPlannerAgentExecutor
        # ------------------------------------------------------------------
        runner = Runner(
            app_name=agent_card.name,
            agent=travel_planner_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        agent_executor = TravelPlannerAgentExecutor(runner=runner, event_queue=None)

        # ------------------------------------------------------------------
        # A2A request handler & Starlette application
        # ------------------------------------------------------------------
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        a2a_app = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        ).build()

        # ------------------------------------------------------------------
        # REST bridge: POST /api/plan  <-- called by the Next.js frontend
        # Accepts: { "prompt": "..." }
        # Returns: { "itinerary": "...markdown..." }
        # ------------------------------------------------------------------
        async def plan_endpoint(request: Request) -> JSONResponse:
            try:
                body = await request.json()
                prompt = body.get("prompt", "").strip()
                if not prompt:
                    return JSONResponse({"error": "prompt is required"}, status_code=400)

                session_id = str(uuid.uuid4())
                session = await runner.session_service.create_session(
                    app_name=agent_card.name,
                    user_id="frontend_user",
                    session_id=session_id,
                )
                message = genai_types.Content(
                    role="user",
                    parts=[genai_types.Part(text=prompt)],
                )
                itinerary = ""
                async for event in runner.run_async(
                    session_id=session.id,
                    user_id="frontend_user",
                    new_message=message,
                ):
                    # Collect text from the final response event.
                    # Do NOT break early — the ADK ParallelAgent uses an
                    # asyncio.TaskGroup internally. Closing the async generator
                    # before it finishes (via break) raises GeneratorExit inside
                    # the TaskGroup and produces a noisy BaseExceptionGroup log.
                    if event.is_final_response() and event.content:
                        # Overwrite itinerary to ensure we only keep the LAST final response.
                        # This safely discards the intermediate JSON responses from the parallel sub-agents.
                        current_text = "".join(part.text for part in event.content.parts if part.text)
                        if current_text:
                            itinerary = current_text

                return JSONResponse({"itinerary": itinerary})
            except Exception as exc:
                logger.exception("Error in /api/plan: %s", exc)
                return JSONResponse({"error": str(exc)}, status_code=500)

        # Mount the REST bridge at /api/plan and fall back to the A2A app
        app = Starlette(
            routes=[
                Route("/api/plan", plan_endpoint, methods=["POST"]),
                Mount("/", app=a2a_app),
            ]
        )

        logger.info(
            "Starting Travel Planner server at http://%s:%d", host, port
        )
        logger.info("  ➜ A2A protocol : http://%s:%d/", host, port)
        logger.info("  ➜ REST bridge  : http://%s:%d/api/plan", host, port)

        return app

    except MissingAPIKeyError as e:
        logger.error("Configuration error: %s", e)
        exit(1)
    except Exception as e:
        logger.error("An error occurred during server startup: %s", e)
        exit(1)


app = create_app()

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
