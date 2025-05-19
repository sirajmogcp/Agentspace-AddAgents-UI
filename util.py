import requests

def get_gcp_project_id():
    """Gets the GCP project ID from the metadata server."""
    try:
        # For most GCP services, the metadata server is available.
        metadata_server_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        headers = {"Metadata-Flavor": "Google"}
        response = requests.get(metadata_server_url, headers=headers, timeout=5) # Added a timeout
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        # This might happen if not running on GCP or if metadata server is inaccessible.
        print(f"Error fetching project ID from metadata server: {e}")
        # Fallback or further handling can be added here.
        # For example, you might check for an environment variable as a fallback.
        # import os
        # project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        # if project_id:
        #     return project_id
        return None

if __name__ == '__main__':
     get_gcp_project_id()
    