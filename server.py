from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from planner_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    prompt: str

# Initialize the Runner with InMemorySessionService
runner = Runner(
    app_name="trip_planner",
    agent=root_agent,
    session_service=InMemorySessionService(),
    auto_create_session=True
)

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    final_output = ""
    
    # Create the user message
    new_message = types.Content(role="user", parts=[types.Part.from_text(text=request.prompt)])

    try:
        # Run the agent using ADK Runner
        async for event in runner.run_async(
            user_id="anonymous",
            session_id="session_1",
            new_message=new_message
        ):
            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text:
                    if event.author == "PlannerAgent":
                        final_output += text
                    elif not final_output and event.author == "TripPlannerPipeline":
                        final_output += text
                    elif event.author == root_agent.name:
                        final_output += text
                    
        if not final_output:
            final_output = "No itinerary generated. Please ensure your prompt is clear."
        else:
            import re
            # Remove <think>...</think> blocks if present
            final_output = re.sub(r'<think>.*?</think>', '', final_output, flags=re.DOTALL)
            
            # Fallback for models that output "Thinking Process: ... Let's write it."
            # We can try to strip it if "Thinking Process:" is at the start and followed by a clear break.
            # But the prompt should ideally handle this now. Just in case, if we find "Thinking Process:",
            # we might split by the first double newline or markdown heading.
            # A simple rule: If it starts with "Thinking Process:", find the first actual markdown heading "#" or emoji flag.
            if "Thinking Process:" in final_output:
                # Find the first major heading or emoji that usually starts the itinerary
                match = re.search(r'(?:\n\n|\n)(#|🇯🇵|✈️|🏨|🗓️|Phase|\*\*Title:\*\*)', final_output)
                if match:
                    final_output = final_output[match.start():]
            
            final_output = final_output.strip()
            
    except Exception as e:
        print(f"Error executing runner: {e}")
        final_output = f"An error occurred while generating the plan: {str(e)}"

    return {"itinerary": final_output}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
