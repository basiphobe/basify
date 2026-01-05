import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "basify.DirectoryAutoIterator",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "BasifyDirectoryAutoIterator") {
            // onExecutionStart fires when node begins executing
            // We schedule the reset for after execution completes
            const onExecutionStart = nodeType.prototype.onExecutionStart;
            nodeType.prototype.onExecutionStart = function() {
                onExecutionStart?.apply(this, arguments);
                
                // Find the reset_progress widget
                const resetWidget = this.widgets?.find(w => w.name === "reset_progress");
                
                if (resetWidget && resetWidget.value === "true") {
                    // Schedule reset after execution completes (500ms should be enough)
                    setTimeout(() => {
                        resetWidget.value = "false";
                        app.graph?.setDirtyCanvas(true, true);
                    }, 500);
                }
            };
        }
    }
});
