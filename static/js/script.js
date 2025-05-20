// Initialize modals
const addAgentModal = new bootstrap.Modal(document.getElementById('addAgentModal'));
const showAgentsModal = new bootstrap.Modal(document.getElementById('showAgentsModal'));

// Load apps on page load
document.addEventListener('DOMContentLoaded', loadApps);

async function loadApps() {
    try {
        const response = await fetch('/api/as-agents');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Check if data is an array
        if (!Array.isArray(data)) {
            console.error('Expected array but got:', data);
            throw new Error('Invalid response format: expected array of apps');
        }
        
        displayApps(data);
    } catch (error) {
        console.error('Error loading apps:', error);
        const appsList = document.getElementById('appsList');
        appsList.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <h6>Error loading apps</h6>
                    <p>${error.message}</p>
                    <small>Please check the console for more details.</small>
                </div>
            </div>
        `;
    }
}

function displayApps(apps) {
    const appsList = document.getElementById('appsList');
    appsList.innerHTML = apps.map(app => `
        <div class="col-md-6 col-lg-4">
            <div class="card app-card">
                <div class="card-body">
                    <h5 class="card-title">${app.appName}</h5>
                    <p class="card-text">ID: ${app.appId}</p>
                    <p class="card-text"><strong>Project ID:</strong> ${app.project_id}</p>
            
                    <button class="btn btn-primary me-2" onclick="showAddAgentModal(${app.id}, '${app.project_id}', '${app.appId}')">
                        Add Agent
                    </button>
                    <button class="btn btn-info" onclick="showAgents(${app.id}, '${app.project_id}', '${app.appId}')">
                        Show Agents
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function showAddAgentModal(appId, projectId, appId) {
    // Set hidden fields for form submission
    document.getElementById('addAgentProjectId').value = projectId;
    document.getElementById('addAgentAppId').value = appId;
    
    // Set display fields
    document.getElementById('displayProjectId').value = projectId;
    document.getElementById('displayAppId').value = appId;
    
    // Reset other form fields
    document.getElementById('displayName').value = '';
    document.getElementById('description').value = '';
    document.getElementById('toolDescription').value = '';
    document.getElementById('authId').value = '';
    document.getElementById('iconUri').value = '';
    
    // Load reasoning engines for the dropdown
    loadReasoningEngines(projectId);
    
    addAgentModal.show();
}

async function loadReasoningEngines(projectId) {
    const loadingDiv = document.getElementById('adkLoading');
    const dropdown = document.getElementById('adkDeploymentId');
    try {
        // Show loading indicator
        if (loadingDiv) loadingDiv.style.display = 'inline-block';
        // Optionally, disable the dropdown while loading
        if (dropdown) dropdown.disabled = true;

        const response = await fetch(`/api/as-agents/list-reasoning-engines?project_id=${projectId}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const engines = await response.json();
        dropdown.innerHTML = '<option value="">Select ADK Deployment ID</option>';

        if (!Array.isArray(engines)) {
            console.error('Expected array but got:', engines);
            throw new Error('Invalid response format: expected array of engines');
        }

        engines.forEach(engine => {
            const option = document.createElement('option');
            option.value = engine.name;
            option.textContent = `${engine.display_name} (${engine.name})`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading reasoning engines:', error);
        dropdown.innerHTML = '<option value="">Error loading engines</option>';
        alert('Error loading reasoning engines. Please try again.');
    } finally {
        // Hide loading indicator and enable dropdown
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (dropdown) dropdown.disabled = false;
    }
}

function showAgents(appId, projectId, appId) {
    console.log('Showing agents for:', { appId, projectId, appId }); // Debug log
    document.getElementById('showAgentsProjectIdDisplay').textContent = projectId;
    document.getElementById('showAgentsAppIdDisplay').textContent = appId;
    loadAgents(appId);
    showAgentsModal.show();
}

async function loadAgents(appId) {
    try {
        const projectId = document.getElementById('showAgentsProjectIdDisplay').textContent;
        const appId = document.getElementById('showAgentsAppIdDisplay').textContent;
        
        console.log('Loading agents for:', { projectId, appId }); // Debug log
        
        const response = await fetch(`/api/as-agents/list-agents?project_id=${projectId}&app_id=${appId}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received agents data:', data); // Debug log
        
        // Check if data has agents array
        if (data && data.agents) {
            displayAgents(data.agents);
        } else {
            displayAgents([]);
        }
    } catch (error) {
        console.error('Error loading agents:', error);
        const agentsList = document.getElementById('agentsList');
        agentsList.innerHTML = `<div class="alert alert-danger">
            <h6>Error loading agents</h6>
            <p>${error.message}</p>
            <small>Please check the console for more details.</small>
        </div>`;
    }
}

function displayAgents(agents) {
    const agentsList = document.getElementById('agentsList');
    
    if (!agents || agents.length === 0) {
        agentsList.innerHTML = '<div class="alert alert-info">No agents found for this app.</div>';
        return;
    }
    
    try {
        console.log('Displaying agents:', agents); // Debug log
        agentsList.innerHTML = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Display Name</th>
                            <th>Agent ID</th>
                            <th>ADK Deployment ID</th>
                            <th>Description</th>
                            <th>Tool Description</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${agents.map(agent => {
                            console.log('Processing agent:', agent); // Debug log for each agent
                            const adkDeploymentId = agent.adkAgentDefinition?.provisionedReasoningEngine?.reasoningEngine || 'Not specified';
                            const toolDescription = agent.adkAgentDefinition?.toolSettings?.toolDescription || 'No tool description';
                            const agentId = agent.name.split('/').pop(); // Extract the last part of the name as agent ID
                            return `
                            <tr>
                                <td>${agent.displayName || 'Unnamed Agent'}</td>
                                <td>${agent.name || 'Not specified'}</td>
                                <td>${adkDeploymentId}</td>
                                <td>${agent.description || 'No description'}</td>
                                <td>${toolDescription}</td>
                                <td>
                                    <button class="btn btn-danger btn-sm" onclick="deleteAgent('${agentId}')">
                                        <i class="bi bi-trash"></i> Delete
                                    </button>
                                </td>
                            </tr>
                        `}).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error displaying agents:', error);
        console.error('Agents data:', agents); // Log the data that caused the error
        agentsList.innerHTML = `<div class="alert alert-danger">
            <h6>Error displaying agents</h6>
            <p>${error.message}</p>
            <small>Please check the console for more details.</small>
        </div>`;
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) {
        return;
    }
    
    try {
        const projectId = document.getElementById('showAgentsProjectIdDisplay').textContent;
        const appId = document.getElementById('showAgentsAppIdDisplay').textContent;
        
        const response = await fetch(`/api/as-agents/delete-agent?project_id=${projectId}&app_id=${appId}&agent_id=${agentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        // Reload the agents list
        loadAgents(appId);
    } catch (error) {
        console.error('Error deleting agent:', error);
        alert('Error deleting agent: ' + error.message);
    }
}

// Save Agent
document.getElementById('saveAgentBtn').addEventListener('click', async () => {
    const form = document.getElementById('addAgentForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const projectId = document.getElementById('addAgentProjectId').value;
    const appId = document.getElementById('addAgentAppId').value;
    const data = {
        project_id: projectId,
        app_id: appId,
        display_name: document.getElementById('displayName').value,
        description: document.getElementById('description').value,
        tool_description: document.getElementById('toolDescription').value,
        adk_deployment_id: document.getElementById('adkDeploymentId').value,
        auth_id: document.getElementById('authId').value || null,
        icon_uri: document.getElementById('iconUri').value || null
    };

    try {
        const response = await fetch('/api/as-agents/add-agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (response.ok) {
            addAgentModal.hide();
            alert('Agent added successfully!');
            // Refresh the agents list if the modal is open
            const showAgentsModal = document.getElementById('showAgentsModal');
            if (showAgentsModal.classList.contains('show')) {
                loadAgents(appId);
            }
        } else {
            alert(`Error: ${result.error || 'Failed to add agent'}`);
        }
    } catch (error) {
        console.error('Error adding agent:', error);
        alert('Error adding agent. Please try again.');
    }
});
