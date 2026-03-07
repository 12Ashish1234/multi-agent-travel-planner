from google.adk.agents.llm_agent import Agent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from planner_agent.instructions import (
    FLIGHT_AGENT_INSTRUCTION,
    HOTEL_AGENT_INSTRUCTION,
    SIGHTSEEING_AGENT_INSTRUCTION,
    TRIP_PLANNER_INSTRUCTION
)

# Flight Agent: Specializes in flight booking and information
flight_agent = Agent(
    model=LiteLlm(model="ollama_chat/qwen3.5:cloud"),
    name="FlightAgent",
    description="Flight booking agent",
    instruction=FLIGHT_AGENT_INSTRUCTION,
    output_key="flight_options"
)

# Hotel Agent: Specializes in hotel booking and information
hotel_agent = Agent(
    model=LiteLlm(model="ollama_chat/qwen3.5:cloud"),
    name="HotelAgent",
    description="Hotel booking agent",
    instruction=HOTEL_AGENT_INSTRUCTION,
    output_key="hotel_options"
)

# Sightseeing Agent: Specializes in providing sightseeing recommendations
sightseeing_agent = Agent(
    model=LiteLlm(model="ollama_chat/qwen3.5:cloud"),
    name="SightseeingAgent",
    description="Sightseeing information agent",
    instruction=SIGHTSEEING_AGENT_INSTRUCTION,
    output_key="sightseeing_options"
)

# Parallel Agent orchestrating the three specialized domains
parallel_agent = ParallelAgent(
    name="ParallelTripAgents",
    sub_agents=[flight_agent, hotel_agent, sightseeing_agent],
    description="Runs flight, hotel, and sightseeing agents concurrently to gather comprehensive trip options."
)

# Planner Agent synthesizing the options into a cohesive Markdown itinerary
planner_agent = Agent(
    model=LiteLlm(model="ollama_chat/qwen3.5:cloud"),
    name="PlannerAgent",
    instruction=TRIP_PLANNER_INSTRUCTION,
    description="Synthesizes all the parallel research into a well-formatted Markdown itinerary."
)

# Root Pipeline Agent executing the overall structure strictly sequence
root_agent = SequentialAgent(
    name="TripPlannerPipeline",
    sub_agents=[parallel_agent, planner_agent],
    description="Coordinates parallel research and synthesizes the final itinerary."
)