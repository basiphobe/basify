import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

// Displays any input value as text on a node
app.registerExtension({
	name: "basify.DisplayAnythingAsText",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		if (nodeData.name === "BasifyDisplayAnythingAsText") {
			function populate(text) {
				// Clear all existing widgets
				if (this.widgets) {
					for (let i = 0; i < this.widgets.length; i++) {
						this.widgets[i].onRemove?.();
					}
					this.widgets.length = 0;
				}

				// Get the text value (handle array or single value)
				const textValue = Array.isArray(text) ? text[0] : text;
				
				// Create the display widget
				const w = ComfyWidgets["STRING"](
					this, 
					"display_text", 
					["STRING", { multiline: true }], 
					app
				).widget;
				
				// Configure the widget appearance and behavior
				w.inputEl.style.fontFamily = "monospace";
				w.inputEl.style.fontSize = "12px";
				// Make it editable so text can be selected and copied easily
				w.inputEl.readOnly = false;
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

			// When the node is executed, display the text from Python
			const onExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				onExecuted?.apply(this, arguments);
				populate.call(this, message.text);
			};

			// Restore widget state when loading from saved workflow
			const onConfigure = nodeType.prototype.onConfigure;
			nodeType.prototype.onConfigure = function () {
				onConfigure?.apply(this, arguments);
				if (this.widgets_values?.length) {
					populate.call(this, this.widgets_values);
				}
			};
		}
	},
});
