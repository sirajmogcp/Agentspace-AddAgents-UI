import os
import requests
import google.auth
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from google.api_core import exceptions as google_api_exceptions
from flask import Flask, jsonify, request, render_template, abort
import vertexai
from vertexai.preview import reasoning_engines
from as_agent_registry_service import *

app = Flask(__name__)

# --- GCP Project ID Retrieval ---
def get_gcp_project_id():
    """Gets the GCP project ID from metadata server or environment variable."""
    try:
        metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        headers = {"Metadata-Flavor": "Google"}
        response = requests.get(metadata_server_url, headers=headers, timeout=2)
        response.raise_for_status()
        return response.text, None
    except requests.exceptions.RequestException:
        project_id_env = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if project_id_env:
            return project_id_env, None
        else:
            error_message = (
                "Metadata server unavailable and GOOGLE_CLOUD_PROJECT environment variable not set."
            )
            return None, error_message
    except Exception as e:
        return None, f"Unexpected error fetching project ID: {e}"

# --- Vertex AI Reasoning Engine Listing ---
def get_reasoning_engines_details(project_id: str, location_id: str):
    """
    Lists Vertex AI ReasoningEngines using the Vertex AI SDK.
    """
    if not project_id:
        return None, "Project ID is required to list Reasoning Engines."
    if not location_id:
        location_id = os.environ.get('REASONING_ENGINE_LOCATION', 'us-central1')
        #return None, "Location ID is required to list Reasoning Engines (e.g., 'us-central1')."

    try:
        # Initialize Vertex AI SDK for the specific project and location
        vertexai.init(project=project_id, location=location_id)

        # List the reasoning engines
        listed_engines = reasoning_engines.ReasoningEngine.list()
        
        engines_details_list = []
        if listed_engines:
            for engine in listed_engines:
                engines_details_list.append({
                    "name": engine.name,  # Short ID
                    "resource_name": engine.resource_name, # Full path
                    "display_name": engine.display_name,
                    "create_time": engine.create_time.strftime('%Y-%m-%d %H:%M:%S %Z') if engine.create_time else "N/A",
                    "update_time": engine.update_time.strftime('%Y-%m-%d %H:%M:%S %Z') if engine.update_time else "N/A",
                })
        return engines_details_list, None

    except google.auth.exceptions.DefaultCredentialsError:
        return None, "Google Cloud Default Credentials not found. Please run 'gcloud auth application-default login'."
    except google_api_exceptions.PermissionDenied as e:
        return None, f"Permission denied listing Reasoning Engines: {e}. Ensure the user/service account has 'Vertex AI User' role or equivalent permissions for 'aiplatform.reasoningEngines.list'."
    except google_api_exceptions.NotFound as e:
        return None, f"Resource not found for Reasoning Engines (e.g., project or location, or API not enabled/available in region): {e}"
    except google_api_exceptions.GoogleAPIError as e:
        return None, f"API error listing Reasoning Engines: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred while listing Reasoning Engines: {e}"

# --- Discovery Engine Listing ---
def list_discovery_engines(project_id: str, location_id: str, collection_id: str):
    """
    Lists all engines for a given project, location, and collection
    in Google Cloud Discovery Engine using the client library.

    Args:
        project_id: Your Google Cloud project ID.
        location_id: The location ID (e.g., 'global', 'us').
        collection_id: The collection ID (e.g., 'default_collection').

    Returns:
        A tuple containing a list of engine details or None, and an error message or None.
    """
    if not project_id:
        return None, "Project ID is required to list Discovery Engines."
    if not collection_id:
        return None, "Collection ID is required to list Discovery Engines."

    try:
        client_options = (
            ClientOptions(api_endpoint=f"{location_id}-discoveryengine.googleapis.com")
            if location_id != "global"
            else None
        )

        client = discoveryengine.EngineServiceClient(client_options=client_options)

        parent_collection_path = client.collection_path(
            project=project_id,
            location=location_id,
            collection=collection_id,
        )

        response = client.list_engines(parent=parent_collection_path)

        engines_list = []
        for engine in response.engines:
            engine_data = {
                "id": len(engines_list) + 1,  # Generate sequential IDs
                "appId": engine.name.split('/')[-1],  # Extract the last part of the name
                "appName": engine.display_name,
                "appType": discoveryengine.SolutionType(engine.solution_type).name,
                "details": f"Discovery Engine of type {discoveryengine.SolutionType(engine.solution_type).name}",
                "project_id": project_id,  # Add the GCP project ID
                "agents": []  # Changed from categories to agents
            }
            engines_list.append(engine_data)
            print(f"Added engine with project_id: {engine_data['project_id']}")  # Debug print
        
        return engines_list, None

    except google.auth.exceptions.DefaultCredentialsError:
        return None, "Google Cloud Default Credentials not found. Please run 'gcloud auth application-default login'."
    except google_api_exceptions.PermissionDenied as e:
        return None, f"Permission denied listing Discovery Engines: {e}. Ensure the user/service account has 'Discovery Engine Viewer' role or equivalent permissions."
    except google_api_exceptions.NotFound as e:
        return None, f"Resource not found (e.g., project, location, or collection '{collection_id}'): {e}"
    except google_api_exceptions.GoogleAPIError as e:
        return None, f"API error listing Discovery Engines: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred while listing Discovery Engines: {e}"

