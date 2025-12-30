import { app } from '/scripts/app.js';
import { ComfyWidgets } from '/scripts/widgets.js';

// Local storage for last selections
const STORAGE_KEY = 'basify_checkpoint_selections';

function getLastSelection(directoryPath) {
    try {
        const selections = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        return selections[directoryPath] || '';
    } catch {
        return '';
    }
}

function saveLastSelection(directoryPath, checkpoint) {
    try {
        const selections = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        selections[directoryPath] = checkpoint;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selections));
    } catch (e) {
        console.warn('Could not save checkpoint selection:', e);
    }
}

// Function to get checkpoints from a directory via API
async function getCheckpointsFromDirectory(directoryPath) {
    let response = null;
    let data = null;
    
    try {
        response = await fetch('/basify/scan_directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ directory_path: directoryPath })
        });
        
        if (response.ok) {
            data = await response.json();
            const checkpoints = data.checkpoints || [];
            
            // Clean up response objects
            data = null;
            response = null;
            
            return checkpoints;
        }
    } catch (error) {
        console.error('Error fetching checkpoints:', error);
    } finally {
        // Ensure cleanup
        data = null;
        response = null;
    }
    return [];
}

app.registerExtension({
    name: "basify.DirectoryCheckpointScanner",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DirectoryCheckpointScanner") {
            const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                const result = originalOnNodeCreated?.apply(this, arguments);
                
                // Wait for widgets to be created
                setTimeout(async () => {
                    const directoryWidget = this.widgets.find(w => w.name === "directory_path");
                    const checkpointWidget = this.widgets.find(w => w.name === "selected_checkpoint");
                    
                    if (directoryWidget && checkpointWidget) {
                        // Remove the old widget and create a new combo widget
                        const checkpointIndex = this.widgets.indexOf(checkpointWidget);
                        this.widgets.splice(checkpointIndex, 1);
                        
                        // Create new combo widget
                        const comboWidget = ComfyWidgets.COMBO(this, "selected_checkpoint", [["Loading..."], {}]).widget;
                        
                        // Store reference to update later
                        this.checkpointComboWidget = comboWidget;
                        
                        // Function to update checkpoint list
                        const updateCheckpoints = async (directoryPath) => {
                            if (!directoryPath) return;
                            
                            const checkpoints = await getCheckpointsFromDirectory(directoryPath);
                            if (checkpoints.length > 0 && checkpoints[0] !== "No checkpoints found") {
                                comboWidget.options.values = checkpoints;
                                
                                // Try to restore last selection for this directory
                                const lastSelection = getLastSelection(directoryPath);
                                if (lastSelection && checkpoints.includes(lastSelection)) {
                                    comboWidget.value = lastSelection;
                                } else {
                                    comboWidget.value = checkpoints[0];
                                }
                            } else {
                                comboWidget.options.values = ["No checkpoints found"];
                                comboWidget.value = "No checkpoints found";
                            }
                            
                            // Force widget update
                            if (this.onResize) {
                                this.onResize();
                            }
                        };
                        
                        // Store original combo callback
                        const originalComboCallback = comboWidget.callback;
                        
                        // Create new combo callback that saves selection
                        comboWidget.callback = function(value) {
                            // Call original callback if it exists
                            if (originalComboCallback) {
                                originalComboCallback.call(this, value);
                            }
                            
                            // Save the selection for this directory
                            if (directoryWidget.value && value && 
                                value !== "Loading..." && 
                                value !== "No checkpoints found" && 
                                !value.startsWith("Error scanning")) {
                                saveLastSelection(directoryWidget.value, value);
                            }
                        };
                        
                        // Store original callback
                        const originalCallback = directoryWidget.callback;
                        
                        // Create new callback that updates checkpoint list
                        directoryWidget.callback = function(value) {
                            // Call original callback if it exists
                            if (originalCallback) {
                                originalCallback.call(this, value);
                            }
                            
                            updateCheckpoints(value);
                        };
                        
                        // Initialize with default directory
                        if (directoryWidget.value) {
                            updateCheckpoints(directoryWidget.value);
                        }
                    }
                }, 100);
                
                return result;
            };
        }
    }
});
