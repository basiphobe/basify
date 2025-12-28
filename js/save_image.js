import { app } from "../../../scripts/app.js";

// Saves an image to a specified location
if (!app.extensions.find(ext => ext.name === "basify.SaveImageToPath")) {
    app.registerExtension({
        name: "basify.SaveImageToPath",
        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            if (nodeData.name === 'BasifySaveImage') {
                const originalOnAdded = nodeType.prototype.onAdded;
                nodeType.prototype.onAdded = async function () {
                    originalOnAdded?.apply(this, arguments);

                    this._llm_widgets = {};

                    this._llm_widgets.saveAgainButton = this.addWidget("button", "Save Again", null, async () => {
                        await fetch("/basify/server/llm/save_again", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: {}
                        });
                    }, { width: 50, serialize: false });
                }
            }
        }
    });
}