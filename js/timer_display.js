import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const TIMER_NODE_CLASS = "BasifyTimerDisplay";
const timerNodes = new Set();

let listenersAttached = false;
const DEFAULT_FONT_SIZE = 180;

function getMinimumTimerSize(node) {
	const fontSize = Number(node._timerFontSize) || DEFAULT_FONT_SIZE;
	const timerText = String(node._timerText || formatElapsed(0));
	const visibleChars = Math.max(timerText.length, 8);
	const textWidth = Math.round(visibleChars * fontSize * 0.68);

	return {
		width: textWidth + 120,
		height: Math.round(fontSize + 120),
	};
}

function updateNodeSize(node) {
	requestAnimationFrame(() => {
		const minimumSize = getMinimumTimerSize(node);
		const nextSize = node.computeSize();
		nextSize[0] = Math.max(nextSize[0], minimumSize.width);
		nextSize[1] = Math.max(nextSize[1], minimumSize.height);
		node.setSize(nextSize);
		app.graph?.setDirtyCanvas(true, false);
	});
}

function getEventApi() {
	if (app.api?.addEventListener) {
		return app.api;
	}

	return api;
}

function formatElapsed(elapsedMs) {
	const totalTenths = Math.max(0, Math.floor(elapsedMs / 100));
	const totalSeconds = Math.floor(totalTenths / 10);
	const tenths = totalTenths % 10;
	const hours = Math.floor(totalSeconds / 3600);
	const minutes = Math.floor((totalSeconds % 3600) / 60);
	const seconds = totalSeconds % 60;

	if (hours > 0) {
		return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
	}

	return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${tenths}`;
}

function updateWidgetValue(node, value) {
	const previousLength = String(node._timerText || "").length;
	node._timerText = value;
	if (value.length !== previousLength) {
		updateNodeSize(node);
	}
	app.graph?.setDirtyCanvas(true, false);
}

function renderElapsed(node, elapsedMs) {
	node._timerElapsedMs = elapsedMs;
	updateWidgetValue(node, formatElapsed(elapsedMs));
}

function clearNodeInterval(node) {
	if (node._timerInterval) {
		clearInterval(node._timerInterval);
		node._timerInterval = null;
	}
}

function stopTimer(node, wasSuccessful = true) {
	if (!node._timerRunning && node._timerStartMs == null) {
		return;
	}

	clearNodeInterval(node);

	const finalElapsed = node._timerStartMs == null
		? node._timerElapsedMs || 0
		: Date.now() - node._timerStartMs;

	node._timerRunning = false;
	node._timerStartMs = null;
	renderElapsed(node, finalElapsed);
	node._timerColor = wasSuccessful ? "#f7f2df" : "#ff8a8a";
	app.graph?.setDirtyCanvas(true, false);
}

function startTimer(node) {
	clearNodeInterval(node);
	node._timerRunning = true;
	node._timerStartMs = Date.now();
	node._timerElapsedMs = 0;
	renderElapsed(node, 0);

	node._timerColor = "#ffe49c";

	node._timerInterval = setInterval(() => {
		renderElapsed(node, Date.now() - node._timerStartMs);
	}, 100);
}

function startAllTimers() {
	for (const node of timerNodes) {
		startTimer(node);
	}
}

function ensureTimersStarted() {
	for (const node of timerNodes) {
		if (!node._timerRunning) {
			startTimer(node);
		}
	}
}

function stopAllTimers(wasSuccessful = true) {
	for (const node of timerNodes) {
		stopTimer(node, wasSuccessful);
	}
}

function attachListeners() {
	if (listenersAttached) {
		return;
	}

	listenersAttached = true;
	const eventApi = getEventApi();

	eventApi.addEventListener("execution_start", () => {
		for (const node of timerNodes) {
			node._timerQueued = true;
		}
	});

	eventApi.addEventListener("executing", ({ detail }) => {
		if (detail == null) {
			stopAllTimers(true);
			for (const node of timerNodes) {
				node._timerQueued = false;
			}
			return;
		}

		ensureTimersStarted();
	});

	eventApi.addEventListener("progress", () => {
		ensureTimersStarted();
	});

	eventApi.addEventListener("execution_cached", () => {
		ensureTimersStarted();
	});

	eventApi.addEventListener("status", ({ detail }) => {
		const queueRemaining = detail?.exec_info?.queue_remaining;
		if (queueRemaining === 0 && !app.runningNodeId) {
			stopAllTimers(true);
		}
	});

	eventApi.addEventListener("execution_complete", () => {
		stopAllTimers(true);
		for (const node of timerNodes) {
			node._timerQueued = false;
		}
	});

	eventApi.addEventListener("execution_success", () => {
		stopAllTimers(true);
		for (const node of timerNodes) {
			node._timerQueued = false;
		}
	});

	eventApi.addEventListener("execution_error", () => {
		stopAllTimers(false);
		for (const node of timerNodes) {
			node._timerQueued = false;
		}
	});

	eventApi.addEventListener("execution_interrupted", () => {
		stopAllTimers(false);
		for (const node of timerNodes) {
			node._timerQueued = false;
		}
	});
}

function ensureTimerDisplay(node) {
	if (node._timerDisplayInitialized) {
		return;
	}

	node._timerDisplayInitialized = true;
	node._timerText = formatElapsed(node._timerElapsedMs || 0);
	node._timerColor = "#f7f2df";
	updateNodeSize(node);
}

function ensureTextSizeWidget(node) {
	if (node._timerSizeWidget) {
		return;
	}

	const widget = node.addWidget(
		"slider",
		"text_size",
		node._timerFontSize || DEFAULT_FONT_SIZE,
		(value) => {
			node._timerFontSize = Number(value) || DEFAULT_FONT_SIZE;
			updateNodeSize(node);
		},
		{
			min: 24,
			max: 300,
			step: 1,
			precision: 0,
		}
	);

	node._timerSizeWidget = widget;
}

function initializeNode(node) {
	if (node.comfyClass !== TIMER_NODE_CLASS || node._basifyTimerInitialized) {
		return;
	}

	node._basifyTimerInitialized = true;
	node._timerInterval = null;
	node._timerStartMs = null;
	node._timerElapsedMs = 0;
	node._timerRunning = false;
	node._timerQueued = false;
	node._timerFontSize = DEFAULT_FONT_SIZE;
	node._timerText = formatElapsed(0);
	node._timerColor = "#f7f2df";
	node.color = "#6b5121";
	node.bgcolor = "#2a2114";

	ensureTextSizeWidget(node);
	ensureTimerDisplay(node);
	timerNodes.add(node);

	const originalOnDrawForeground = node.onDrawForeground;
	node.onDrawForeground = function (ctx) {
		const result = originalOnDrawForeground?.apply(this, arguments);

		if (!ctx || this.flags?.collapsed) {
			return result;
		}

		ctx.save();
		ctx.fillStyle = this._timerColor || "#f7f2df";
		ctx.font = `700 ${this._timerFontSize || DEFAULT_FONT_SIZE}px monospace`;
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.fillText(
			this._timerText || formatElapsed(0),
			this.size[0] / 2,
			Math.max((this._timerFontSize || DEFAULT_FONT_SIZE) * 0.7, this.size[1] / 2 + 10)
		);
		ctx.restore();

		return result;
	};

	const originalOnRemoved = node.onRemoved;
	node.onRemoved = function () {
		clearNodeInterval(this);
		timerNodes.delete(this);
		return originalOnRemoved?.apply(this, arguments);
	};

	const originalOnConfigure = node.onConfigure;
	node.onConfigure = function () {
		const result = originalOnConfigure?.apply(this, arguments);
		this._timerFontSize = Number(this._timerSizeWidget?.value) || this._timerFontSize || DEFAULT_FONT_SIZE;
		ensureTextSizeWidget(this);
		ensureTimerDisplay(this);
		renderElapsed(this, this._timerElapsedMs || 0);
		updateNodeSize(this);
		return result;
	};
}

app.registerExtension({
	name: "basify.TimerDisplay",
	setup() {
		attachListeners();
	},
	nodeCreated(node) {
		initializeNode(node);
	}
});
