import requests
import os
import vertexai
from vertexai.preview import reasoning_engines
import google.auth.exceptions
from google.api_core import exceptions as google_api_exceptions
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

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
