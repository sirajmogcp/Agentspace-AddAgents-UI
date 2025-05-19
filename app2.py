from flask import Flask, jsonify, request, render_template, abort

app = Flask(__name__)

# In-memory data store for Agentspace Apps
agentspace_apps_db = [
    {
        "id": 1, # Internal DB ID
        "appId": "AS-PRO-001", # New "App ID" field (custom identifier)
        "appName": "AlphaSuite Editor", # Was "name", now "appName"
        "appType": "Productivity", # New field
        "details": "Next-gen collaborative content creation tool.",
        "categories": []
    },
    {
        "id": 2,
        "appId": "AS-NET-SECURE",
        "appName": "ConnectSphere VPN",
        "appType": "Networking Security",
        "details": "Secure and private internet access client.",
        "categories": []
    },
    {
        "id": 3,
        "appId": "AS-AI-ASSIST",
        "appName": "CogniLink Assistant",
        "appType": "AI Copilot",
        "details": "Intelligent assistant for daily tasks and queries.",
        "categories": []
    },
    {
        "id": 4,
        "appId": "AS-TASK-MASTER",
        "appName": "TaskFlow Organizer",
        "appType": "Task Management",
        "details": "Streamline your workflows and boost productivity.",
        "categories": []
    }
]
next_category_id = 1 # Simple ID generator for categories

# --- Helper Functions ---
def find_agentspace_app(app_db_id): # Renamed from find_product
    agentspace_app = next((app_item for app_item in agentspace_apps_db if app_item["id"] == app_db_id), None)
    if not agentspace_app:
        abort(404, description=f"Agentspace App with internal ID {app_db_id} not found.")
    return agentspace_app

def find_category_in_app(agentspace_app, category_id): # Renamed parameter
    category = next((cat for cat in agentspace_app["categories"] if cat["id"] == category_id), None)
    if not category:
        abort(404, description=f"Category with ID {category_id} not found in app {agentspace_app['appName']}.")
    return category

# --- API Endpoints ---

# 1. Get all Agentspace Apps
@app.route('/api/agentspace-apps', methods=['GET']) # Updated route
def get_agentspace_apps():
    return jsonify(agentspace_apps_db)

# 2. Add a category to an Agentspace App
@app.route('/api/agentspace-apps/<int:app_db_id>/categories', methods=['POST']) # Updated route
def add_category_to_app(app_db_id): # Renamed parameter
    global next_category_id
    agentspace_app = find_agentspace_app(app_db_id)
    
    if not request.json or not 'name' in request.json:
        abort(400, description="Missing 'name' in request body for category.")
    
    category_name = request.json['name']
    category_details = request.json.get('details', '')

    new_category = {
        "id": next_category_id,
        "name": category_name,
        "details": category_details
    }
    agentspace_app["categories"].append(new_category)
    next_category_id += 1
    return jsonify({"message": "Category added successfully", "category": new_category}), 201

# 3. Show categories of an Agentspace App
@app.route('/api/agentspace-apps/<int:app_db_id>/categories', methods=['GET']) # Updated route
def get_app_categories(app_db_id): # Renamed parameter
    agentspace_app = find_agentspace_app(app_db_id)
    return jsonify(agentspace_app["categories"])

# 4. Delete a category from an Agentspace App
@app.route('/api/agentspace-apps/<int:app_db_id>/categories/<int:category_id>', methods=['DELETE']) # Updated route
def delete_category_from_app(app_db_id, category_id): # Renamed parameter
    agentspace_app = find_agentspace_app(app_db_id)
    category_to_delete = find_category_in_app(agentspace_app, category_id)
    
    agentspace_app["categories"] = [cat for cat in agentspace_app["categories"] if cat["id"] != category_id]
    return jsonify({"message": f"Category with ID {category_id} deleted successfully from app {agentspace_app['appName']}."})

# --- Frontend Route ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)