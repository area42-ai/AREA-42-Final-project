// Watch Out - AI Safety & PPE Monitoring System Controller

// Global App State
const state = {
    socket: null,
    stream: null,
    videoElement: null, // Hidden video player for uploaded files and camera stream
    canvasElement: null,
    canvasCtx: null,
    isStreaming: false,      // Webcam active state
    isFilePlaying: false,    // Uploaded file active state
    isRecording: false,
    isMonitoring: false,
    currentView: 'dashboard',
    
    // Safety requirements
    settings: {
        require_helmet: true,
        require_vest: true,
        require_goggles: true
    },
    isBackendConnected: false,
    
    // FPS & Latency stats tracking
    fps: 0,
    fpsIntervalTimer: null,
    drawLoopRequest: null,
    lastFrameTime: Date.now(),
    latency: 0,
    frameCount: 0,
    
    // Snapshots cache in memory (since we don't have a persistent database in frontend-only)
    localAlerts: [],
    localRecordings: [],
    
    // Multi-camera state
    cameras: [],          // Array of { id, name, resolution } from backend
    cameraStreaming: false, // True when MJPEG streams are active
    
    // Mock worker coordinates helper
    mockWorkers: [
        { id: 1, baseAngle: 0, speed: 0.003, scale: 1 },
        { id: 2, baseAngle: Math.PI / 2, speed: 0.002, scale: 0.8 }
    ]
};

// UI Elements Cache
const elements = {
    // Nav Tabs
    menuDashboard: document.getElementById('menu-dashboard'),
    menuRecordings: document.getElementById('menu-recordings'),
    menuAlerts: document.getElementById('menu-alerts'),
    views: {
        dashboard: document.getElementById('view-dashboard'),
        recordings: document.getElementById('view-recordings'),
        alerts: document.getElementById('view-alerts')
    },
    
    // Stats & Clock
    liveClock: document.getElementById('live-clock'),
    statusDot: document.getElementById('system-status-dot'),
    statusText: document.getElementById('system-status-text'),
    statusIndicator: document.getElementById('system-status-indicator'),
    metricSafetyRate: document.getElementById('metric-safety-rate'),
    metricActivePersonnel: document.getElementById('metric-active-personnel'),
    metricViolationsCount: document.getElementById('metric-violations-count'),
    violationsCountBadge: document.getElementById('violations-count-badge'),
    
    // Camera Grid
    cameraGrid: document.getElementById('camera-grid'),
    cameraGridPlaceholder: document.getElementById('camera-grid-placeholder'),
    
    // Legacy Video Viewer (used for file upload flow)
    cameraCanvas: document.getElementById('camera-canvas'),
    sourceVideo: document.getElementById('source-video-element'),
    videoFileInput: document.getElementById('video-file-input'),
    
    // Dashboard Buttons
    btnStartStream: document.getElementById('btn-start-stream'),
    btnPauseStream: document.getElementById('btn-pause-stream'),
    btnUploadTrigger: document.getElementById('btn-upload-trigger'),
    btnRecord: document.getElementById('btn-record'),
    
    // Settings Rule Panels
    reqHelmet: document.getElementById('req-helmet'),
    reqVest: document.getElementById('req-vest'),
    reqGoggles: document.getElementById('req-goggles'),
    
    // Console
    consoleLog: document.getElementById('console-log-stream'),
    consoleFps: document.getElementById('console-fps'),
    consoleLatency: document.getElementById('console-latency'),
    
    // Logs Feeds & Archives
    liveAlertFeed: document.getElementById('live-alert-feed'),
    recordingsGrid: document.getElementById('recordings-grid'),
    alertsGrid: document.getElementById('alerts-grid'),
    btnRefreshRecordings: document.getElementById('btn-refresh-recordings'),
    btnRefreshAlerts: document.getElementById('btn-refresh-alerts'),
    
    // Modal
    modal: document.getElementById('video-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalMediaBody: document.getElementById('modal-media-body'),
    modalClose: document.getElementById('modal-close'),
    
    // Toasts
    toastContainer: document.getElementById('toast-container')
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    setupViewNavigation();
    setupControlsListeners();
    setupClock();
    
    // Setup off-screen elements
    state.canvasElement = document.createElement('canvas');
    state.canvasCtx = state.canvasElement.getContext('2d');
    
    // Synchronize settings panel state
    syncSettingsState();
    
    // Backend is assumed connected since we run from Flask
    state.isBackendConnected = true;
    // Populate with mock archives if no backend is present
    loadMockArchives();
    
    // Fetch cameras from backend and build grid
    fetchAndBuildCameraGrid();
});

