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
    session_id: str = "session_1"

# Initialize the Runner with InMemorySessionService
runner = Runner(
    app_name="trip_planner",
    agent=root_agent,
    session_service=InMemorySessionService(),
    auto_create_session=True
)

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    print(f"\n--- New Planning Request [Session: {request.session_id}] ---")
    print(f"User Prompt: {request.prompt[:100]}...")
    
    final_output = ""
    
    # Create the user message
    new_message = types.Content(role="user", parts=[types.Part.from_text(text=request.prompt)])

    try:
        # Run the agent using ADK Runner
        print(f"Starting ADK Runner for session: {request.session_id}")
        async for event in runner.run_async(
            user_id="anonymous",
            session_id=request.session_id,
            new_message=new_message
        ):
            if event.author:
                # Log the agent activity
                content_preview = ""
                if event.content and event.content.parts:
                    content_preview = "".join(p.text for p in event.content.parts if p.text)[:50].replace('\n', ' ')
                
                print(f"  [AGENT EVENT] Author: {event.author:20} | Content: {content_preview}...")

            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text:
                    # Collecting output from specific agents or the pipeline as per existing logic
                    if event.author == "PlannerAgent":
                        final_output += text
                    elif not final_output and event.author == "TripPlannerPipeline":
                        final_output += text
                    elif event.author == root_agent.name:
                        final_output += text
                    
        if not final_output:
            print("  [WARNING] No output collected from agents.")
            final_output = "No itinerary generated. Please ensure your prompt is clear."
        else:
            print(f"  [SUCCESS] Generated {len(final_output)} characters of itinerary.")
            import re
            # Remove <think>...</think> blocks if present
            final_output = re.sub(r'<think>.*?</think>', '', final_output, flags=re.DOTALL)
            
            # Fallback for models that output "Thinking Process: ... Let's write it."
            if "Thinking Process:" in final_output:
                match = re.search(r'(?:\n\n|\n)(#|🇯🇵|✈️|🏨|🗓️|Phase|\*\*Title:\*\*)', final_output)
                if match:
                    final_output = final_output[match.start():]
            
            final_output = final_output.strip()
            
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        final_output = f"An error occurred while generating the plan: {str(e)}"

    print(f"--- Request Complete ---\n")
    return {"itinerary": final_output}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
