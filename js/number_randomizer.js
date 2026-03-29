import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "Basify.NumberRandomizer",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "BasifyNumberRandomizer") {
            function populate(text) {
                // Remove any existing display widget (find and remove by name)
                if (this.widgets) {
                    const widgetIndex = this.widgets.findIndex(w => w.name === "generated_value");
                    if (widgetIndex !== -1) {
                        this.widgets[widgetIndex].onRemove?.();
                        this.widgets.splice(widgetIndex, 1);
                    }
                }

                // Get the text value (handle array or single value)
                const textValue = Array.isArray(text) ? text[0] : text;
                
                // Create the display widget
                const w = ComfyWidgets["STRING"](
                    this, 
                    "generated_value", 
                    ["STRING", { multiline: true }], 
                    app
                ).widget;
                
                // Configure the widget appearance and behavior
                w.inputEl.style.fontFamily = "monospace";
                w.inputEl.style.fontSize = "14px";
                w.inputEl.readOnly = true;
                w.inputEl.style.opacity = 0.85;
                w.inputEl.style.backgroundColor = "#1e1e1e";
                
                // Set the value
                if (!textValue && textValue !== 0 && textValue !== false) {
                    w.value = "";
                } else {
                    w.value = String(textValue);
                }

                // Resize node to fit content
                requestAnimationFrame(() => {
                    const sz = this.computeSize();
                    if (sz[0] < this.size[0]) {
                        sz[0] = this.size[0];
                    }
                    if (sz[1] < this.size[1]) {
                        sz[1] = this.size[1];
                    }
                    this.onResize?.(sz);
                    app.graph.setDirtyCanvas(true, false);
                });
            }

            // When the node is executed, display the text from Python ui
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                // message.text comes from the ui.text field in Python return
                populate.call(this, message.text);
            };

            // Restore widget state when loading from saved workflow
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                onConfigure?.apply(this, arguments);
                if (this.widgets_values?.length > 3) { // More than just input values
                    populate.call(this, this.widgets_values.slice(3));
                }
            };
        }
    }
});
