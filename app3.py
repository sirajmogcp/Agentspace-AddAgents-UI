import os
import requests # Still used by get_gcp_project_id
import google.auth
# google.auth.transport.requests is no longer needed by list_discovery_engines
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions # For specifying API endpoint
from google.api_core import exceptions as google_api_exceptions # For more specific error handling
from flask import Flask, render_template
# Vertex AI SDK imports for Reasoning Engines
import vertexai
from vertexai.preview import reasoning_engines

app = Flask(__name__)


# --- Vertex AI Reasoning Engine Listing ---
def get_reasoning_engines_details(project_id: str, location_id: str):
    """
    Lists Vertex AI ReasoningEngines using the Vertex AI SDK.
    """
    if not project_id:
        return None, "Project ID is required to list Reasoning Engines."
    if not location_id:
        return None, "Location ID is required to list Reasoning Engines (e.g., 'us-central1')."

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


# --- Updated Discovery Engine Listing (using client library) ---
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
        # For more information, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
        client_options = (
            ClientOptions(api_endpoint=f"{location_id}-discoveryengine.googleapis.com")
            if location_id != "global"
            else None # Client library handles global endpoint by default
        )

        # Create a client
        # ADC will be used by the client library implicitly
        client = discoveryengine.EngineServiceClient(client_options=client_options)

        # The full resource name of the parent collection
        # e.g. projects/{project}/locations/{location}/collections/{collection}
        parent_collection_path = client.collection_path(
            project=project_id,
            location=location_id,
            collection=collection_id,
        )

        # Make the request
        response = client.list_engines(parent=parent_collection_path)

        engines_list = []
        for engine in response.engines: # Iterate over the Engine objects in the response
            engines_list.append({
                "name": engine.name,
                "displayName": engine.display_name,
                # Convert SolutionType enum to its string name
                "solutionType": discoveryengine.SolutionType(engine.solution_type).name,
            })
        
        return engines_list, None

    except google.auth.exceptions.DefaultCredentialsError:
        return None, "Google Cloud Default Credentials not found. Please run 'gcloud auth application-default login'."
    except google_api_exceptions.PermissionDenied as e:
        return None, f"Permission denied listing Discovery Engines: {e}. Ensure the user/service account has 'Discovery Engine Viewer' role or equivalent permissions."
    except google_api_exceptions.NotFound as e:
        return None, f"Resource not found (e.g., project, location, or collection '{collection_id}'): {e}"
    except google_api_exceptions.GoogleAPIError as e: # Catch other client library API errors
        return None, f"API error listing Discovery Engines: {e}"
    except Exception as e: # Catch any other unexpected errors
        return None, f"An unexpected error occurred while listing Discovery Engines: {e}"


@app.route('/')
def index():
    gcp_project_id, gcp_project_id_error = get_gcp_project_id()
    
    # For Agent Builder Apps
    discovery_engine_location = os.environ.get('DISCOVERY_ENGINE_LOCATION', 'global')


    # For Vertex AI Reasoning Engines
    # Reasoning Engines are typically regional, e.g., "us-central1"
    reasoning_engine_location = os.environ.get('REASONING_ENGINE_LOCATION', 'us-central1')
    reasoning_engines_data = None
    reasoning_engines_error_msg = None
    
    if gcp_project_id:
        reasoning_engines_data, reasoning_engines_error_msg = get_reasoning_engines_details(
            gcp_project_id,
            reasoning_engine_location
        )
    else:
        reasoning_engines_error_msg = "Cannot fetch Reasoning Engines without a GCP Project ID."


    # For Discovery Engines
    discovery_engine_location = os.environ.get('DISCOVERY_ENGINE_LOCATION', discovery_engine_location)
    discovery_engine_collection_id = os.environ.get('DISCOVERY_ENGINE_COLLECTION_ID', 'default_collection')
    
    discovery_engines = None
    discovery_engines_error = None

    if gcp_project_id:
        discovery_engines, discovery_engines_error = list_discovery_engines(
            gcp_project_id,
            discovery_engine_location,
            discovery_engine_collection_id
        )
    else:
        discovery_engines_error = "Cannot fetch Discovery Engines without a GCP Project ID."
        if not discovery_engine_collection_id:
             discovery_engines_error += " Collection ID is also missing."


    return render_template(
        'index.html',
        gcp_project_id=gcp_project_id,
        gcp_project_id_error=gcp_project_id_error,
        discovery_engine_location=discovery_engine_location,
        discovery_engine_collection_id=discovery_engine_collection_id,
        discovery_engines=discovery_engines,
        discovery_engines_error=discovery_engines_error,
        reasoning_engine_location=reasoning_engine_location,
        reasoning_engines=reasoning_engines_data,
        reasoning_engines_error=reasoning_engines_error_msg,
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))