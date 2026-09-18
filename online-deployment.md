# Online Deployment Guide: AI Website Visibility & Operations Agent Loop

This guide outlines architectural patterns, containerization, serverless deployment, scheduled monitoring, and CI/CD pipelines to deploy the Visibility Agent Loop online.

---

## 1. Deployment Architecture Options

Depending on your use case, the agent loop can be deployed in three primary modes:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Deployment Models                               │
├───────────────────┬────────────────────────────┬───────────────────────┤
│ Model             │ Target Infrastructure      │ Best For              │
├───────────────────┼────────────────────────────┼───────────────────────┤
│ 1. REST API       │ Google Cloud Run / Docker  │ On-demand audits via  │
│                   │ AWS App Runner / Fly.io    │ API, CMS triggers     │
├───────────────────┼────────────────────────────┼───────────────────────┤
│ 2. Scheduled Cron │ Cloud Scheduler + Cloud Run│ Daily/weekly tracking │
│    Monitor        │ or GitHub Actions Cron     │ & Slack/email alerts  │
├───────────────────┼────────────────────────────┼───────────────────────┤
│ 3. CI/CD Gate     │ GitHub Actions / GitLab CI │ Preventing SEO/AEO/AIO│
│                   │ Pull Request workflows     │ regressions on deploy │
└───────────────────┴────────────────────────────┴───────────────────────┘
```

---

## 2. Containerization (Docker)

Create a production-ready `Dockerfile` in the project root:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY samples/ ./samples/

# Expose container port
EXPOSE 8080

# Default command (FastAPI or CLI entrypoint)
CMD ["python3", "-m", "src.main", "--demo"]
```

Build and test locally:
```bash
# Build image
docker build -t visibility-agent-loop:latest .

# Run test loop inside container
docker run --rm visibility-agent-loop:latest python3 -m src.main --demo
```

---

## 3. Web Service / REST API (FastAPI)

To run the pipeline as an online microservice, you can wrap the pipeline in a lightweight FastAPI application (`src/api.py`):

```python
# src/api.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any

from src.orchestrator.pipeline import VisibilityPipeline

app = FastAPI(
    title="AI Website Visibility Agent API",
    description="Multi-agent pipeline evaluating SEO, AEO, GEO, and AIO visibility.",
    version="1.0.0"
)

pipeline = VisibilityPipeline()

class AuditRequest(BaseModel):
    url: HttpUrl
    perform_loopback: bool = True

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "visibility-agent-loop"}

@app.post("/api/v1/audit")
def audit_website(req: AuditRequest):
    try:
        target_url = str(req.url)
        result = pipeline.run_loop(
            target=target_url,
            perform_loopback=req.perform_loopback
        )
        return {
            "target": result.target,
            "executed_at": result.executed_at,
            "scores": result.initial_audit.scores.model_dump(),
            "findings_count": len(result.initial_audit.findings),
            "critical_issues": [
                f.model_dump() for f in result.initial_audit.get_findings_by_severity("critical")
            ],
            "recommendations": [
                r.model_dump() for r in result.action_plan.recommendations
            ],
            "artifacts": [
                {
                    "name": a.name,
                    "file_path": a.file_path,
                    "artifact_type": a.artifact_type,
                    "content": a.content
                }
                for a in result.operation_result.artifacts
            ],
            "score_delta": result.score_delta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Add `uvicorn` and `fastapi` to your environment:
```bash
pip install fastapi uvicorn
uvicorn src.api:app --host 0.0.0.0 --port 8080
```

---

## 4. Deploying to Google Cloud Run (Serverless)

Google Cloud Run provides automatic scaling (down to zero when idle), managed HTTPS, and native IAM integration.

### Step-by-Step Deployment:

1. **Authenticate and set default project:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```

2. **Enable required Google Cloud APIs:**
   ```bash
   gcloud services enable run.googleapis.com \
                          artifactregistry.googleapis.com \
                          cloudbuild.googleapis.com
   ```

3. **Create an Artifact Registry repository:**
   ```bash
   gcloud artifacts repositories create visibility-apps \
       --repository-format=docker \
       --location=us-central1 \
       --description="Visibility Agent Docker repository"
   ```

4. **Build and submit image using Cloud Build:**
   ```bash
   gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/visibility-apps/agent-loop:v1
   ```

5. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy visibility-agent-service \
       --image=us-central1-docker.pkg.dev/YOUR_GCP_PROJECT_ID/visibility-apps/agent-loop:v1 \
       --region=us-central1 \
       --platform=managed \
       --allow-unauthenticated \
       --memory=1Gi \
       --cpu=1 \
       --timeout=300 \
       --set-env-vars="PORT=8080"
   ```

Once deployed, Cloud Run provides a secure public URL (e.g. `https://visibility-agent-service-xyz.run.app`).

---

## 5. Scheduled Automated Monitoring (Cloud Scheduler + Cloud Run)

To run automated periodic visibility health checks against your production domains:

1. **Create a Cloud Pub/Sub topic or target URL directly:**
   ```bash
   gcloud scheduler jobs create http weekly-visibility-audit \
       --location=us-central1 \
       --schedule="0 9 * * 1" \
       --uri="https://visibility-agent-service-xyz.run.app/api/v1/audit" \
       --http-method=POST \
       --headers="Content-Type=application/json" \
       --message-body='{"url":"https://yourdomain.com", "perform_loopback": false}' \
       --time-zone="America/New_York"
   ```

2. **Alerting & Notifications:**
   - Configure a webhook endpoint in your API to forward reports to Slack, Discord, or Microsoft Teams when `scores.overall < 70`.

---

## 6. Continuous Integration (GitHub Actions CI/CD Gate)

You can prevent SEO and AI search regressions by running the Auditor Agent on every pull request that touches frontend templates or content.

Create `.github/workflows/visibility-gate.yml`:

```yaml
name: Website Visibility & AI Optimization Audit

on:
  pull_request:
    branches: [ main, master ]
  schedule:
    # Run every Monday at 8:00 AM UTC
    - cron: '0 8 * * 1'
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Test Suite
        run: pytest tests/ -v

      - name: Run Visibility Audit Loop
        run: |
          python3 -m src.main --demo --output-dir audit_output

      - name: Upload Audit Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: visibility-audit-reports
          path: audit_output/
```

---

## 7. Secrets & Environment Variables

When deploying online, manage API keys and credentials through secure secret stores:

| Variable | Description | Recommended Provider |
|---|---|---|
| `GEMINI_API_KEY` | Optional Google GenAI API key for generative enrichment | GCP Secret Manager / GitHub Secrets |
| `OPENAI_API_KEY` | Optional OpenAI API key for generative enrichment | GCP Secret Manager / GitHub Secrets |
| `SLACK_WEBHOOK_URL` | Webhook URL for alerting on visibility drops | GCP Secret Manager / Vault |
| `PORT` | Listening port for web container (default: `8080`) | Environment Variable |

In Google Cloud Run, mount secrets directly:
```bash
gcloud run services update visibility-agent-service \
    --region=us-central1 \
    --update-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

---

## 8. Historical Tracking with BigQuery / Cloud Storage

To track visibility trends over time:
1. Export `audit_report.json` to a Google Cloud Storage bucket (`gs://your-visibility-audits/YYYY-MM-DD/`).
2. Stream scores (`timestamp`, `target`, `overall`, `seo`, `aeo`, `geo`, `aio`) into a BigQuery table (`analytics.visibility_history`).
3. Connect Looker Studio or Google Cloud Monitoring to graph visibility trends, AI citation rates, and search performance improvements.
