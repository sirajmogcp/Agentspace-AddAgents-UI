import os
from flask import Flask, jsonify, request, render_template, abort
from util import *

app = Flask(__name__)

# --- API Endpoints ---
@app.route('/api/as-agents', methods=['GET'])
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

@app.route('/api/as-agents/add-agent', methods=['POST'])
def as_agents_add_agent():
    data = request.json
    required_fields = ['project_id', 'app_id', 'display_name', 'description', 'tool_description', 'adk_deployment_id']
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    result = add_agent(
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
    # Get port from environment variable (Cloud Run sets this)
    port = int(os.getenv('PORT', 8080))
    # Run the app
    app.run(host='0.0.0.0', port=port)