// ----------------------------------------------------
// MULTI-CAMERA GRID BUILDER
// ----------------------------------------------------
async function fetchAndBuildCameraGrid() {
    const grid = elements.cameraGrid;
    const placeholder = elements.cameraGridPlaceholder;
    
    try {
        const res = await fetch('/api/cameras');
        const data = await res.json();
        state.cameras = data.cameras || [];
    } catch (err) {
        console.error('Failed to fetch cameras:', err);
        state.cameras = [];
    }
    
    // Remove placeholder
    if (placeholder) placeholder.remove();
    
    if (state.cameras.length === 0) {
        // No cameras found — show empty state
        grid.innerHTML = `
            <div class="camera-grid-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M23 7l-7 5 7 5V7z"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
                <h4>No Cameras Detected</h4>
                <p>No camera devices were found on this machine. Connect a camera and refresh, or upload a video file for analysis.</p>
            </div>
        `;
        updateStatusText('NO CAMERAS', 'red');
        return;
    }
    
    // Apply single-camera class if only 1 camera
    if (state.cameras.length === 1) {
        grid.classList.add('single-camera');
    } else {
        grid.classList.remove('single-camera');
    }
    
    // Build a card for each camera
    grid.innerHTML = '';
    state.cameras.forEach(cam => {
        grid.appendChild(buildCameraCard(cam));
    });
    
    updateStatusText(`${state.cameras.length} CAMERA${state.cameras.length > 1 ? 'S' : ''} READY`, 'green');
    showToast(`${state.cameras.length} camera(s) detected`, 'success');
}

function buildCameraCard(cam) {
    const card = document.createElement('div');
    card.className = 'camera-card';
    card.id = `camera-card-${cam.id}`;
    
    card.innerHTML = `
        <div class="camera-card-header">
            <div class="camera-card-title-group">
                <span class="camera-status-dot" id="cam-dot-${cam.id}"></span>
                <span class="camera-card-name">${cam.name}</span>
                <span class="camera-card-resolution">${cam.resolution}</span>
            </div>
            <div class="camera-card-actions">
                <button title="Fullscreen" onclick="toggleCameraFullscreen(${cam.id})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                    </svg>
                </button>
            </div>
        </div>
        <div class="camera-feed-wrapper" id="cam-feed-${cam.id}">
            <div class="camera-offline-placeholder" id="cam-placeholder-${cam.id}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M23 7l-7 5 7 5V7z"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
                <span>Standby</span>
            </div>
            <div class="camera-feed-overlay">
                <span class="camera-overlay-badge disconnected" id="cam-badge-${cam.id}">OFFLINE</span>
                <span class="camera-overlay-timestamp" id="cam-time-${cam.id}">--:--:--</span>
            </div>
        </div>
    `;
    
    return card;
}

function toggleCameraFullscreen(camId) {
    const feedWrapper = document.getElementById(`cam-feed-${camId}`);
    if (!feedWrapper) return;
    
    if (!document.fullscreenElement) {
        feedWrapper.requestFullscreen().catch(() => {});
    } else {
        document.exitFullscreen();
    }
}

// ----------------------------------------------------
// CORE CLOCK & HEADER METRICS
// ----------------------------------------------------
function setupClock() {
    setInterval(() => {
        const now = new Date();
        elements.liveClock.textContent = now.toTimeString().split(' ')[0];
    }, 1000);
}

function updateHeaderMetrics(activeCount, violationsCount) {
    elements.metricActivePersonnel.textContent = activeCount;
    elements.metricViolationsCount.textContent = violationsCount;
    elements.violationsCountBadge.textContent = violationsCount;
    
    if (activeCount === 0) {
        elements.metricSafetyRate.textContent = "100%";
        elements.metricSafetyRate.className = "stat-val green";
    } else {
        const rate = Math.round(((activeCount - violationsCount) / activeCount) * 100);
        elements.metricSafetyRate.textContent = `${rate}%`;
        
        if (rate >= 90) {
            elements.metricSafetyRate.className = "stat-val green";
        } else if (rate >= 70) {
            elements.metricSafetyRate.className = "stat-val orange";
        } else {
            elements.metricSafetyRate.className = "stat-val red";
        }
    }
}

// ----------------------------------------------------
// TABS NAVIGATION & VIEW ROUTING
// ----------------------------------------------------
function setupViewNavigation() {
    const tabs = [
        { menu: elements.menuDashboard, view: 'dashboard' },
        { menu: elements.menuRecordings, view: 'recordings', loadAction: fetchRecordings },
        { menu: elements.menuAlerts, view: 'alerts', loadAction: fetchAlerts }
    ];
    
    tabs.forEach(tab => {
        tab.menu.addEventListener('click', () => {
            // Remove active style from menu and view
            tabs.forEach(t => {
                t.menu.classList.remove('active');
                elements.views[t.view].classList.remove('active');
            });
            
            // Set clicked active
            tab.menu.classList.add('active');
            elements.views[tab.view].classList.add('active');
            state.currentView = tab.view;
            
            if (tab.loadAction) tab.loadAction();
        });
    });
    
    elements.btnRefreshRecordings.addEventListener('click', fetchRecordings);
    elements.btnRefreshAlerts.addEventListener('click', fetchAlerts);
}

