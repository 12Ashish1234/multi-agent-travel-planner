from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from planner_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import json
import re

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

# Initialize a single runner with the root IntentAgent
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
    new_message = types.Content(role="user", parts=[types.Part.from_text(text=request.prompt)])

    try:
        # Run the agent using ADK Runner
        # The root IntentAgent will handle routing internally to ResearchPipeline or ChatAgent
        print(f"Starting execution with {root_agent.name}...")
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
                    # Collect output from the final agents in the hierarchy
                    # We collect from PlannerAgent (synthesis), ChatAgent (conversation), 
                    # or the pipeline/root names as fallbacks.
                    if event.author in ["PlannerAgent", "ChatAgent", "ResearchPipeline", "IntentAgent"]:
                        final_output += text
                    
        if not final_output:
            print("  [WARNING] No output collected from agents.")
            final_output = "I'm sorry, I couldn't process that. Could you please rephrase?"
        else:
            print(f"  [SUCCESS] Generated response.")
            # Clean up <think> blocks
            final_output = re.sub(r'<think>.*?</think>', '', final_output, flags=re.DOTALL).strip()
            
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        final_output = f"An error occurred: {str(e)}"

    print(f"--- Request Complete ---\n")
    return {"itinerary": final_output}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
