import { ComfyWidgets } from "../../scripts/widgets.js";
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Basify.LatentGenerator",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "BasifyLatentGenerator") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Get widget references
                const resolutionModeWidget = this.widgets.find(w => w.name === "resolution_mode");
                const predefinedResolutionWidget = this.widgets.find(w => w.name === "predefined_resolution");
                const manualWidthWidget = this.widgets.find(w => w.name === "manual_width");
                const manualHeightWidget = this.widgets.find(w => w.name === "manual_height");
                
                // Function to update widget visibility
                const updateWidgetVisibility = () => {
                    const mode = resolutionModeWidget.value;
                    
                    if (mode === "predefined") {
                        // Show predefined, hide manual
                        predefinedResolutionWidget.type = "combo";
                        manualWidthWidget.type = "converted-widget";
                        manualHeightWidget.type = "converted-widget";
                        
                        // Hide manual widgets by setting them as converted
                        manualWidthWidget.computeSize = () => [0, -4];
                        manualHeightWidget.computeSize = () => [0, -4];
                        
                        // Show predefined widget
                        predefinedResolutionWidget.computeSize = undefined;
                    } else {
                        // Show manual, hide predefined
                        predefinedResolutionWidget.type = "converted-widget";
                        manualWidthWidget.type = "number";
                        manualHeightWidget.type = "number";
                        
                        // Hide predefined widget
                        predefinedResolutionWidget.computeSize = () => [0, -4];
                        
                        // Show manual widgets
                        manualWidthWidget.computeSize = undefined;
                        manualHeightWidget.computeSize = undefined;
                    }
                    
                    // Request redraw
                    this.setDirtyCanvas(true, true);
                };
                
                // Set initial visibility
                setTimeout(updateWidgetVisibility, 1);
                
                // Add callback to resolution mode widget
                const originalCallback = resolutionModeWidget.callback;
                resolutionModeWidget.callback = function(value) {
                    if (originalCallback) {
                        originalCallback.apply(this, arguments);
                    }
                    updateWidgetVisibility();
                };
                
                return r;
            };
        }
    }
});
