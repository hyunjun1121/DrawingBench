// Drawing Application with all advanced features
class DrawingApp {
    constructor() {
        this.canvas = document.getElementById('drawingCanvas');
        this.ctx = this.canvas.getContext('2d');

        // Calculate canvas offset dynamically
        this.updateCanvasOffset();

        // Drawing state
        this.currentTool = 'pen';
        this.currentColor = '#000000';
        this.currentSize = 2;
        this.isDrawing = false;
        this.lastX = 0;
        this.lastY = 0;
        this.mouseX = 0;
        this.mouseY = 0;

        // Shape tool state
        this.shapeStartX = 0;
        this.shapeStartY = 0;
        this.tempCanvas = null;

        // Action log
        this.actionLog = [];

        // History for undo/redo
        this.history = [];
        this.historyStep = -1;
        this.maxHistory = 50;

        // Performance metrics
        this.metrics = {
            startTime: null,
            endTime: null,
            totalActions: 0,
            drawingActions: 0,
            toolChanges: 0,
            colorChanges: 0
        };

        // Execution control
        this.isExecuting = false;
        this.stopRequested = false;

        // UI coordinates cache
        this.uiCoordinates = {};

        this.init();
    }

    init() {
        // Clear canvas
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Save initial state
        this.saveState();

        // Calculate UI element coordinates
        this.calculateUICoordinates();

        // Setup UI event listeners
        this.setupUIListeners();

        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Track mouse position and update cursor preview
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
            this.updateCursorPreview(e.clientX, e.clientY);
            this.updateStateDisplay();
        });

        // Update canvas offset on window resize
        window.addEventListener('resize', () => {
            this.updateCanvasOffset();
        });

        this.updateStateDisplay();
    }

    updateCanvasOffset() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvasOffsetX = rect.left;
        this.canvasOffsetY = rect.top;
    }

    calculateUICoordinates() {
        // Calculate exact coordinates for all UI elements
        this.uiCoordinates = {
            tools: [],
            sizes: [],
            colors: []
        };

        // Tools
        const toolButtons = document.querySelectorAll('.tool-button');
        toolButtons.forEach((btn, index) => {
            const rect = btn.getBoundingClientRect();
            const coords = {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2),
                tool: btn.dataset.tool
            };
            this.uiCoordinates.tools.push(coords);
            btn.dataset.coords = JSON.stringify([coords.x, coords.y]);
        });

        // Sizes
        const sizeButtons = document.querySelectorAll('.size-button');
        sizeButtons.forEach((btn, index) => {
            const rect = btn.getBoundingClientRect();
            const coords = {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2),
                size: btn.dataset.size
            };
            this.uiCoordinates.sizes.push(coords);
            btn.dataset.coords = JSON.stringify([coords.x, coords.y]);
        });

        // Colors
        const colorButtons = document.querySelectorAll('.color-button');
        colorButtons.forEach((btn, index) => {
            const rect = btn.getBoundingClientRect();
            const coords = {
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2),
                color: btn.dataset.color
            };
            this.uiCoordinates.colors.push(coords);
            btn.dataset.coords = JSON.stringify([coords.x, coords.y]);
        });
    }

    setupUIListeners() {
        // Tool buttons
        document.querySelectorAll('.tool-button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tool-button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentTool = btn.dataset.tool;
                this.metrics.toolChanges++;
                this.log(`Tool selected: ${this.currentTool}`);
                this.updateStateDisplay();
            });
        });

        // Size buttons
        document.querySelectorAll('.size-button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.size-button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentSize = parseInt(btn.dataset.size);
                this.log(`Size changed: ${this.currentSize}`);
                this.updateStateDisplay();
            });
        });

        // Color buttons
        document.querySelectorAll('.color-button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.color-button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentColor = btn.dataset.color;
                this.metrics.colorChanges++;
                this.log(`Color changed: ${this.currentColor}`);
                this.updateStateDisplay();
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Z: Undo
            if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            }
            // Ctrl+Shift+Z or Ctrl+Y: Redo
            if ((e.ctrlKey && e.shiftKey && e.key === 'z') || (e.ctrlKey && e.key === 'y')) {
                e.preventDefault();
                this.redo();
            }
        });
    }

    updateCursorPreview(x, y) {
        const preview = document.getElementById('cursorPreview');
        const rect = this.canvas.getBoundingClientRect();

        // Only show preview when over canvas
        if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
            preview.style.display = 'block';
            preview.style.left = x + 'px';
            preview.style.top = y + 'px';
            preview.style.width = this.currentSize * 2 + 'px';
            preview.style.height = this.currentSize * 2 + 'px';
            preview.style.borderColor = this.currentColor;
        } else {
            preview.style.display = 'none';
        }
    }

    saveState() {
        // Remove any states after current step
        this.history = this.history.slice(0, this.historyStep + 1);

        // Save current canvas state
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        this.history.push(imageData);

        // Limit history size
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyStep++;
        }
    }

    undo() {
        if (this.historyStep > 0) {
            this.historyStep--;
            const imageData = this.history[this.historyStep];
            this.ctx.putImageData(imageData, 0, 0);
            this.log('Undo');
        }
    }

    redo() {
        if (this.historyStep < this.history.length - 1) {
            this.historyStep++;
            const imageData = this.history[this.historyStep];
            this.ctx.putImageData(imageData, 0, 0);
            this.log('Redo');
        }
    }

    // Convert screen coordinates to canvas coordinates
    screenToCanvas(screenX, screenY) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: screenX - rect.left,
            y: screenY - rect.top
        };
    }

    // Mouse actions
    moveTo(x, y) {
        this.mouseX = x;
        this.mouseY = y;

        this.log(`moveTo: (${x}, ${y})`);
        this.updateStateDisplay();

        // If drawing with pen/eraser, continue the line
        if (this.isDrawing && (this.currentTool === 'pen' || this.currentTool === 'eraser')) {
            const canvasCoords = this.screenToCanvas(x, y);
            this.drawLine(this.lastX, this.lastY, canvasCoords.x, canvasCoords.y);
            this.lastX = canvasCoords.x;
            this.lastY = canvasCoords.y;
            this.metrics.drawingActions++;
        }
    }

    click(x, y) {
        // Use current mouse position if coordinates not provided
        if (x === undefined) {
            x = this.mouseX;
            y = this.mouseY;
        }

        const element = document.elementFromPoint(x, y);

        // Check if clicking on tool button
        const toolButton = element.closest('.tool-button');
        if (toolButton) {
            toolButton.click();
            this.log(`click: Tool button at (${x}, ${y}) - ${toolButton.dataset.tool}`);
            return;
        }

        // Check if clicking on size button
        const sizeButton = element.closest('.size-button');
        if (sizeButton) {
            sizeButton.click();
            this.log(`click: Size button at (${x}, ${y}) - ${sizeButton.dataset.size}`);
            return;
        }

        // Check if clicking on color button
        const colorButton = element.closest('.color-button');
        if (colorButton) {
            colorButton.click();
            this.log(`click: Color button at (${x}, ${y}) - ${colorButton.dataset.color}`);
            return;
        }

        // Check if clicking on canvas
        if (element === this.canvas || element.closest('.canvas-wrapper')) {
            const canvasCoords = this.screenToCanvas(x, y);

            if (this.currentTool === 'fill') {
                this.floodFill(canvasCoords.x, canvasCoords.y);
                this.saveState();
                this.log(`click: Fill at canvas (${Math.round(canvasCoords.x)}, ${Math.round(canvasCoords.y)})`);
            } else {
                // Single click draw (dot)
                this.drawDot(canvasCoords.x, canvasCoords.y);
                this.saveState();
                this.log(`click: Draw dot at canvas (${Math.round(canvasCoords.x)}, ${Math.round(canvasCoords.y)})`);
            }
            this.metrics.drawingActions++;
        }
    }

    mouseDown(x, y) {
        // Use current mouse position if coordinates not provided
        if (x === undefined) {
            x = this.mouseX;
            y = this.mouseY;
        }

        const element = document.elementFromPoint(x, y);

        // Only start drawing if on canvas
        if (element === this.canvas || element.closest('.canvas-wrapper')) {
            const canvasCoords = this.screenToCanvas(x, y);
            this.isDrawing = true;
            this.lastX = canvasCoords.x;
            this.lastY = canvasCoords.y;
            this.shapeStartX = canvasCoords.x;
            this.shapeStartY = canvasCoords.y;

            // For shape tools, save the current canvas
            if (['line', 'rectangle', 'circle'].includes(this.currentTool)) {
                this.tempCanvas = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            }

            this.log(`mouseDown: at (${x}, ${y}) -> canvas (${Math.round(canvasCoords.x)}, ${Math.round(canvasCoords.y)})`);
        }
    }

    mouseUp(x, y) {
        if (this.isDrawing) {
            if (x === undefined) {
                x = this.mouseX;
                y = this.mouseY;
            }

            const canvasCoords = this.screenToCanvas(x, y);

            // Draw final shape for shape tools
            if (['line', 'rectangle', 'circle'].includes(this.currentTool)) {
                this.drawShape(this.shapeStartX, this.shapeStartY, canvasCoords.x, canvasCoords.y);
                this.tempCanvas = null;
            }

            this.isDrawing = false;
            this.saveState();
            this.log(`mouseUp: at (${x}, ${y})`);
        }
    }

    // Drawing functions
    drawLine(x1, y1, x2, y2) {
        if (this.currentTool === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
        } else {
            this.ctx.globalCompositeOperation = 'source-over';
        }

        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = this.currentSize;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();

        this.ctx.globalCompositeOperation = 'source-over';
    }

    drawDot(x, y) {
        if (this.currentTool === 'eraser') {
            this.ctx.globalCompositeOperation = 'destination-out';
        } else {
            this.ctx.globalCompositeOperation = 'source-over';
        }

        this.ctx.fillStyle = this.currentColor;
        this.ctx.beginPath();
        this.ctx.arc(x, y, this.currentSize / 2, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.globalCompositeOperation = 'source-over';
    }

    drawShape(x1, y1, x2, y2) {
        // Restore canvas before drawing final shape
        if (this.tempCanvas) {
            this.ctx.putImageData(this.tempCanvas, 0, 0);
        }

        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = this.currentSize;
        this.ctx.lineCap = 'round';

        switch (this.currentTool) {
            case 'line':
                this.ctx.beginPath();
                this.ctx.moveTo(x1, y1);
                this.ctx.lineTo(x2, y2);
                this.ctx.stroke();
                break;

            case 'rectangle':
                this.ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                break;

            case 'circle':
                const radius = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
                this.ctx.beginPath();
                this.ctx.arc(x1, y1, radius, 0, Math.PI * 2);
                this.ctx.stroke();
                break;
        }
    }

    floodFill(startX, startY) {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;

        const startPos = (Math.floor(startY) * this.canvas.width + Math.floor(startX)) * 4;
        const startR = data[startPos];
        const startG = data[startPos + 1];
        const startB = data[startPos + 2];

        const fillColor = this.hexToRgb(this.currentColor);

        if (startR === fillColor.r && startG === fillColor.g && startB === fillColor.b) {
            return;
        }

        const stack = [[Math.floor(startX), Math.floor(startY)]];
        const visited = new Set();

        while (stack.length > 0) {
            const [x, y] = stack.pop();
            const key = `${x},${y}`;

            if (visited.has(key)) continue;
            if (x < 0 || x >= this.canvas.width || y < 0 || y >= this.canvas.height) continue;

            const pos = (y * this.canvas.width + x) * 4;
            const r = data[pos];
            const g = data[pos + 1];
            const b = data[pos + 2];

            if (r !== startR || g !== startG || b !== startB) continue;

            visited.add(key);
            data[pos] = fillColor.r;
            data[pos + 1] = fillColor.g;
            data[pos + 2] = fillColor.b;
            data[pos + 3] = 255;

            if (visited.size > 100000) break;

            stack.push([x + 1, y]);
            stack.push([x - 1, y]);
            stack.push([x, y + 1]);
            stack.push([x, y - 1]);
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    // Logging
    log(message) {
        this.actionLog.push({
            timestamp: Date.now(),
            message: message
        });

        if (this.actionLog.length > 50) {
            this.actionLog.shift();
        }

        this.updateLogDisplay();
    }

    updateLogDisplay() {
        const logElement = document.getElementById('actionLog');
        logElement.innerHTML = this.actionLog
            .slice()
            .reverse()
            .map(entry => {
                const match = entry.message.match(/^(\w+):\s*(.+)$/);
                if (match) {
                    return `<div class="log-entry"><span class="log-action">${match[1]}</span>: <span class="log-coords">${match[2]}</span></div>`;
                }
                return `<div class="log-entry">${entry.message}</div>`;
            })
            .join('');
    }

    updateStateDisplay() {
        const stateElement = document.getElementById('currentState');
        stateElement.innerHTML = `
            Tool: ${this.currentTool}<br>
            Color: ${this.currentColor}<br>
            Size: ${this.currentSize}<br>
            Mouse: (${this.mouseX}, ${this.mouseY})<br>
            Drawing: ${this.isDrawing ? 'Yes' : 'No'}
        `;
    }

    updateMetricsDisplay() {
        const metricsElement = document.getElementById('metrics');
        const duration = this.metrics.endTime ? this.metrics.endTime - this.metrics.startTime : 0;
        const efficiency = this.metrics.totalActions > 0 ?
            (this.metrics.drawingActions / this.metrics.totalActions * 100).toFixed(1) : 'N/A';

        metricsElement.innerHTML = `
            <div>Total Actions: ${this.metrics.totalActions}</div>
            <div>Drawing Actions: ${this.metrics.drawingActions}</div>
            <div>Tool Changes: ${this.metrics.toolChanges}</div>
            <div>Color Changes: ${this.metrics.colorChanges}</div>
            <div>Execution Time: ${duration}ms</div>
            <div>Efficiency: ${efficiency}%</div>
        `;
    }

    clear() {
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.saveState();
        this.log('Canvas cleared');
    }

    downloadCanvas() {
        const link = document.createElement('a');
        link.download = `drawing_${Date.now()}.png`;
        link.href = this.canvas.toDataURL();
        link.click();
        this.log('Canvas downloaded');
    }

    getCanvasDataURL() {
        return this.canvas.toDataURL();
    }

    // Execute command with error handling
    async executeCommand(command, skipDelay = false) {
        if (this.stopRequested) {
            throw new Error('Execution stopped by user');
        }

        const action = command.action;
        this.metrics.totalActions++;

        try {
            switch (action) {
                case 'moveTo':
                    if (command.x === undefined || command.y === undefined) {
                        throw new Error('moveTo requires x and y coordinates');
                    }
                    this.moveTo(command.x, command.y);
                    break;
                case 'click':
                    this.click(command.x, command.y);
                    break;
                case 'mouseDown':
                    this.mouseDown(command.x, command.y);
                    break;
                case 'mouseUp':
                    this.mouseUp(command.x, command.y);
                    break;
                case 'undo':
                    this.undo();
                    break;
                case 'redo':
                    this.redo();
                    break;
                default:
                    throw new Error(`Unknown action: ${action}`);
            }

            // Small delay for visualization
            if (!skipDelay) {
                await new Promise(resolve => setTimeout(resolve, 5));
            }

        } catch (error) {
            this.log(`ERROR: ${error.message}`);
            throw error;
        }
    }

    exportCoordinates() {
        return {
            canvas: {
                offset: {
                    x: Math.round(this.canvasOffsetX),
                    y: Math.round(this.canvasOffsetY)
                },
                size: {
                    width: this.canvas.width,
                    height: this.canvas.height
                },
                bounds: {
                    left: Math.round(this.canvasOffsetX),
                    top: Math.round(this.canvasOffsetY),
                    right: Math.round(this.canvasOffsetX + this.canvas.width),
                    bottom: Math.round(this.canvasOffsetY + this.canvas.height)
                }
            },
            tools: this.uiCoordinates.tools,
            sizes: this.uiCoordinates.sizes,
            colors: this.uiCoordinates.colors
        };
    }
}

// Global app instance
let app;

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    app = new DrawingApp();
    setStatus('Ready - Drawing app initialized', 'success');
});

