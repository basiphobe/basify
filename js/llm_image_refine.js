import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Basify.ImageRefine",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "BasifyImageRefine") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated?.apply(this, arguments);
                
                // Set node styling
                this.color = "#2a4d69";
                this.bgcolor = "#1f3a50";
                
                return result;
            };
            
            // Add a button to swap vision and text models
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                onExecuted?.apply(this, arguments);
                
                // You can add custom execution behavior here if needed
                // For example, logging or custom UI updates
                if (message && message.text) {
                    console.log("[Basify Image Refine] Processing complete");
                }
            };
        }
    }
});
