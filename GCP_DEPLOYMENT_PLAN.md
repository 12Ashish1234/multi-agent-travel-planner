# GCP Deployment Architecture Plan

Deploying containerized frontend and backend applications to Google Cloud Platform (GCP) requires a few strategic architectural choices. For an AI trip planner application comprising a stateless Next.js frontend and a FastAPI backend, **Google Cloud Run** is highly recommended. It is a fully managed, serverless platform built precisely for Docker containers.

## Proposed Architecture

When migrating from Docker Compose to GCP Cloud Run, the local `docker network` connection is replaced by secure HTTPS routing.

### 1. Artifact Registry (Container Storage)
Before deploying, we must configure Google Artifact Registry.
- Create a Docker repository in Artifact Registry (e.g., `us-central1-docker.pkg.dev/YOUR-PROJECT/trip-planner-repo`).
- Tag our local `backend` and `frontend` Docker images.
- Push the images to this registry.

### 2. Secret Manager (Security)
To maintain the security posture we established locally, we should not expose your `GOOGLE_API_KEY` in plain text inside your container deployment variables.
- Create a secret in **Google Secret Manager** for the Gemini API Key.
- Grant the Cloud Run service account access to read this secret.

### 3. Backend Cloud Run Service
- Deploy the docker image from Artifact Registry to a new Cloud Run service named `trip-planner-backend`.
- **Considerations**:
  - Secure the backend to disallow public access? Since the Next.js server-side API proxy `route.js` will call it, we can keep the backend internal-only for tighter security, OR leave it public if you are iterating quickly. To keep it simple at the prototype phase, it's often easiest to deploy it publicly but rely on CORS/route obfuscation as a temporary measure.
  - Inject the secret from Secret Manager into the container environment as `GOOGLE_API_KEY`.
- **Output**: This deployment generates a stable HTTPS URL (e.g., `https://backend-xyz.a.run.app`).

### 4. Frontend Cloud Run Service
- Deploy the frontend docker image to a new Cloud Run Service named `trip-planner-frontend`.
- **Considerations**:
  - Set the runtime environment variable `BACKEND_URL` to equal the newly generated backend HTTPS URL.
  - Allow unauthenticated network traffic so public users can access the Next.js UI over the public internet.
  - Ensure the Cloud Run container allocates enough memory (e.g., 512MB or 1GB) for the Next.js server payload and rendering tasks.

## Deployment Execution Checklist

1. [ ] Install and authenticate the `gcloud` CLI (`gcloud auth login`).
2. [ ] Ensure a GCP Project is created and billing is enabled.
3. [ ] Enable required APIs: Cloud Run API, Secret Manager API, Artifact Registry API.
4. [ ] Push local Docker images to Artifact Registry.
5. [ ] Create a Secret in Secret Manager containing your Gemini API Key.
6. [ ] Deploy backend service pointing to the artifact, linking the Secret Manager key.
7. [ ] Deploy frontend service pointing to the artifact, setting the environment variable `BACKEND_URL` to the deployed backend's URL.
