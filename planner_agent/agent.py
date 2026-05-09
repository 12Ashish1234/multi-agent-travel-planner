from google.adk.agents import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from planner_agent.instructions import (
    FLIGHT_AGENT_INSTRUCTION,
    HOTEL_AGENT_INSTRUCTION,
    SIGHTSEEING_AGENT_INSTRUCTION,
    TRIP_PLANNER_INSTRUCTION,
    INTENT_ROUTER_INSTRUCTION,
    CHAT_AGENT_INSTRUCTION
)
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = os.getenv("MODEL", "ollama_chat/gemma4:31b-cloud")

# --- Specialized Research Agents ---

flight_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="FlightAgent",
    description="Flight booking agent",
    instruction=FLIGHT_AGENT_INSTRUCTION,
    output_key="flight_options"
)

hotel_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="HotelAgent",
    description="Hotel booking agent",
    instruction=HOTEL_AGENT_INSTRUCTION,
    output_key="hotel_options",
)

sightseeing_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="SightseeingAgent",
    description="Sightseeing information agent",
    instruction=SIGHTSEEING_AGENT_INSTRUCTION,
    output_key="sightseeing_options"
)

# --- Orchestration Layers ---

# Parallel Agent gathering all research data
parallel_researcher = ParallelAgent(
    name="ParallelTripAgents",
    sub_agents=[flight_agent, hotel_agent, sightseeing_agent],
    description="Runs flight, hotel, and sightseeing agents concurrently to gather comprehensive trip options."
)

# Synthesis Agent crafting the final markdown
planner_synthesis_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="PlannerAgent",
    instruction=TRIP_PLANNER_INSTRUCTION,
    description="Synthesizes all the parallel research into a well-formatted Markdown itinerary."
)

# The full Research Pipeline as a single unit
research_pipeline = SequentialAgent(
    name="ResearchPipeline",
    sub_agents=[parallel_researcher, planner_synthesis_agent],
    description="Executes full research for flights, hotels, and sightseeing, then generates a complete itinerary. Use this for new trips or major changes."
)

# Simple Chat Agent for conversational turns
chat_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="ChatAgent",
    instruction=CHAT_AGENT_INSTRUCTION,
    description="Handles greetings, thank yous, and simple conversational questions about the existing plan. Use this for non-research tasks."
)

# --- Root Router Agent ---

# The IntentAgent acts as the dispatcher (Router)
root_agent = LlmAgent(
    model=LiteLlm(model=MODEL),
    name="IntentAgent",
    instruction=INTENT_ROUTER_INSTRUCTION,
    sub_agents=[chat_agent, research_pipeline],
    description="Main entry point. Analyzes user intent and delegates to either ResearchPipeline for trip planning or ChatAgent for simple conversation."
)
