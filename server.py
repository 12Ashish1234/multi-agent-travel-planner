from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from planner_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

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

# Production Best Practice: Use environment variables for DB connection
# Default to local SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///trip_planner.db")

# Initialize the Database Session Service
session_service = DatabaseSessionService(db_url=DATABASE_URL)

# Initialize a single runner with the root IntentAgent and Persistent Session Service
runner = Runner(
    app_name="trip_planner",
    agent=root_agent,
    session_service=session_service,
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
                    # Capture text from user-facing agents
                    if event.author in ["MasterPlanner", "SynthesisAgent", "ChatAgent"]:
                        # Double-check: Skip raw JSON blocks or tool syntax artifacts
                        clean_text = text.strip()
                        if not clean_text.startswith("```json") and not clean_text.startswith("{") and not clean_text.startswith("["):
                            final_output += text
                    
        if not final_output:
            print("  [WARNING] No output collected from agents.")
            final_output = "I'm sorry, I couldn't process that. Could you please rephrase?"
        else:
            print(f"  [SUCCESS] Generated response.")
            final_output = re.sub(r'<think>.*?</think>', '', final_output, flags=re.DOTALL).strip()
            
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        final_output = f"An error occurred: {str(e)}"

    print(f"--- Request Complete ---\n")
    return {"itinerary": final_output}

# --- Session Management Endpoints ---

@app.get("/api/sessions")
async def list_sessions():
    """List all available chat sessions with descriptive titles."""
    try:
        print(f"Fetching sessions for app_name='trip_planner'...")
        response = await session_service.list_sessions(app_name="trip_planner", user_id="anonymous")
        sessions = response.sessions
        
        result = []
        for s_summary in sessions:
            title = s_summary.id # Fallback
            
            # Fetch full session to get events for the title
            try:
                full_session = await session_service.get_session(
                    app_name="trip_planner", 
                    user_id="anonymous", 
                    session_id=s_summary.id
                )
                if full_session and full_session.events:
                    for event in full_session.events:
                        if event.author == "user" and event.content and event.content.parts:
                            text = "".join(p.text for p in event.content.parts if p.text).strip()
                            if text:
                                title = (text[:30] + '...') if len(text) > 30 else text
                                break
            except Exception as e:
                print(f"  [WARNING] Could not fetch details for session {s_summary.id}: {e}")
            
            result.append({
                "id": s_summary.id,
                "title": title,
                "created_at": getattr(s_summary, 'created_at', None),
                "updated_at": s_summary.last_update_time
            })
        
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result
    except Exception as e:
        print(f"  [ERROR] list_sessions failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Retrieve the full history of a specific session."""
    try:
        session = await session_service.get_session(app_name="trip_planner", user_id="anonymous", session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert ADK events to a simple message format for the frontend
        history = []
        for event in session.events:
            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text:
                    role = "user" if event.author == "user" else "assistant"
                    # Capture user and user-facing agent responses
                    if event.author in ["user", "MasterPlanner", "SynthesisAgent", "ChatAgent"]:
                        # Skip raw research data
                        clean_text = text.strip()
                        if not clean_text.startswith("```json") and not clean_text.startswith("{") and not clean_text.startswith("["):
                            history.append({
                                "role": role,
                                "content": text,
                                "author": event.author
                            })
        return {"session_id": session_id, "history": history}
    except Exception as e:
        print(f"  [ERROR] get_session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    try:
        await session_service.delete_session(app_name="trip_planner", user_id="anonymous", session_id=session_id)
        return {"status": "deleted"}
    except Exception as e:
        print(f"  [ERROR] delete_session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