// Synchronize toggles into settings object
function syncSettingsState() {
    state.settings.require_helmet = elements.reqHelmet.checked;
    state.settings.require_vest = elements.reqVest.checked;
    state.settings.require_goggles = elements.reqGoggles.checked;
}

function setupControlsListeners() {
    const checkboxInputs = [
        elements.reqHelmet, elements.reqVest, elements.reqGoggles
    ];
    
    checkboxInputs.forEach(input => {
        if (input) {
            input.addEventListener('change', () => {
                syncSettingsState();
                showToast("Detector settings updated", "warning");
            });
        }
    });
    
    // Webcam Activation
    elements.btnStartStream.addEventListener('click', startWebcam);
    
    // Deactivate Feed
    elements.btnPauseStream.addEventListener('click', stopActiveFeed);
    
    // File upload trigger
    elements.btnUploadTrigger.addEventListener('click', () => {
        elements.videoFileInput.click();
    });
    
    elements.videoFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleUploadedVideoFile(e.target.files[0]);
        }
    });
    
    // Incident Force Reporting



    
    // Record Button
    elements.btnRecord.addEventListener('click', toggleRecordingState);
    


    // Modal Close
    elements.modalClose.addEventListener('click', closeModal);
}

// ----------------------------------------------------
// DRAG & DROP FILE MANAGER
// ----------------------------------------------------
function setupDragAndDrop() {
    const wrapper = elements.videoWrapper;
    
    wrapper.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('drag-over');
    });
    
    wrapper.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');
    });
    
    wrapper.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('video/')) {
            handleUploadedVideoFile(files[0]);
        } else {
            showToast("Invalid file type. Please upload a video.", "danger");
        }
    });
    
    // Click on dropzone also browse
    elements.dropZone.addEventListener('click', () => {
        if (!state.isStreaming && !state.isFilePlaying) {
            elements.videoFileInput.click();
        }
    });
}

// ----------------------------------------------------
// BACKEND REAL-TIME WEBSOCKET LINK
// ----------------------------------------------------
function connectWebSocket() {
    // Replaced by real API fetch
}

function updateStatusText(text, colorClass) {
    elements.statusText.textContent = text;
    elements.statusDot.className = `status-dot ${colorClass}`;
}

// ----------------------------------------------------
// FEED ACTIVATION LOGIC (WEBCAM & FILE)
// ----------------------------------------------------
async function startWebcam() {
    if (state.cameraStreaming || state.isFilePlaying) return;
    
    if (state.cameras.length === 0) {
        showToast("No cameras available to start", "danger");
        return;
    }
    
    // For each camera card, inject an MJPEG <img> stream
    state.cameras.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);
        
        // Remove offline placeholder
        if (placeholder) placeholder.style.display = 'none';
        
        // Create MJPEG img element
        let imgEl = feedWrapper.querySelector('img.mjpeg-feed');
        if (!imgEl) {
            imgEl = document.createElement('img');
            imgEl.className = 'mjpeg-feed';
            imgEl.alt = `Camera ${cam.id} Feed`;
            feedWrapper.insertBefore(imgEl, feedWrapper.firstChild);
        }
        imgEl.src = `/api/stream/${cam.id}`;
        
        // Update status indicators
        if (badge) {
            badge.textContent = 'LIVE';
            badge.classList.remove('disconnected');
        }
        if (dot) dot.className = 'camera-status-dot online';
        if (card) card.classList.add('camera-active');
        
        // Start timestamp update
        if (timeEl) {
            cam._timeInterval = setInterval(() => {
                timeEl.textContent = new Date().toLocaleTimeString();
            }, 1000);
            timeEl.textContent = new Date().toLocaleTimeString();
        }
    });
    
    state.cameraStreaming = true;
    state.isStreaming = true;
    
    // Update controls
    elements.btnStartStream.disabled = true;
    elements.btnPauseStream.disabled = false;
    elements.btnRecord.disabled = false;
    
    updateStatusText(`${state.cameras.length} CAMERA${state.cameras.length > 1 ? 'S' : ''} ACTIVE`, 'green');
    showToast(`${state.cameras.length} camera stream(s) activated`, "success");
}

