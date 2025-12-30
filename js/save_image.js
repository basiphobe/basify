import { app } from "../../../scripts/app.js";

// Extension for BasifySaveImage node
if (!app.extensions.find(ext => ext.name === "basify.SaveImageToPath")) {
    app.registerExtension({
        name: "basify.SaveImageToPath",
        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            if (nodeData.name === 'BasifySaveImage') {
                // Extension registered for potential future enhancements
                // Currently no UI modifications needed
            }
        }
    });
}