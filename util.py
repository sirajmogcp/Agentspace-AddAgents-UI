import requests
import os
import vertexai
import json
import logging
from vertexai.preview import reasoning_engines
import google.auth.exceptions
from google.api_core import exceptions as google_api_exceptions
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine
from google.auth import default
from google.auth.transport.requests import Request

# --- GCP Project ID Retrieval (same as before) ---
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




def get_credentials():
    """
    Get Google Cloud credentials using Application Default Credentials.
    
    Returns:
        tuple: (credentials, project_id)
    """
    try:
        credentials, project = default()
        if credentials.expired:
            credentials.refresh(Request())
        return credentials, project
    except Exception as e:
        logging.error(f"Error getting credentials: {str(e)}")
        raise

def _check_required_params(params, required):
    missing = [param for param in required if not params.get(param)]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

def add_agent(project_id, app_id, display_name, description, tool_description, adk_deployment_id, auth_id, icon_uri=None):
    """
    Creates a new agent in the Agent Registry.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.
        display_name (str): Display name of the agent.
        description (str): Description of the agent.
        tool_description (str): Tool description for the agent.
        adk_deployment_id (str): Reasoning Engine ID.
        auth_id (str): Authorization ID.
        icon_uri (str, optional): Icon URI for the agent. Defaults to None.

    Returns:
        dict: A dictionary containing the status code, stdout, and stderr of the curl command.
    """
    _check_required_params(locals(), ["project_id", "app_id", "display_name", "description", "tool_description", "adk_deployment_id"])
    
    try:
        credentials, _ = get_credentials()
        access_token = credentials.token
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return {"error": f"Authentication failed: {str(e)}"}

    # Construct the URL
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"

    # Prepare the request body
    data = {
        "displayName": display_name,
        "description": description,
        "adk_agent_definition": {
            "tool_settings": {
                "tool_description": tool_description
            },
            "provisioned_reasoning_engine": {
                "reasoning_engine": f"projects/{project_id}/locations/global/reasoningEngines/{adk_deployment_id}"
            },
            "authorizations": [f"projects/{project_id}/locations/global/authorizations/{auth_id}"] if auth_id else [],
        }
    }

    if icon_uri:
        data["icon"] = {"uri": icon_uri}

    # Make the HTTP request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return {"status_code": response.status_code, "data": response.json()}
    except requests.exceptions.RequestException as e:
        logging.error(f"Create Agent Error: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "status_code": response.status_code if 'response' in locals() else None}

def list_agents(project_id, app_id):
    """
    Lists agents in the Agent Registry for a given project and app.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.

    Returns:
        dict: A dictionary containing a list of agents or an error message.
    """
    try:
        credentials, _ = get_credentials()
        access_token = credentials.token
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return {"error": f"Authentication failed: {str(e)}"}

    # Construct the URL
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"

    # Make the HTTP request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {"agents": data.get("agents", [])}
    except requests.exceptions.RequestException as e:
        logging.error(f"List Agents Error: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "status_code": response.status_code if 'response' in locals() else None}

def get_agent(project_id, app_id, agent_id):
    """
    Retrieves details for a specific agent from the Agent Registry.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.
        agent_id (str): ID of the agent to retrieve.

    Returns:
        dict: A dictionary containing the agent details or an error message.
    """
    try:
        credentials, _ = get_credentials()
        access_token = credentials.token
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return {"error": f"Authentication failed: {str(e)}"}

    # Construct the URL
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"

    # Make the HTTP request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return {"agent_details": response.json()}
    except requests.exceptions.RequestException as e:
        logging.error(f"Get Agent Error: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "status_code": response.status_code if 'response' in locals() else None}

def update_agent(project_id, app_id, agent_id, display_name, description, tool_description, adk_deployment_id, auth_id, icon_uri=None):
    """
    Updates an existing agent in the Agent Registry.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.
        agent_id (str): ID of the agent to update.
        display_name (str): New display name for the agent (leave blank to keep current).
        description (str): New description for the agent (leave blank to keep current).
        tool_description (str): New tool description (leave blank to keep current).
        adk_deployment_id (str): New Reasoning Engine ID (leave blank to keep current).
        auth_id (str, optional): New Authorization ID (leave blank to keep current). Defaults to None.
        icon_uri (str, optional): New icon URI (leave blank to keep current). Defaults to None.
    
    Returns:    
        dict: A dictionary containing the status code, stdout, stderr, and optionally the updated agent details or an error message.
    """

    # First get the agent
    get_result = get_agent(project_id, app_id, agent_id)
    if "agent_details" not in get_result:
        return {"error": f"Could not retrieve agent details: {get_result.get('error', '')}"}
    
    existing_agent = get_result["agent_details"]

    # Prepare updated data. Use existing values as defaults.
    updated_data = {
        "displayName": display_name or existing_agent.get("displayName", ""),
        "description": description or existing_agent.get("description", ""),
    }

    #Handle adk_agent_definition.
    existing_adk = existing_agent.get("adkAgentDefinition", {})
    updated_adk = {}

    #Tool settings
    existing_tool = existing_adk.get("toolSettings", {})
    updated_adk["tool_settings"] = {
        "tool_description": tool_description or existing_tool.get("toolDescription", "")
    }

    #Reasoning engine
    existing_reasoning = existing_adk.get("provisionedReasoningEngine", {}).get("reasoningEngine","")
    updated_adk["provisionedReasoningEngine"] = {
        "reasoning_engine": adk_deployment_id or existing_reasoning
    }

    #Authorizations
    existing_auths = existing_adk.get("authorizations", [])
    updated_adk["authorizations"] = [auth_id] if auth_id else existing_auths

    existing_icon = existing_agent.get("icon")
    if icon_uri:  # If new icon URI is provided
        updated_data["icon"] = {"uri": icon_uri}
    elif existing_icon:  # If no new URI, retain the existing icon
        updated_data["icon"] = existing_icon

    updated_data["adk_agent_definition"] = updated_adk

    # Construct the URL
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"    

    try:
        credentials, _ = get_credentials()
        access_token = credentials.token
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return {"error": f"Authentication failed: {str(e)}"}

    # Make the HTTP request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        response = requests.patch(url, headers=headers, json=updated_data)
        response.raise_for_status()
        return {"status_code": response.status_code, "updated_agent": response.json()}
    except requests.exceptions.RequestException as e:
        logging.error(f"Update Agent Error: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "status_code": response.status_code if 'response' in locals() else None}

def get_agent_by_display_name(project_id, app_id, display_name):
    """
    Retrieves an agent from the Agent Registry by its display name.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.
        display_name (str): Display name of the agent to retrieve.

    Returns:
        dict: A dictionary containing the agent details or a message indicating the agent was not found.
    """
    _check_required_params(locals(), ["project_id", "app_id", "display_name"])

    list_result = list_agents(project_id, app_id)
    if "error" in list_result:
        return list_result

    agents = list_result.get("agents", [])
    for agent in agents:
        if agent.get("displayName") == display_name:
            return {"agent": agent}

    return {"message": f"Agent with display name '{display_name}' not found."}


def delete_agent(project_id, app_id, agent_id):
    """
    Deletes an agent from the Agent Registry.

    Args:
        project_id (str): Google Cloud Project ID.
        app_id (str): App ID for the Discovery Engine.
        agent_id (str): ID of the agent to delete.

    Returns:
        dict: A dictionary containing the status code, stdout, and stderr of the curl command,
              or an error message.
    """
    _check_required_params(locals(), ["project_id", "app_id", "agent_id"])

    try:
        credentials, _ = get_credentials()
        access_token = credentials.token
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return {"error": f"Authentication failed: {str(e)}"}

    # Construct the URL
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents/{agent_id}"

    # Make the HTTP request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return {"status_code": response.status_code, "message": f"Agent {agent_id} deleted successfully."}
    except requests.exceptions.RequestException as e:
        logging.error(f"Delete Agent Error: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "status_code": response.status_code if 'response' in locals() else None}