function handleUploadedVideoFile(file) {
    if (state.isStreaming || state.isFilePlaying || state.cameraStreaming) {
        stopActiveFeed();
    }
    
    const url = URL.createObjectURL(file);
    elements.sourceVideo.srcObject = null;
    elements.sourceVideo.src = url;
    elements.sourceVideo.play();
    
    state.isFilePlaying = true;
    
    // Adjust controls
    elements.btnStartStream.disabled = true;
    elements.btnPauseStream.disabled = false;
    elements.btnRecord.disabled = true;
    
    showToast("Processing video file...", "success");
    elements.consoleLog.innerHTML = '<div style="color: #FBBF24;">{ "status": "system_busy", "message": "Waiting for API response..." }</div>';
    
    // 1. Upload the file
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        
        // 2. Call the analyze API with the uploaded filename
        return fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_name: data.filename, pipeline: "video_frame_pipeline" })
        });
    })
    .then(async response => {
        if (!response.ok) {
            throw new Error('API Request Failed');
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let isFirstLog = true;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (value) {
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (let line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        
                        if (data.type === 'log') {
                            if (isFirstLog) {
                                elements.consoleLog.textContent = '';
                                isFirstLog = false;
                            }
                            elements.consoleLog.textContent += data.message + '\n';
                            elements.consoleLog.scrollTop = elements.consoleLog.scrollHeight;
                        } else if (data.type === 'result') {
                            // Print final JSON result
                            const incidents = data.data.incidents || [];
                            updateConsoleOutput(incidents, data.data.incident_detected);
                            
                            // Update Sidebar
                            if (incidents.length > 0) {
                                incidents.forEach(inc => {
                                    const timeStr = new Date().toLocaleTimeString();
                                    addViolationToSidebar({
                                        id: inc.incident_id,
                                        timestamp: new Date().toLocaleDateString() + ' ' + timeStr,
                                        description: `PPE safety violation: ${inc.violated_items.join(', ')} missing`,
                                        image_path: "",
                                        violators_details: [{ person_id: inc.person_id || 1, missing: inc.violated_items }],
                                        confidence: inc.confidence
                                    });
                                });
                            }
                        } else if (data.type === 'error') {
                            showToast(data.message, "danger");
                        }
                    } catch(e) {
                        console.error("JSON parse error for line:", line, e);
                    }
                }
            }
            if (done) break;
        }
        
        if (buffer.trim()) {
            try {
                const data = JSON.parse(buffer);
                if (data.type === 'log') {
                    if (isFirstLog) {
                        elements.consoleLog.textContent = '';
                        isFirstLog = false;
                    }
                    elements.consoleLog.textContent += data.message + '\n';
                    elements.consoleLog.scrollTop = elements.consoleLog.scrollHeight;
                } else if (data.type === 'result') {
                    const incidents = data.data.incidents || [];
                    updateConsoleOutput(incidents, data.data.incident_detected);
                    if (incidents.length > 0) {
                        incidents.forEach(inc => {
                            const timeStr = new Date().toLocaleTimeString();
                            addViolationToSidebar({
                                id: inc.incident_id,
                                timestamp: new Date().toLocaleDateString() + ' ' + timeStr,
                                description: `PPE safety violation: ${inc.violated_items.join(', ')} missing`,
                                image_path: "",
                                violators_details: [{ person_id: inc.person_id || 1, missing: inc.violated_items }],
                                confidence: inc.confidence
                            });
                        });
                    }
                } else if (data.type === 'error') {
                    showToast(data.message, "danger");
                }
            } catch(e) {
                console.error("JSON parse error for buffer:", buffer, e);
            }
        }
        
        showToast("Analysis Complete", "success");
    })
    .catch(err => {
        console.error("Analysis Error:", err);
        showToast("Error connecting to real API: " + err.message, "danger");
    });
}

function stopActiveFeed() {
    if (!state.isStreaming && !state.isFilePlaying && !state.cameraStreaming) return;
    
    // Stop loops
    if (state.drawLoopRequest) cancelAnimationFrame(state.drawLoopRequest);
    state.drawLoopRequest = null;
    
    // Terminate webcam tracks (legacy)
    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
        state.stream = null;
    }
    
    // Stop video file
    elements.sourceVideo.pause();
    elements.sourceVideo.src = '';
    elements.sourceVideo.srcObject = null;
    
    // Disconnect all MJPEG camera streams
    state.cameras.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);
        
        // Remove MJPEG img
        if (feedWrapper) {
            const imgEl = feedWrapper.querySelector('img.mjpeg-feed');
            if (imgEl) {
                imgEl.src = '';
                imgEl.remove();
            }
        }
        
        // Show offline placeholder again
        if (placeholder) placeholder.style.display = 'flex';
        
        // Reset status indicators
        if (badge) {
            badge.textContent = 'OFFLINE';
            badge.classList.add('disconnected');
        }
        if (dot) dot.className = 'camera-status-dot offline';
        if (card) card.classList.remove('camera-active');
        
        // Clear timestamp interval
        if (cam._timeInterval) {
            clearInterval(cam._timeInterval);
            cam._timeInterval = null;
        }
        
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        if (timeEl) timeEl.textContent = '--:--:--';
    });
    
    state.isStreaming = false;
    state.isFilePlaying = false;
    state.isRecording = false;
    state.cameraStreaming = false;
    
    // Reset control buttons
    elements.btnStartStream.disabled = false;
    elements.btnPauseStream.disabled = true;
    elements.btnRecord.disabled = true;
    elements.btnRecord.classList.remove('recording-active');
    elements.btnRecord.innerHTML = '<span class="record-indicator-dot"></span> Start Monitoring';
    
    updateHeaderMetrics(0, 0);
    updateStatusText(`${state.cameras.length} CAMERA${state.cameras.length > 1 ? 'S' : ''} READY`, 'green');
    
    elements.consoleLog.innerHTML = '{ "status": "system_idle", "message": "Awaiting active camera stream or video file upload..." }';
    
    showToast("All camera streams deactivated", "warning");
}