// Execute commands from textarea
async function executeCommands() {
    const input = document.getElementById('commandInput').value.trim();

    if (!input) {
        setStatus('Error: Empty input', 'error');
        return;
    }

    try {
        const commands = JSON.parse(input);

        if (!Array.isArray(commands)) {
            throw new Error('Input must be an array of commands');
        }

        app.isExecuting = true;
        app.stopRequested = false;
        app.metrics.startTime = Date.now();
        app.metrics.totalActions = 0;
        app.metrics.drawingActions = 0;

        setStatus(`Executing ${commands.length} commands...`, '');

        for (let i = 0; i < commands.length; i++) {
            try {
                await app.executeCommand(commands[i], true);
            } catch (err) {
                if (err.message === 'Execution stopped by user') {
                    setStatus(`Execution stopped at command ${i}`, 'warning');
                    return;
                }
                // Continue execution despite errors
                console.error(`Error at command ${i}:`, err);
            }
        }

        app.metrics.endTime = Date.now();
        app.updateMetricsDisplay();
        setStatus(`Successfully executed ${commands.length} commands`, 'success');

    } catch (err) {
        setStatus(`Parse error: ${err.message}`, 'error');
    } finally {
        app.isExecuting = false;
        app.stopRequested = false;
    }
}

// Execute with visual replay
async function executeWithReplay() {
    const input = document.getElementById('commandInput').value.trim();

    if (!input) {
        setStatus('Error: Empty input', 'error');
        return;
    }

    try {
        const commands = JSON.parse(input);

        if (!Array.isArray(commands)) {
            throw new Error('Input must be an array of commands');
        }

        app.isExecuting = true;
        app.stopRequested = false;
        app.metrics.startTime = Date.now();
        app.metrics.totalActions = 0;
        app.metrics.drawingActions = 0;

        setStatus(`Replaying ${commands.length} commands...`, '');

        for (let i = 0; i < commands.length; i++) {
            try {
                await app.executeCommand(commands[i], false); // With delay
            } catch (err) {
                if (err.message === 'Execution stopped by user') {
                    setStatus(`Replay stopped at command ${i}`, 'warning');
                    return;
                }
                console.error(`Error at command ${i}:`, err);
            }
        }

        app.metrics.endTime = Date.now();
        app.updateMetricsDisplay();
        setStatus(`Replay completed (${commands.length} commands)`, 'success');

    } catch (err) {
        setStatus(`Parse error: ${err.message}`, 'error');
    } finally {
        app.isExecuting = false;
        app.stopRequested = false;
    }
}

