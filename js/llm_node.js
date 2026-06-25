import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Cache model lists per service to avoid redundant API calls within a session.
// Stores resolved arrays (after fetch completes) or Promises (while in-flight).
const modelCache = {};

async function fetchModelsForService(serviceName) {
    // Return cached result if available (resolved array or in-flight promise)
    if (modelCache[serviceName]) {
        return modelCache[serviceName];
    }

    // Store the promise so concurrent calls share the same in-flight request
    const fetchPromise = (async () => {
        let response = null;
        let data = null;

        try {
            response = await fetch("/basify/llm_models", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ service: serviceName }),
            });

            if (response.ok) {
                data = await response.json();
                const models = data.models || [];
                // Replace promise with resolved array for instant future access
                modelCache[serviceName] = models;
                data = null;
                response = null;
                return models;
            }
        } catch (error) {
            console.error("[Basify LLM] Error fetching models:", error);
            // Clear failed cache entry so next attempt retries
            delete modelCache[serviceName];
        } finally {
            data = null;
            response = null;
        }
        delete modelCache[serviceName];
        return ["Service unavailable"];
    })();

    modelCache[serviceName] = fetchPromise;
    return fetchPromise;
}

app.registerExtension({
    name: "Basify.LLMProcess",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "LLMProcess") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);

            // Set node styling
            this.color = "#2d4a3e";
            this.bgcolor = "#1a3028";

            // Wait for widgets to be created
            setTimeout(async () => {
                const serviceWidget = this.widgets.find((w) => w.name === "service");
                const modelWidget = this.widgets.find((w) => w.name === "model");

                if (!serviceWidget || !modelWidget) return;

                // Capture the saved model value before replacing the widget
                const savedModelValue = modelWidget.value;

                // Replace the model STRING widget with a COMBO widget
                const modelIndex = this.widgets.indexOf(modelWidget);
                this.widgets.splice(modelIndex, 1);

                // Create the COMBO widget for model selection
                const comboWidget = ComfyWidgets.COMBO(
                    this,
                    "model",
                    [["Loading..."], { default: "Loading..." }]
                ).widget;

                // Move the combo widget to the correct position
                const currentIndex = this.widgets.indexOf(comboWidget);
                if (currentIndex !== modelIndex) {
                    this.widgets.splice(currentIndex, 1);
                    this.widgets.splice(modelIndex, 0, comboWidget);
                }

                // Function to update model list based on selected service
                const updateModels = async (serviceName, restoreValue) => {
                    if (!serviceName || serviceName === "No services configured") {
                        comboWidget.options.values = ["No services configured"];
                        comboWidget.value = "No services configured";
                        return;
                    }

                    comboWidget.options.values = ["Loading..."];
                    comboWidget.value = "Loading...";

                    const models = await fetchModelsForService(serviceName);
                    if (models.length > 0) {
                        comboWidget.options.values = models;
                        // Restore saved value if it exists in the list, otherwise pick first
                        if (restoreValue && models.includes(restoreValue)) {
                            comboWidget.value = restoreValue;
                        } else {
                            comboWidget.value = models[0];
                        }
                    } else {
                        comboWidget.options.values = ["No models found"];
                        comboWidget.value = "No models found";
                    }

                    app.graph.setDirtyCanvas(true);
                };

                // Listen for service changes
                const originalCallback = serviceWidget.callback;
                serviceWidget.callback = function (value) {
                    if (originalCallback) {
                        originalCallback.call(this, value);
                    }
                    updateModels(value, null);
                };

                // Initial load — fetch models for the current service, restoring saved value
                updateModels(serviceWidget.value, savedModelValue);
            }, 100);

            return result;
        };
    },
});
