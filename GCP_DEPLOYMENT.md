# 🚀 Deploying Trip Planner Agent to Google Cloud Platform (GCP)

This document outlines the step-by-step process for containerizing and deploying the multi-agent Trip Planner application to Google Cloud Run. 

It specifically covers configurations necessary for **Apple Silicon (M1/M2/M3)** users to successfully cross-compile and deploy to GCP's `linux/amd64` architecture.

---

## Prerequisites: Local Containerization & Testing

Before following this GCP deployment guide, ensure that you have:
1. **Created Dockerfiles:** Both the frontend (`frontend/Dockerfile`) and backend (`Dockerfile.backend`) applications must be fully containerized.
2. **Tested Locally:** Always build and run your Docker containers locally first to verify the application functions correctly before pushing to the cloud.
   ```bash
   # Example: Testing the backend locally
   docker build -t backend-local -f Dockerfile.backend .
   docker run -p 8080:8080 --env-file .env backend-local
   ```

---

## 1. Architectural Changes Made for Cloud Deployment

Before deploying, minor adjustments were made to the default Dockerfiles to comply with Google Cloud Run's environment and mitigate cross-compilation emulation crashes.

### Backend Changes (`Dockerfile.backend`)
**Reason:** Cloud Run dynamically assigns a port via the `$PORT` environment variable (defaulting to `8080`). Hardcoding `8000` causes deployment failures.
- Swapped `EXPOSE 8000` to `EXPOSE 8080`.
- Updated the startup command to inject the dynamic port:
  `CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]`

### Frontend Changes (`frontend/Dockerfile`)
**Reason:** Building Next.js applications for `amd64` on an `arm64` (Apple Silicon) Mac uses QEMU emulation. Next.js's SWC compiler is highly resource-intensive and reliably causes "Segmentation fault" (SIGSEGV) crashes during `npm run build` on Alpine Linux bases under emulation.
- Switched the base image from `node:20-alpine` to `node:20-slim` (Debian-based is more stable for QEMU).
- Added `ENV NEXT_TELEMETRY_DISABLED=1` to reduce memory overhead and speed up the build.
- **Final Fix:** Shifted the actual build execution to **Google Cloud Build** (detailed below) to natively build on an `amd64` server, completely bypassing local emulation.

---

## 2. GCP Environment Setup

Execute the following commands in your terminal to prepare your GCP project. Set your actual project ID and desired region first.

```bash
export PROJECT_ID="your-project-id" # e.g., agentverse-summoner-xnmn0hrgu9
export REGION="asia-south1"

# 1. Login and set project
gcloud auth login
gcloud config set project $PROJECT_ID

# 2. Enable Required APIs
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

### Create Artifact Registry
Google Cloud Run requires container images to be hosted in GCP Artifact Registry.

```bash
# Create a docker repository
gcloud artifacts repositories create trip-planner-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker repository for Trip Planner"

# Authenticate local Docker client to this registry
gcloud auth configure-docker $REGION-docker.pkg.dev
```

---

## 3. Securing API Keys (Secret Manager)

Never hardcode the Gemini API key. Use Secret Manager and grant Cloud Run permission to read it.

```bash
# 1. Create the secret
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-

# 2. Get your numeric Project Number
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# 3. Grant the Default Compute Service Account access to read the secret
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 4. Deploying the Backend

We can build the backend locally targeting the `linux/amd64` platform, push it, and deploy.

```bash
# 1. Build Backend Image
docker build --platform linux/amd64 -t $REGION-docker.pkg.dev/$PROJECT_ID/trip-planner-repo/backend:latest -f Dockerfile.backend .

# 2. Push to Artifact Registry
docker push $REGION-docker.pkg.dev/$PROJECT_ID/trip-planner-repo/backend:latest

# 3. Deploy to Cloud Run (Injecting the Secret)
gcloud run deploy trip-planner-backend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/trip-planner-repo/backend:latest \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=gemini-api-key:latest"
```

*Note: Upon successful deployment, `gcloud` will output a **Service URL** (e.g., `https://trip-planner-backend-xyz.a.run.app`). Copy this URL for the frontend configuration.*

---

## 5. Deploying the Frontend (Using Cloud Build)

To avoid the local QEMU memory crash, we use Google Cloud Build to natively package the Next.js frontend in the cloud.

```bash
# 1. Submit directory to Cloud Build (Builds and pushes automatically)
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/trip-planner-repo/frontend:latest \
  ./frontend
```

Once Cloud Build succeeds, deploy the frontend to Cloud Run. Make sure to replace `<BACKEND_SERVICE_URL>` with the URL generated in Step 4.

```bash
# 2. Deploy Frontend to Cloud Run (Injecting the Backend URL)
gcloud run deploy trip-planner-frontend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/trip-planner-repo/frontend:latest \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="BACKEND_URL=<BACKEND_SERVICE_URL>"
```

---

## 6. Accessing the Application

The final frontend deployment command will yield a public URL. Click it to access the live AI Trip Planner in your browser. 

Because the `BACKEND_URL` environment variable was passed dynamically, the Next.js API Proxy (`frontend/src/app/api/plan/route.js`) is correctly wired to securely forward all user prompts to your private backend service.

### Updating Environment Variables
If your Backend URL ever changes, you **do not** need to rebuild the frontend container. Simply update the environment variable on the existing service:

```bash
gcloud run services update trip-planner-frontend \
  --region $REGION \
  --update-env-vars="BACKEND_URL=<NEW_BACKEND_URL>"
```