// Stop execution
function stopExecution() {
    if (app.isExecuting) {
        app.stopRequested = true;
        setStatus('Stop requested...', 'warning');
    }
}

// Clear canvas
function clearCanvas() {
    app.clear();
    setStatus('Canvas cleared', 'success');
}

// Run evaluation
function runEvaluation() {
    const resultElement = document.getElementById('evaluationResult');
    const imageData = app.getCanvasDataURL();
    const metrics = app.metrics;

    // Simple client-side evaluation
    const evaluation = {
        canvas_data: imageData.substring(0, 100) + '...',
        metrics: metrics,
        history_size: app.history.length,
        current_state: {
            tool: app.currentTool,
            color: app.currentColor,
            size: app.currentSize
        }
    };

    resultElement.textContent = JSON.stringify(evaluation, null, 2);
    setStatus('Evaluation completed', 'success');
}

// Download coordinates
function downloadCoordinates() {
    const coords = app.exportCoordinates();
    const blob = new Blob([JSON.stringify(coords, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ui_coordinates.json';
    link.click();
    URL.revokeObjectURL(url);
    setStatus('Coordinates exported', 'success');
}

// Capture screenshots for vision tasks
function captureCleanUI() {
    // Capture initial clean UI state (for turn 1)
    return html2canvas(document.body, {
        backgroundColor: '#f0f0f0',
        scale: 1,
        logging: false
    }).then(canvas => {
        return canvas.toDataURL('image/png');
    });
}

function captureCanvasOnly() {
    // Capture only the drawing canvas area
    return app.canvas.toDataURL('image/png');
}

function captureFullState() {
    // Capture entire UI with current state visible
    return html2canvas(document.body, {
        backgroundColor: '#f0f0f0',
        scale: 1,
        logging: false
    }).then(canvas => {
        return canvas.toDataURL('image/png');
    });
}

async function downloadScreenshot(type = 'full') {
    let dataUrl;
    let filename;

    switch(type) {
        case 'canvas':
            dataUrl = captureCanvasOnly();
            filename = 'canvas_screenshot.png';
            break;
        case 'clean':
            dataUrl = await captureCleanUI();
            filename = 'clean_ui_screenshot.png';
            break;
        default:
            dataUrl = await captureFullState();
            filename = 'full_screenshot.png';
    }

    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = filename;
    link.click();
    setStatus(`Screenshot saved: ${filename}`, 'success');
}

// Set status message
function setStatus(message, type) {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    statusElement.className = 'status';
    if (type) {
        statusElement.classList.add(type);
    }
}