function drawPlaceholderFeed(text) {
    const ctx = elements.cameraCanvas.getContext('2d');
    const w = elements.cameraCanvas.width = 640;
    const h = elements.cameraCanvas.height = 360;
    
    ctx.fillStyle = "#0B0F19";
    ctx.fillRect(0, 0, w, h);
    
    // Draw crosshair grid lines for industrial vibe
    ctx.strokeStyle = "rgba(255, 85, 0, 0.15)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h);
    ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2);
    ctx.stroke();
    
    // Text
    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    ctx.font = "600 13px 'Outfit', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(text.toUpperCase(), w / 2, h / 2);
}

// ----------------------------------------------------
// PROCESS & RENDER ENGINE LOOPS
// ----------------------------------------------------
function startProcessingLoops() {
    state.lastFrameTime = Date.now();
    state.frameCount = 0;
    
    if (state.drawLoopRequest) cancelAnimationFrame(state.drawLoopRequest);
    state.drawLoopRequest = requestAnimationFrame(renderFrameLoop);
    
    if (!state.isBackendConnected) {
        startLocalSimulationTimer();
    }
}

function startLocalSimulationTimer() {
    if (state.fpsIntervalTimer) clearInterval(state.fpsIntervalTimer);
    
    // FPS calculation ticks every second
    state.fpsIntervalTimer = setInterval(() => {
        state.fps = state.frameCount;
        state.frameCount = 0;
        elements.consoleFps.textContent = `FPS: ${state.fps}`;
        
        // Mock connection check in background
        if (!state.isBackendConnected && Math.random() < 0.1) {
            connectWebSocket();
        }
    }, 1000);
}

function renderFrameLoop() {
    if (!state.isStreaming && !state.isFilePlaying) return;
    
    const canvas = elements.cameraCanvas;
    const ctx = canvas.getContext('2d');
    
    // Draw the raw video frame to the canvas
    if (elements.sourceVideo.readyState >= 2) {
        ctx.drawImage(elements.sourceVideo, 0, 0, canvas.width, canvas.height);
        
        // Add artificial camera overlay details
        ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
        ctx.font = "600 10px 'Fira Code', monospace";
        ctx.textAlign = "left";
        ctx.fillText("CAM_01_FEED // INFERENCE ACTIVE", 20, 25);
    }
    
    // In real API mode, the backend sends the log stream which updates the console.
    // The video plays natively underneath.
    
    state.frameCount++;
    state.drawLoopRequest = requestAnimationFrame(renderFrameLoop);
}

// ----------------------------------------------------
// FRONTEND AI DETECTOR SIMULATION
// ----------------------------------------------------
function simulateDetections(width, height) {
    return []; // No simulation
}