# --- Helper Functions ---
def find_agentspace_app(app_db_id):
    gcp_project_id, _ = get_gcp_project_id()
    discovery_engine_location = os.environ.get('DISCOVERY_ENGINE_LOCATION', 'global')
    discovery_engine_collection_id = os.environ.get('DISCOVERY_ENGINE_COLLECTION_ID', 'default_collection')
    
    engines_list, _ = list_discovery_engines(gcp_project_id, discovery_engine_location, discovery_engine_collection_id)
    if not engines_list:
        abort(404, description=f"Agentspace App with internal ID {app_db_id} not found.")
    
    agentspace_app = next((app_item for app_item in engines_list if app_item["id"] == app_db_id), None)
    if not agentspace_app:
        abort(404, description=f"Agentspace App with internal ID {app_db_id} not found.")
    return agentspace_app

def find_agent_in_app(agentspace_app, agent_id):  # Changed from find_category_in_app
    agent = next((agt for agt in agentspace_app["agents"] if agt["id"] == agent_id), None)  # Changed from categories to agents
    if not agent:
        abort(404, description=f"Agent with ID {agent_id} not found in app {agentspace_app['appName']}.")  # Changed from Category to Agent
    return agent

# --- API Endpoints ---
@app.route('/api/agentspace-apps', methods=['GET'])
def get_agentspace_apps():
    gcp_project_id, gcp_project_id_error = get_gcp_project_id()
    if gcp_project_id_error:
        return jsonify({"error": gcp_project_id_error}), 500

    discovery_engine_location = os.environ.get('DISCOVERY_ENGINE_LOCATION', 'global')
    discovery_engine_collection_id = os.environ.get('DISCOVERY_ENGINE_COLLECTION_ID', 'default_collection')
    
    engines_list, error = list_discovery_engines(gcp_project_id, discovery_engine_location, discovery_engine_collection_id)
    if error:
        return jsonify({"error": error}), 500
    
    # Add GCP project ID to each engine in the list
    for engine in engines_list:
        engine['project_id'] = gcp_project_id
    
    return jsonify(engines_list)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-as')
def test_as_page():
    return render_template('test_as.html')

@app.route('/api/as-agents/list-agents')
def as_agents_list_agents():
    project_id = request.args.get('project_id')
    app_id = request.args.get('app_id')
    
    if not project_id or not app_id:
        return jsonify({"error": "Project ID and App ID are required"}), 400
    
    result = list_agents(project_id, app_id)
    return jsonify(result)

@app.route('/api/as-agents/create-agent', methods=['POST'])
def as_agents_create_agent():
    data = request.json
    required_fields = ['project_id', 'app_id', 'display_name', 'description', 'tool_description', 'adk_deployment_id']
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    result = create_agent(
        project_id=data['project_id'],
        app_id=data['app_id'],
        display_name=data['display_name'],
        description=data['description'],
        tool_description=data['tool_description'],
        adk_deployment_id=data['adk_deployment_id'],
        auth_id=data.get('auth_id'),
        icon_uri=data.get('icon_uri')
    )
    return jsonify(result)

@app.route('/api/as-agents/get-agent')
def as_agents_get_agent():
    project_id = request.args.get('project_id')
    app_id = request.args.get('app_id')
    agent_id = request.args.get('agent_id')
    
    if not all([project_id, app_id, agent_id]):
        return jsonify({"error": "Project ID, App ID, and Agent ID are required"}), 400
    
    result = get_agent(project_id, app_id, agent_id)
    return jsonify(result)

@app.route('/api/as-agents/update-agent', methods=['PUT'])
def as_agents_update_agent():
    data = request.json
    required_fields = ['project_id', 'app_id', 'agent_id']
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    result = update_agent(
        project_id=data['project_id'],
        app_id=data['app_id'],
        agent_id=data['agent_id'],
        display_name=data.get('display_name'),
        description=data.get('description'),
        tool_description=data.get('tool_description'),
        adk_deployment_id=data.get('adk_deployment_id'),
        auth_id=data.get('auth_id'),
        icon_uri=data.get('icon_uri')
    )
    return jsonify(result)

@app.route('/api/as-agents/delete-agent', methods=['DELETE'])
def as_agents_delete_agent():
    project_id = request.args.get('project_id')
    app_id = request.args.get('app_id')
    agent_id = request.args.get('agent_id')
    
    if not all([project_id, app_id, agent_id]):
        return jsonify({"error": "Project ID, App ID, and Agent ID are required"}), 400
    
    result = delete_agent(project_id, app_id, agent_id)
    return jsonify(result)

@app.route('/api/as-agents/get-agent-by-name')
def as_agents_get_agent_by_name():
    project_id = request.args.get('project_id')
    app_id = request.args.get('app_id')
    display_name = request.args.get('display_name')
    
    if not all([project_id, app_id, display_name]):
        return jsonify({"error": "Project ID, App ID, and Display Name are required"}), 400
    
    result = get_agent_by_display_name(project_id, app_id, display_name)
    return jsonify(result)

@app.route('/api/as-agents/list-reasoning-engines')
def as_agents_list_reasoning_engines():
    project_id = request.args.get('project_id')
    location_id = request.args.get('location_id')
    
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400
    
    engines_list, error = get_reasoning_engines_details(project_id, location_id)
    if error:
        return jsonify({"error": error}), 500
    
    return jsonify(engines_list)

if __name__ == '__main__':
    app.run(debug=True)