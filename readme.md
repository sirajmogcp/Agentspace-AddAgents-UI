# AgentSpace Add Agents UI

A Flask application for managing AgentSpace agents, built with Google Cloud Discovery Engine and Vertex AI.

## Prerequisites

- Python 3.8 or higher
- Google Cloud SDK
- A Google Cloud Project with the following APIs enabled:
  - Discovery Engine API
  - Vertex AI API
  - Cloud Run API

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Agentspace-AddAgents-UI
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.yaml.template env.yaml
   ```
   Edit `env.yaml` with your values:
   ```yaml
   GOOGLE_CLOUD_PROJECT: "your-project-id"
   DISCOVERY_ENGINE_LOCATION: "global"
   DISCOVERY_ENGINE_COLLECTION_ID: "default_collection"
   REASONING_ENGINE_LOCATION: "us-central1"
   PORT: "8080"
   ```

5. **Set up Google Cloud authentication**
   ```bash
   gcloud auth application-default login
   ```

6. **Run the application locally**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:8080`

## Deploying to Cloud Run

1. **Enable required APIs**
   ```bash
   gcloud services enable discoveryengine.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable run.googleapis.com
   ```

2. **Create a service account (if not exists)**
   ```bash
   gcloud iam service-accounts create agentspace-service \
     --display-name="AgentSpace Service Account"
   ```

3. **Grant necessary permissions**
   ```bash
   gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
     --member="serviceAccount:agentspace-service@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
     --role="roles/discoveryengine.viewer"
   
   gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
     --member="serviceAccount:agentspace-service@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

4. **Build and deploy to Cloud Run**
   ```bash
   gcloud run deploy agentspace-agents \
     --source . \
     --region us-central1 \
     --platform managed \
     --service-account agentspace-service@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
     --allow-unauthenticated \
     --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,DISCOVERY_ENGINE_LOCATION=global,DISCOVERY_ENGINE_COLLECTION_ID=default_collection,REASONING_ENGINE_LOCATION=us-central1"
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GOOGLE_CLOUD_PROJECT | Your Google Cloud Project ID | - |
| DISCOVERY_ENGINE_LOCATION | Location for Discovery Engine | global |
| DISCOVERY_ENGINE_COLLECTION_ID | Collection ID for Discovery Engine | default_collection |
| REASONING_ENGINE_LOCATION | Location for Reasoning Engines | us-central1 |
| PORT | Port for the Flask application | 8080 |

## API Endpoints

- `GET /api/as-agents` - List all AgentSpace apps
- `GET /api/as-agents/list-agents` - List agents for a specific app
- `POST /api/as-agents/add-agent` - Add a new agent
- `GET /api/as-agents/get-agent` - Get agent details
- `PUT /api/as-agents/update-agent` - Update an existing agent
- `DELETE /api/as-agents/delete-agent` - Delete an agent
- `GET /api/as-agents/get-agent-by-name` - Get agent by display name
- `GET /api/as-agents/list-reasoning-engines` - List available reasoning engines

## Troubleshooting

1. **401 Unauthorized Errors**
   - Ensure service account has correct permissions
   - Verify authentication is properly set up
   - Check if APIs are enabled

2. **404 Not Found Errors**
   - Verify project ID is correct
   - Check if Discovery Engine and Vertex AI resources exist
   - Ensure correct location is specified

3. **500 Internal Server Errors**
   - Check Cloud Run logs
   - Verify environment variables are set correctly
   - Ensure all required APIs are enabled

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 