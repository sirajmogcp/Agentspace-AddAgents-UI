import requests
import json
import logging
from google.auth import default
from google.auth.transport.requests import Request

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

def create_agent(project_id, app_id, display_name, description, tool_description, adk_deployment_id, auth_id, icon_uri=None):
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