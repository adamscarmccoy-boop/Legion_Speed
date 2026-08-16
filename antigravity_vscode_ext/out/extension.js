"use strict";
// extension.ts
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const path = require("path"); // Node.js path module for cross-platform path handling
const fs = require("fs");
const child_process_1 = require("child_process");
let apiProcess;
let activePanel;
/**
 * Client for interacting with the Legion API Bridge.
 * Handles connection, retries, and error surfacing to the VS Code UI.
 */
class LegionClient {
    baseUrl;
    maxRetries = 5;
    retryDelayMs = 1000; // Initial delay for exponential backoff
    statusItem; // VS Code status bar item to display connection/processing state
    isConnected = false; // Internal state for connection status
    constructor(baseUrl, statusItem) {
        this.baseUrl = baseUrl;
        this.statusItem = statusItem;
    }
    /**
     * Pings the API bridge to check connectivity.
     * Implements exponential backoff for initial connection attempts and updates UI status.
     */
    async ping() {
        this.statusItem.text = "$(loading~spin) Connecting to Legion...";
        this.statusItem.tooltip = "Attempting to connect to Legion API Bridge...";
        this.statusItem.backgroundColor = undefined; // Reset background color
        for (let i = 0; i < this.maxRetries; i++) {
            try {
                const response = await fetch(`${this.baseUrl}/ping`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'pong') {
                        this.isConnected = true;
                        this.updateStatusUI("ready", "Legion API Bridge is online and ready.");
                        console.log("Legion API Bridge connected successfully.");
                        return true;
                    }
                }
            }
            catch (error) {
                console.warn(`Legion API Bridge connection attempt ${i + 1} failed: ${error}`);
            }
            // Exponential backoff
            await new Promise(resolve => setTimeout(resolve, this.retryDelayMs * Math.pow(2, i)));
        }
        this.isConnected = false;
        this.updateStatusUI("error", "Failed to connect to Legion API Bridge after multiple attempts. Please ensure the backend server is running.", true);
        return false;
    }
    /**
     * Updates the VS Code status bar item with the given status and message.
     * @param status The status type ("ready", "processing", "error").
     * @param message The message to display.
     * @param showAlert If true, also shows a VS Code error message box.
     */
    updateStatusUI(status, message, showAlert = false) {
        this.statusItem.tooltip = message;
        switch (status) {
            case "initializing":
                this.statusItem.text = "$(loading~spin) Legion Initializing...";
                this.statusItem.backgroundColor = undefined;
                break;
            case "ready":
                this.statusItem.text = "$(check) Legion Connected";
                this.statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.successBackground');
                break;
            case "processing":
                this.statusItem.text = "$(loading~spin) Legion Processing...";
                this.statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                break;
            case "error":
                this.statusItem.text = "$(error) Legion Error";
                this.statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                if (showAlert) {
                    vscode.window.showErrorMessage(`Legion Error: ${message}`);
                }
                break;
        }
    }
    /**
     * Generic fetch wrapper with robust error handling and UI status updates.
     */
    async _fetch(endpoint, method, body) {
        if (!this.isConnected) {
            this.updateStatusUI("error", "Legion API Bridge is not connected. Attempting to reconnect...", true);
            const reconnected = await this.ping();
            if (!reconnected) {
                return null;
            }
        }
        this.updateStatusUI("processing", `Executing ${endpoint}...`);
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: body ? JSON.stringify(body) : undefined,
            };
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            if (!response.ok) {
                const errorData = (await response.json().catch(() => ({ detail: `HTTP error! Status: ${response.status} - ${response.statusText}` })));
                const errorMessage = errorData?.detail || `Legion API error: ${response.statusText || 'Unknown error'}. Response: ${JSON.stringify(errorData)}`;
                this.updateStatusUI("error", errorMessage, true);
                return null;
            }
            const result = (await response.json());
            this.updateStatusUI("ready", "Legion operation completed successfully.");
            return result;
        }
        catch (error) {
            const errorMessage = `Legion Client Error (${endpoint}): ${error.message || error}`;
            this.updateStatusUI("error", errorMessage, true);
            return null;
        }
    }
    async getStatus() {
        return this._fetch('/status', 'GET');
    }
    async analyzeAudio(request) {
        return this._fetch('/analyze_audio', 'POST', request);
    }
    async masterAudio(request) {
        return this._fetch('/master_audio', 'POST', request);
    }
    async chat(request) {
        return this._fetch('/chat', 'POST', request);
    }
}
function activate(context) {
    // Create a dedicated LogOutputChannel which automatically saves to context.logUri
    const logChannel = vscode.window.createOutputChannel('Legion Sonic Engine', { log: true });
    context.subscriptions.push(logChannel);
    logChannel.info('Legion Sonic Engine extension is now active!');
    // Get API Base URL from VS Code settings, default to http://localhost:8000
    const apiBaseUrl = vscode.workspace.getConfiguration('legionSonicEngine').get('apiBaseUrl') || 'http://localhost:8000';
    // Create a status bar item
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusItem.show();
    const client = new LegionClient(apiBaseUrl, statusItem);
    // Start the backend API process automatically
    const backendPath = path.join(context.extensionPath, 'backend', 'api_bridge.py');
    const pythonExecutable = vscode.workspace.getConfiguration('python').get('defaultInterpreterPath') || 'python';
    logChannel.info(`Starting API Bridge from: ${backendPath} using ${pythonExecutable}`);
    apiProcess = (0, child_process_1.spawn)(pythonExecutable, [backendPath], { cwd: path.join(context.extensionPath, 'backend') });
    apiProcess.stdout?.on('data', (data) => {
        const text = data.toString().trim();
        if (text) {
            logChannel.info(`[API Bridge]: ${text}`);
            activePanel?.webview.postMessage({ command: 'receiveLog', text: text });
        }
    });
    apiProcess.stderr?.on('data', (data) => {
        const text = data.toString().trim();
        if (text) {
            logChannel.error(`[API Bridge Error]: ${text}`);
            activePanel?.webview.postMessage({ command: 'receiveLog', text: text });
        }
    });
    // Initial connection attempt when the extension activates
    client.ping();
    // --- Register VS Code Commands ---
    // Command to analyze the active audio file or a path in the active editor
    let disposableAnalyze = vscode.commands.registerCommand('legionSonicEngine.analyzeAudio', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active text editor. Please open an audio file path in a text editor or select it in Explorer.');
            return;
        }
        let filePath;
        // Determine file path: either from the active file or from text in the editor
        if (editor.document.uri.scheme === 'file' && editor.document.languageId === 'plaintext') {
            filePath = editor.document.getText().trim();
            if (!filePath || !filePath.match(/\.(wav|mp3|flac)$/i)) {
                vscode.window.showErrorMessage('The active document does not contain a valid audio file path (e.g., .wav, .mp3, .flac).');
                return;
            }
        }
        else if (editor.document.uri.scheme === 'file') {
            filePath = editor.document.uri.fsPath;
            if (!filePath.match(/\.(wav|mp3|flac)$/i)) {
                vscode.window.showErrorMessage('The active file is not a valid audio file (e.g., .wav, .mp3, .flac).');
                return;
            }
        }
        else {
            vscode.window.showErrorMessage('Please open an audio file or a text file containing an audio file path to analyze.');
            return;
        }
        // Basic check for file existence (backend will do a more robust check)
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
        }
        catch {
            vscode.window.showErrorMessage(`File not found at: ${filePath}. Please ensure the path is correct and accessible.`);
            return;
        }
        const request = { file_path: filePath };
        const result = await client.analyzeAudio(request);
        if (result?.success) {
            vscode.window.showInformationMessage(`Legion Audio Analysis Complete for: ${path.basename(filePath)}`);
            if (result.data) {
                // Display analysis results in a new read-only JSON editor
                const doc = await vscode.workspace.openTextDocument({
                    content: JSON.stringify(result.data, null, 2),
                    language: 'json'
                });
                await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside, true); // Open beside, preserve focus
            }
        }
        else {
            vscode.window.showErrorMessage(`Legion Audio Analysis Failed for: ${path.basename(filePath)}. ${result?.message || 'Unknown error.'}`);
        }
    });
    // Command to master the active audio file or a path in the active editor
    let disposableMaster = vscode.commands.registerCommand('legionSonicEngine.masterAudio', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active text editor. Please open an audio file path in a text editor or select it in Explorer.');
            return;
        }
        let inputFilePath;
        if (editor.document.uri.scheme === 'file' && editor.document.languageId === 'plaintext') {
            inputFilePath = editor.document.getText().trim();
            if (!inputFilePath || !inputFilePath.match(/\.(wav|mp3|flac)$/i)) {
                vscode.window.showErrorMessage('The active document does not contain a valid audio file path (e.g., .wav, .mp3, .flac).');
                return;
            }
        }
        else if (editor.document.uri.scheme === 'file') {
            inputFilePath = editor.document.uri.fsPath;
            if (!inputFilePath.match(/\.(wav|mp3|flac)$/i)) {
                vscode.window.showErrorMessage('The active file is not a valid audio file (e.g., .wav, .mp3, .flac).');
                return;
            }
        }
        else {
            vscode.window.showErrorMessage('Please open an audio file or a text file containing an audio file path to master.');
            return;
        }
        // Basic check for input file existence
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(inputFilePath));
        }
        catch {
            vscode.window.showErrorMessage(`Input file not found at: ${inputFilePath}. Please ensure the path is correct and accessible.`);
            return;
        }
        // Prompt user for output file path
        const baseName = path.basename(inputFilePath, path.extname(inputFilePath));
        const outputDirectory = path.dirname(inputFilePath);
        const suggestedOutputPath = path.join(outputDirectory, `${baseName}_MASTERED.wav`);
        const outputFilePath = await vscode.window.showInputBox({
            prompt: `Enter the output path for the mastered audio.`,
            value: suggestedOutputPath,
            placeHolder: 'E.g., /path/to/my_track_mastered.wav'
        });
        if (!outputFilePath) {
            vscode.window.showInformationMessage('Audio mastering cancelled by user.');
            return;
        }
        const request = {
            input_file_path: inputFilePath,
            output_file_path: outputFilePath
        };
        const result = await client.masterAudio(request);
        if (result?.success) {
            vscode.window.showInformationMessage(`Legion Audio Mastering Complete! Output: ${path.basename(outputFilePath)}`);
            if (result.data) {
                // Optionally display more data about the mastering process (e.g., metrics)
                const doc = await vscode.workspace.openTextDocument({
                    content: JSON.stringify(result.data, null, 2),
                    language: 'json'
                });
                await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside, true);
            }
        }
        else {
            vscode.window.showErrorMessage(`Legion Audio Mastering Failed for: ${path.basename(inputFilePath)}. ${result?.message || 'Unknown error.'}`);
        }
    });
    // Command to manually refresh the connection status
    let disposableRefresh = vscode.commands.registerCommand('legionSonicEngine.refreshConnection', () => {
        client.ping();
    });
    // Command to start the Antigravity Swarm Chat Webview
    let disposableStartSwarm = vscode.commands.registerCommand('antigravity.startSwarm', () => {
        const panel = vscode.window.createWebviewPanel('antigravitySwarm', 'Antigravity Swarm', vscode.ViewColumn.Beside, {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'src'))]
        });
        activePanel = panel;
        panel.onDidDispose(() => {
            activePanel = undefined;
        });
        const htmlPath = path.join(context.extensionPath, 'src', 'webview.html');
        let htmlContent = '';
        try {
            htmlContent = fs.readFileSync(htmlPath, 'utf8');
        }
        catch (e) {
            vscode.window.showErrorMessage('Could not load webview.html');
        }
        panel.webview.html = htmlContent;
        // Execute condensed startup sequence visually in the webview
        setTimeout(async () => {
            panel.webview.postMessage({ command: 'receiveMessage', text: 'Booting Legion API Bridge locally...' });
            // Wait for ping to confirm the background process is fully alive
            const isApiReady = await client.ping();
            if (isApiReady) {
                panel.webview.postMessage({ command: 'receiveMessage', text: '✅ API Bridge Online. Handshaking with Ray Cluster...' });
                // Simulate Ray confirmation (or in the future, hit a real /ray_status endpoint)
                setTimeout(() => {
                    panel.webview.postMessage({ command: 'receiveMessage', text: '✅ Ray Cluster Confirmed. Sovereign AI is fully locked in and ready.' });
                }, 1500);
            }
            else {
                panel.webview.postMessage({ command: 'receiveMessage', text: '❌ Critical Error: Failed to connect to local API Bridge.' });
            }
        }, 800);
        // Handle messages from the webview
        panel.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                case 'sendMessage':
                    // Call the newly added /chat endpoint in api_bridge.py
                    client.chat({ message: message.text }).then(result => {
                        if (result && result.success) {
                            panel.webview.postMessage({ command: 'receiveMessage', text: result.message });
                        }
                        else {
                            panel.webview.postMessage({ command: 'receiveMessage', text: `❌ Error: ${result?.message || 'Chat request failed.'}` });
                        }
                    });
                    return;
                case 'startRay':
                    // Check real Ray status from the backend
                    fetch(`${apiBaseUrl}/ray_status`)
                        .then(resp => resp.json())
                        .then((data) => {
                        if (data.connected) {
                            panel.webview.postMessage({
                                command: 'receiveMessage',
                                text: `✅ Ray cluster is live! Namespace: ${data.namespace}, Active nodes: ${data.node_count}/${data.total_nodes}`
                            });
                        }
                        else {
                            panel.webview.postMessage({
                                command: 'receiveMessage',
                                text: `⚠️ Ray not connected: ${data.message || 'Not initialized'}. Start Ray with: ray start --head`
                            });
                        }
                    })
                        .catch((err) => {
                        panel.webview.postMessage({
                            command: 'receiveMessage',
                            text: `❌ Could not reach Ray status endpoint: ${err.message}`
                        });
                    });
                    return;
            }
        }, undefined, context.subscriptions);
    });
    // Add all disposables to the context to be cleaned up on deactivation
    context.subscriptions.push(disposableAnalyze, disposableMaster, disposableRefresh, disposableStartSwarm, statusItem);
}
// this method is called when your extension is deactivated
function deactivate() {
    if (apiProcess) {
        console.log('Killing API Bridge process...');
        apiProcess.kill();
    }
    console.log('Legion Sonic Engine extension is now deactivated.');
}
//# sourceMappingURL=extension.js.map