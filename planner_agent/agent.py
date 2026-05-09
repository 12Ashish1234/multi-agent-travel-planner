from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from planner_agent.instructions import (
    FLIGHT_AGENT_INSTRUCTION,
    HOTEL_AGENT_INSTRUCTION,
    SIGHTSEEING_AGENT_INSTRUCTION,
    TRIP_PLANNER_INSTRUCTION,
    MASTER_PLANNER_INSTRUCTION,
    CHAT_AGENT_INSTRUCTION
)
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = os.getenv("MODEL", "ollama_chat/gemma4:31b-cloud")

# --- Specialized Agents ---
# Flat hierarchy: MasterPlanner is the root with access to all specialists.

flight_worker = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="FlightAgent",
    description="Researches flights. Return results in strictly valid JSON format only.",
    instruction=FLIGHT_AGENT_INSTRUCTION
)

hotel_worker = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="HotelAgent",
    description="Researches hotels. Return results in strictly valid JSON format only.",
    instruction=HOTEL_AGENT_INSTRUCTION
)

sightseeing_worker = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="SightseeingAgent",
    description="Researches activities. Return results in strictly valid JSON format only.",
    instruction=SIGHTSEEING_AGENT_INSTRUCTION
)

synthesis_worker = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="SynthesisAgent",
    description="Builds the final Markdown itinerary from research data.",
    instruction=TRIP_PLANNER_INSTRUCTION
)

chat_worker = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="ChatAgent",
    description="Handles simple conversation and greetings.",
    instruction=CHAT_AGENT_INSTRUCTION
)

# --- The Master Root Agent ---

# MasterPlanner acts as a Router/Director. 
# It delegates turns to specialists and expects control back.
root_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="MasterPlanner",
    instruction=MASTER_PLANNER_INSTRUCTION,
    sub_agents=[
        flight_worker,
        hotel_worker,
        sightseeing_worker,
        synthesis_worker,
        chat_worker
    ],
    description="Main entry point. Coordinates specialists dynamically based on user needs."
)
