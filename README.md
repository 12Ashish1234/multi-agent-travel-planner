# Trip Planner Agent

This is a multi-agent trip planning application built using the [Google Agent Development Kit (ADK)](https://github.com/google/adk). It uses a parallel-to-sequential agent architecture to gather flight options, hotel accommodations, and sightseeing recommendations concurrently, then synthesizes them into a cohesive Markdown itinerary.

The application is built with a **FastAPI** backend that runs the ADK agent pipeline, and a modern **Next.js** frontend for an interactive user interface. The entire stack is fully containerized using **Docker Compose**.

## Design Architecture

The application follows a modular and hierarchical design:

![Architecture Diagram](docs/images/architecture_diagram.png)

1.  **Orchestration**: A `SequentialAgent` (Root) manages the high-level flow.
2.  **Parallel Research**: A `ParallelAgent` triggers the Flight, Hotel, and Sightseeing agents simultaneously to reduce turnaround time.
3.  **Synthesis**: The final `Agent` (Planner) takes the JSON outputs from the research layer and crafts a user-friendly Markdown itinerary.

## Agent Roles (Powered by Gemini)

| Agent | Responsibility | Output Format |
| :--- | :--- | :--- |
| **Flight Agent** | Researches flight routes, durations, and pricing. | Structured JSON |
| **Hotel Agent** | Identifies top-rated accommodations and amenities. | Structured JSON |
| **Sightseeing Agent** | Recommends local attractions and dining spots. | Structured JSON |
| **Planner Agent** | Synthesizes research into a beautiful Markdown guide. | Markdown |

> **Note**: All agents in this repository use the **Gemini 2.5 Flash** model for fast, accurate generation.

## Prerequisites

1. **Docker and Docker Compose** installed on your system.
2. A valid **Google API Key** to use the Gemini models.

## Setup Instructions

### 1. Configure the Environment
Navigate to the `planner_agent` directory and create an `.env` file (if you haven't already). Insert your Google API key:

```text
GOOGLE_API_KEY="your-api-key-here"
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

### 2. Formulate the Network
This application leverages Next.js API Routes to securely proxy frontend browser requests into the backend container running on an isolated `trip_network`. You do not need to configure any manual network settings.

### 3. Run the Application with Docker Compose
From the project root, build and start the application using Docker Compose:

```bash
docker-compose up --build
```

### 4. Access the Planner
Once the containers are successfully built and orchestrated:
- **Frontend UI**: Open your browser to [http://localhost:3000](http://localhost:3000) to access the interactive web application.
- **Backend API**: The FastAPI backend runs silently in the background on port `8000`.

## Local Development (Without Docker)

If you wish to run the services manually without Docker:
1. Ensure Node.js 20+ and Python 3.11+ are installed.
2. **Backend**: From the root directory, install dependencies (`pip install -r requirements.txt`) and run `uvicorn server:app --reload`.
3. **Frontend**: From the `frontend/` directory, install packages (`npm install`) and start the developer server (`npm run dev`).