function drawBoundingBoxes(ctx, detections) {
    detections.forEach(d => {
        const [x1, y1, x2, y2] = d.box;
        const w = x2 - x1;
        const h = y2 - y1;
        
        // Color mapping
        const color = d.compliant ? '#10B981' : '#EF4444';
        
        // Outer Person Bounding Box
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x1, y1, w, h);
        
        // Label Banner
        ctx.fillStyle = color;
        const label = `Person #${d.person_id} | ${d.compliant ? 'SECURE' : 'VIOLATION'}`;
        ctx.font = "bold 9px 'Outfit', sans-serif";
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x1 - 1, y1 - 18, textWidth + 12, 18);
        
        ctx.fillStyle = "#FFFFFF";
        ctx.fillText(label, x1 + 6, y1 - 6);
        
        // Draw sub boxes (PPE elements)
        // 1. Head (Helmet)
        if (state.settings.require_helmet) {
            const hx = x1 + w * 0.22;
            const hy = y1 - h * 0.02;
            const hw = w * 0.56;
            const hh = h * 0.14;
            
            ctx.strokeStyle = d.helmet === "Present" ? '#10B981' : '#EF4444';
            ctx.lineWidth = 1;
            ctx.strokeRect(hx, hy, hw, hh);
            
            ctx.fillStyle = ctx.strokeStyle;
            ctx.fillRect(hx, hy, 10, 8);
            ctx.fillStyle = "#FFF";
            ctx.font = "700 7px 'Outfit', sans-serif";
            ctx.fillText("H", hx + 3, hy + 6);
        }
        
        // 2. Eyes (Glasses)
        if (state.settings.require_goggles) {
            const gx = x1 + w * 0.28;
            const gy = y1 + h * 0.12;
            const gw = w * 0.44;
            const gh = h * 0.08;
            
            ctx.strokeStyle = d.goggles === "Present" ? '#10B981' : '#EF4444';
            ctx.lineWidth = 1;
            ctx.strokeRect(gx, gy, gw, gh);
        }
        
        // 3. Torso (Safety Vest)
        if (state.settings.require_vest) {
            const vx = x1 + w * 0.15;
            const vy = y1 + h * 0.26;
            const vw = w * 0.7;
            const vh = h * 0.42;
            
            ctx.strokeStyle = d.vest === "Present" ? '#10B981' : '#EF4444';
            ctx.lineWidth = 1;
            ctx.strokeRect(vx, vy, vw, vh);
            
            ctx.fillStyle = ctx.strokeStyle;
            ctx.fillRect(vx, vy, 10, 8);
            ctx.fillStyle = "#FFF";
            ctx.font = "700 7px 'Outfit', sans-serif";
            ctx.fillText("V", vx + 3, vy + 6);
        }
    });
}

// Send frame to websocket (used in live mode)
function sendFrameToWebSocket() {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) return;
    
    // Capture offscreen
    state.canvasElement.width = 640;
    state.canvasElement.height = 360;
    
    const ctx = state.canvasCtx;
    ctx.drawImage(elements.sourceVideo, 0, 0, 640, 360);
    const b64 = state.canvasElement.toDataURL('image/jpeg', 0.65);
    
    const payload = {
        frame: b64,
        settings: state.settings,
        simulation_mode: false,
        recording: state.isRecording,
        report_now: false
    };
    
    state.socket.send(JSON.stringify(payload));
    state.lastFrameTime = Date.now();
}

// ----------------------------------------------------
// SYSTEM ALERTS & SIDEBAR INCIDENT LIST
// ----------------------------------------------------
let lastAlertedTime = {};

function checkForViolationAlerts(detections) {
    const now = Date.now();
    
    detections.forEach(d => {
        if (!d.compliant) {
            const key = `worker_${d.person_id}_${d.missing.join('_')}`;
            
            // Check throttle: prevent spamming notifications for the same worker violation (5 seconds cooldown)
            if (!lastAlertedTime[key] || now - lastAlertedTime[key] > 5000) {
                lastAlertedTime[key] = now;
                
                // Construct a mock log entry
                const timeStr = new Date().toLocaleTimeString();
                
                // Capture Snapshot image in memory
                const snapshotUrl = elements.cameraCanvas.toDataURL('image/jpeg', 0.5);
                
                const newAlert = {
                    id: 'incident_' + Math.random().toString(36).substr(2, 6),
                    timestamp: new Date().toLocaleDateString() + ' ' + timeStr,
                    description: `PPE safety violation: ${d.missing.join(', ')} missing (Worker #${d.person_id})`,
                    image_path: snapshotUrl,
                    violators_details: [{ person_id: d.person_id, missing: d.missing }],
                    confidence: d.confidence
                };
                
                addViolationToSidebar(newAlert);
                
                // Add to local database
                state.localAlerts.unshift(newAlert);
                showToast(`Incident logged: ${d.missing.join(', ')} missing!`, "danger");
            }
        }
    });
}

function addViolationToSidebar(alert) {
    // Clear empty state text
    if (elements.liveAlertFeed.querySelector('.empty-state-card')) {
        elements.liveAlertFeed.innerHTML = '';
    }
    
    const missingStr = alert.violators_details[0].missing.join(', ');
    const isCritical = alert.violators_details[0].missing.includes('Helmet') || alert.violators_details[0].missing.includes('Safety Vest');
    
    const item = document.createElement('div');
    item.className = `violation-item-card ${isCritical ? 'crit' : ''}`;
    
    item.innerHTML = `
        <div class="violation-item-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            </svg>
        </div>
        <div class="violation-item-details">
            <div class="violation-item-meta">
                <span class="violation-time">${alert.timestamp.split(' ')[1]}</span>
                <span class="violation-conf">${Math.round(alert.confidence * 100)}% Match</span>
            </div>
            <h4 class="violation-title">No ${missingStr}</h4>
            <p class="violation-desc">${alert.description}</p>
            <div class="violation-actions">
                <button class="violation-snap-btn" onclick="openSnapshot('${alert.id}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                        <circle cx="12" cy="13" r="4"/>
                    </svg>
                    View Snapshot
                </button>
            </div>
        </div>
    `;
    
    elements.liveAlertFeed.insertBefore(item, elements.liveAlertFeed.firstChild);
}


