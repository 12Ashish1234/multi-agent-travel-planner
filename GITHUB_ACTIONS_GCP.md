# Automating Docker Pushes to GCP Artifact Registry via GitHub Actions

This guide explains how to automatically build and push Docker images to Google Cloud Platform (GCP) Artifact Registry using GitHub Actions. 

We use **Workload Identity Federation (WIF)** to authenticate GitHub Actions to GCP securely. This is the recommended best practice as it avoids storing long-lived, sensitive JSON Service Account keys in GitHub Secrets.

---

## Step 1: Set up Workload Identity Federation in GCP

Run these commands in your local terminal where `gcloud` is authenticated. Replace `YOUR_GITHUB_USERNAME/YOUR_REPO_NAME` with your actual GitHub repository details (e.g., `ashishd/Trip_Planner_Agent`).

```bash
# 1. Set your environment variables
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export GITHUB_REPO="YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"

# 2. Enable the IAM Credentials API (Required for Workload Identity)
gcloud services enable iamcredentials.googleapis.com

# 3. Create a dedicated Service Account for GitHub Actions
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Deployment SA"

export SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# 4. Grant the Service Account permission to push to your Artifact Registry
# (Assuming your repository is named 'trip-planner-repo' and in 'asia-south1')
gcloud artifacts repositories add-iam-policy-binding trip-planner-repo \
  --location=asia-south1 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# 5. Create a Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 6. Create an OIDC Provider in that pool for GitHub
# Note: The attribute-condition securely restricts access to ONLY your specific repository
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${GITHUB_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 7. Bind the Service Account to the GitHub repository via the Identity Pool
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

# 8. Output the Workload Identity Provider resource name (You will need this for GitHub Secrets)
gcloud iam workload-identity-pools providers describe github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

---

## Step 2: Add GitHub Secrets

Go to your repository on GitHub -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following three secrets:

1. `GCP_PROJECT_ID`: Your actual Google Cloud Project ID (e.g., `agentverse-summoner-xnmn0hrgu9`). *Make sure this is the actual ID, not the literal string "GCP_PROJECT_ID"!*
2. `GCP_SERVICE_ACCOUNT`: The email of the service account you created in Step 1 (e.g., `github-actions-sa@<your-project-id>.iam.gserviceaccount.com`).
3. `GCP_WORKLOAD_IDENTITY_PROVIDER`: The exact string output from Step 1, Command 8. It will look similar to:
   `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

---

## Step 3: Create the GitHub Actions Workflow

Create a file in your repository at `.github/workflows/gcp-push.yml` to define your pipeline. 

*Note: Docker enforces strict lowercase repository names, so we use a bash trick (`tr '[:upper:]' '[:lower:]'`) to ensure the `PROJECT_ID` is safely lowercased before building the image path.*

```yaml
name: Build and Push to GCP

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: asia-south1
  REPO_NAME: trip-planner-repo

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    # These permissions are required for Workload Identity Federation
    permissions:
      contents: 'read'
      id-token: 'write'

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      - name: Build and Push Backend Image
        run: |
          PROJECT_ID_LOWER=$(echo "${PROJECT_ID}" | tr '[:upper:]' '[:lower:]')
          IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID_LOWER}/${REPO_NAME}/backend:latest"
          docker build -t $IMAGE_PATH -f Dockerfile.backend .
          docker push $IMAGE_PATH

      - name: Build and Push Frontend Image
        run: |
          PROJECT_ID_LOWER=$(echo "${PROJECT_ID}" | tr '[:upper:]' '[:lower:]')
          IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID_LOWER}/${REPO_NAME}/frontend:latest"
          docker build -t $IMAGE_PATH -f frontend/Dockerfile ./frontend
          docker push $IMAGE_PATH
```