import { app } from "../../../scripts/app.js";

// Adds a test sound button to the Sound Notifier node
if (!app.extensions.find(ext => ext.name === "basify.SoundNotifier")) {
    app.registerExtension({
        name: "basify.SoundNotifier",
        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            if (nodeData.name === 'BasifySoundNotifier') {
                const originalOnAdded = nodeType.prototype.onAdded;
                nodeType.prototype.onAdded = async function () {
                    originalOnAdded?.apply(this, arguments);

                    this._sound_widgets = {};

                    this._sound_widgets.testSoundButton = this.addWidget("button", "🔊 Test Sound", null, async () => {
                        // Get current widget values
                        const soundFileWidget = this.widgets.find(w => w.name === "sound_file");
                        const volumeWidget = this.widgets.find(w => w.name === "volume");
                        const enabledWidget = this.widgets.find(w => w.name === "enabled");

                        const soundFile = soundFileWidget?.value || "~/Music/that-was-quick.mp3";
                        const volume = volumeWidget?.value || 100;
                        const enabled = enabledWidget?.value || "enable";

                        console.log("[Basify Sound Test] Testing sound:", soundFile, "at", volume + "%");

                        try {
                            const response = await fetch("/basify/test_sound", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    sound_file: soundFile,
                                    volume: volume,
                                    enabled: enabled
                                })
                            });
                            
                            const result = await response.json();
                            if (response.ok) {
                                console.log("[Basify Sound Test] Success:", result);
                            } else {
                                console.error("[Basify Sound Test] Error:", result);
                            }
                        } catch (error) {
                            console.error("[Basify Sound Test] Request failed:", error);
                        }
                    }, { serialize: false });
                }
            }
        }
    });
}