// ----------------------------------------------------
// TERMINAL LOG TELEMETRY RENDERER
// ----------------------------------------------------
function updateConsoleOutput(detections, violationDetected) {
    const logData = {
        timestamp: new Date().toISOString(),
        model_inference_engine: "NVIDIA-LLaMa-Vision",
        frame_metrics: {
            fps: state.fps || 15,
            latency_ms: state.latency || 24,
            source_active: state.isStreaming ? "webcam" : (state.isFilePlaying ? "file" : "null")
        },
        site_compliance: {
            secure_state: !violationDetected,
            incident_count: (detections || []).length
        },
        inference_detections: (detections || []).map(d => ({
            incident_id: d.incident_id || "Unknown",
            confidence_match: d.confidence ? parseFloat(d.confidence) : 0.0,
            violated_items: d.violated_items || [],
            status: d.status || "Unknown",
            time_window: d.start_time_sec !== undefined ? `${d.start_time_sec}s - ${d.end_time_sec}s` : "Unknown"
        }))
    };
    
    // Format JSON with syntax highlights
    const rawJson = JSON.stringify(logData, null, 2);
    elements.consoleLog.innerHTML = syntaxHighlightJson(rawJson);
}

function syntaxHighlightJson(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
        var cls = 'json-val-num';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
                return `<span class="${cls}">${match.replace(':', '')}</span>:`;
            } else {
                cls = 'json-val-str';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-val-bool';
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

// ----------------------------------------------------
// FULL SCREEN VIEW MANAGER
// ----------------------------------------------------
function toggleFullscreen() {
    const element = elements.videoWrapper;
    
    if (!document.fullscreenElement) {
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// ----------------------------------------------------
// STREAM RECORDING ACTIONS
// ----------------------------------------------------
let mediaRecorder = null;
let recordedChunks = [];

async function toggleRecordingState() {

    if (!state.isMonitoring) {

        try {

            const response = await fetch("/api/live/start", {
                method: "POST"
            });

            const result = await response.json();

            if (!result.success) {
                showToast(result.error || "Failed to start monitoring", "danger");
                return;
            }

            state.isMonitoring = true;

            elements.btnRecord.classList.add("recording-active");
            elements.btnRecord.textContent = "Stop Monitoring";

            showToast("AI monitoring started", "success");

        } catch (err) {

            console.error(err);
            showToast("Failed to start monitoring", "danger");

        }

    } else {

        try {

            const response = await fetch("/api/live/stop", {
                method: "POST"
            });

            const result = await response.json();

            if (!result.success) {
                showToast(result.error || "Failed to stop monitoring", "danger");
                return;
            }

            state.isMonitoring = false;

            elements.btnRecord.classList.remove("recording-active");
            elements.btnRecord.innerHTML =
                '<span class="record-indicator-dot"></span> Start Monitoring';

            showToast("AI monitoring stopped", "warning");

        } catch (err) {

            console.error(err);
            showToast("Failed to stop monitoring", "danger");

        }

    }

}

// ----------------------------------------------------
// SNAPSHOT & VIDEO MODALS
// ----------------------------------------------------
window.openSnapshot = function(alertId) {
    const alert = state.localAlerts.find(a => a.id === alertId);
    if (!alert) return;
    
    elements.modalTitle.textContent = `Incident Frame Snapshot // ID: ${alert.id.toUpperCase()}`;
    
    // Replace modal media body with image tag
    elements.modalMediaBody.innerHTML = `
        <img src="${alert.image_path}" style="width:100%; aspect-ratio:16/9; object-fit:contain; border-radius:8px; border:1px solid #1E293B;">
    `;
    
    elements.modal.classList.add('active');
};

window.playArchiveVideo = function(filename) {
    elements.modalTitle.textContent = `Video Archive Playback // File: ${filename}`;
    
    // Inject video tag
    elements.modalMediaBody.innerHTML = `
        <video id="modal-video-player" class="modal-video" controls autoplay>
            <source src="/recordings/${filename}" type="video/mp4">
            <!-- Simulated playback loop fallback -->
            Your browser does not support the video tag.
        </video>
    `;
    
    elements.modal.classList.add('active');
};

function closeModal() {
    elements.modal.classList.remove('active');
    // Stop video playback inside modal if playing
    const player = document.getElementById('modal-video-player');
    if (player) player.pause();
    elements.modalMediaBody.innerHTML = '';
}

// ----------------------------------------------------
// STATIC REST API / MOCK DATA SYNC ARCHIVES
// ----------------------------------------------------
async function fetchRecordings() {
    if (state.isBackendConnected) {
        try {
            const response = await fetch('/api/recordings');
            const data = await response.json();
            renderRecordingsList(data);
        } catch (e) {
            renderRecordingsList(state.localRecordings);
        }
    } else {
        renderRecordingsList(state.localRecordings);
    }
}

async function fetchAlerts() {
    if (state.isBackendConnected) {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();
            
            // Combine backend alerts with local manual alerts, sort by timestamp
            const combined = [...state.localAlerts, ...data];
            combined.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            renderAlertsList(combined);
        } catch (e) {
            renderAlertsList(state.localAlerts);
        }
    } else {
        renderAlertsList(state.localAlerts);
    }
}

function renderRecordingsList(data) {
    elements.recordingsGrid.innerHTML = '';
    
    if (data.length === 0) {
        elements.recordingsGrid.innerHTML = `
            <div class="empty-state-card" style="grid-column: 1/-1;">
                <h5>No Recorded Archives Found</h5>
                <p>Use the record stream control to save active camera logs.</p>
            </div>
        `;
        return;
    }
    
    data.forEach(rec => {
        const sizeMB = (rec.size / (1024 * 1024)).toFixed(2);
        const card = document.createElement('div');
        card.className = 'rec-card';
        card.innerHTML = `
            <div class="rec-thumbnail">
                <button class="play-overlay-icon" onclick="playArchiveVideo('${rec.filename}')">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </button>
            </div>
            <div class="rec-card-body">
                <h4 class="rec-name">${rec.filename}</h4>
                <div class="rec-meta">
                    <span>Duration: ${rec.duration}s</span>
                    <span>Size: ${sizeMB} MB</span>
                </div>
                <div class="rec-meta-dt">Timestamp: ${rec.timestamp}</div>
                <div class="rec-actions">
                    <button class="btn-icon" title="Download" onclick="showToast('Downloading started...', 'warning')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                        </svg>
                    </button>
                    <button class="btn-icon del" title="Delete File" onclick="deleteRecording('${rec.filename}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        elements.recordingsGrid.appendChild(card);
    });
}

function renderAlertsList(data) {
    elements.alertsGrid.innerHTML = '';
    
    if (data.length === 0) {
        elements.alertsGrid.innerHTML = `
            <div class="empty-state-card" style="grid-column: 1/-1;">
                <h5>No Reports Available</h5>
                <p>PPE safety compliance violations log file is empty.</p>
            </div>
        `;
        return;
    }
    
    data.forEach(alert => {
        const card = document.createElement('div');
        card.className = 'alert-archive-card';
        card.innerHTML = `
            <img src="${alert.image_path}" class="alert-archive-img" alt="Snapshot Capture" onclick="openSnapshot('${alert.id}')">
            <div class="alert-archive-body">
                <div class="alert-archive-header">
                    <span class="alert-archive-id">${alert.id.toUpperCase()}</span>
                    <span class="alert-archive-time">${alert.timestamp}</span>
                </div>
                <p class="alert-archive-desc">${alert.description}</p>
                <div class="rec-actions">
                    <button class="btn-icon del" title="Delete Log" onclick="deleteAlert('${alert.id}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        elements.alertsGrid.appendChild(card);
    });
}

// Deletion Handlers
window.deleteRecording = async function(filename) {
    if (!confirm(`Are you sure you want to delete recording "${filename}"?`)) return;
    
    if (state.isBackendConnected) {
        try {
            await fetch(`/api/recordings/${filename}`, { method: 'DELETE' });
        } catch (e) {}
    }
    
    state.localRecordings = state.localRecordings.filter(r => r.filename !== filename);
    showToast("File deleted", "warning");
    fetchRecordings();
};

window.deleteAlert = async function(alertId) {
    if (!confirm(`Are you sure you want to delete incident log "${alertId}"?`)) return;
    
    if (state.isBackendConnected) {
        try {
            await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
        } catch (e) {}
    }
    
    state.localAlerts = state.localAlerts.filter(a => a.id !== alertId);
    showToast("Incident report deleted", "warning");
    fetchAlerts();
};

// ----------------------------------------------------
// DYNAMIC MOCK DATA LOADER FOR PROTOTYPE
// ----------------------------------------------------
function loadMockArchives() {
    state.localRecordings = [];
}

// ----------------------------------------------------
// SYSTEM FLOATING TOASTS
// ----------------------------------------------------
function showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'danger' ? 'danger' : (type === 'warning' ? 'warning' : '')}`;
    
    const iconColor = type === 'danger' ? 'var(--color-danger)' : (type === 'warning' ? 'var(--color-warning)' : 'var(--color-success)');
    
    toast.innerHTML = `
        <span style="font-weight: 800; font-family: var(--font-logo); color: ${iconColor};">
            ${type === 'danger' ? '!' : (type === 'warning' ? 'i' : '✓')}
        </span>
        <span class="toast-msg">${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
