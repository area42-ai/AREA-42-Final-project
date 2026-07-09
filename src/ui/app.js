// App state variables
let state = {
    settings: {
        apiUrl: 'https://integrate.api.nvidia.com/v1/chat/completions',
        model: 'meta/llama-3.2-11b-vision-instruct',
        apiKey: '',
        sampleInterval: 1.0,
        confirmationFrames: 2,
        audioAlerts: true
    },
    camera: {
        stream: null,
        isActive: false,
        animationFrameId: null,
        complianceState: 'compliant', // 'compliant' or 'violation'
        violationStreak: 0,
        incidentActive: null // currently tracking open incident
    },
    video: {
        file: null,
        url: null,
        isAnalyzing: false,
        analysisCompleted: false,
        simulatedIncidents: []
    },
    incidents: [], // logged incidents
    stats: {
        violationsToday: 0,
        complianceRate: 100,
        totalChecks: 0,
        compliantChecks: 0
    }
};

// Default constants
const DEFAULT_SETTINGS = {
    apiUrl: 'https://integrate.api.nvidia.com/v1/chat/completions',
    model: 'meta/llama-3.2-11b-vision-instruct',
    apiKey: '',
    sampleInterval: 1.0,
    confirmationFrames: 2,
    audioAlerts: true
};

// UI Elements
const els = {
    // Header
    statLatency: document.getElementById('stat-latency'),
    statViolations: document.getElementById('stat-violations'),
    statCompliance: document.getElementById('stat-compliance'),
    
    // Camera Area
    webcam: document.getElementById('webcam'),
    cameraOverlay: document.getElementById('camera-overlay'),
    cameraPlaceholder: document.getElementById('camera-placeholder'),
    btnStartCamera: document.getElementById('btn-start-camera'),
    btnStopCamera: document.getElementById('btn-stop-camera'),
    cameraStatusText: document.getElementById('camera-status-text'),
    safetyAlarmBanner: document.getElementById('safety-alarm-banner'),
    cameraSimControls: document.getElementById('camera-simulator-controls'),
    btnSimCompliant: document.getElementById('btn-sim-compliant'),
    btnSimViolation: document.getElementById('btn-sim-violation'),
    cameraCard: document.querySelector('.camera-card'),
    btnFullscreenCamera: document.getElementById('btn-fullscreen-camera'),
    btnViewportFullscreen: document.getElementById('btn-viewport-fullscreen'),
    
    // Upload Area
    dropZone: document.getElementById('drop-zone'),
    fileInput: document.getElementById('file-input'),
    uploadedVideo: document.getElementById('uploaded-video'),
    uploadOverlay: document.getElementById('upload-overlay'),
    btnRunAnalysis: document.getElementById('btn-run-analysis'),
    fileInfoBar: document.getElementById('file-info-bar'),
    selectedFileName: document.getElementById('selected-file-name'),
    selectedFileSize: document.getElementById('selected-file-size'),
    btnClearUpload: document.getElementById('btn-clear-upload'),
    uploadStatusText: document.getElementById('upload-status-text'),
    analysisOverlay: document.getElementById('analysis-progress-overlay'),
    progressBarFill: document.getElementById('progress-bar-fill'),
    progressStepText: document.getElementById('progress-step-text'),
    
    // Logs Area
    incidentList: document.getElementById('incident-list'),
    logsEmptyState: document.getElementById('logs-empty-state'),
    logsCounter: document.getElementById('logs-counter'),
    
    // Settings Area
    settingApiUrl: document.getElementById('setting-api-url'),
    settingModel: document.getElementById('setting-model'),
    settingApiKey: document.getElementById('setting-api-key'),
    settingInterval: document.getElementById('setting-interval'),
    settingThreshold: document.getElementById('setting-threshold'),
    settingAudioAlerts: document.getElementById('setting-audio-alerts'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    btnResetSettings: document.getElementById('btn-reset-settings'),
    
    // Evidence Modal
    evidenceModal: document.getElementById('evidence-modal'),
    evidenceImage: document.getElementById('evidence-modal-image'),
    evidenceOverlay: document.getElementById('evidence-modal-overlay'),
    modalCloseBackdrop: document.getElementById('modal-close-backdrop'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    evidenceMetaId: document.getElementById('evidence-meta-id'),
    evidenceMetaTime: document.getElementById('evidence-meta-time'),
    evidenceMetaType: document.getElementById('evidence-meta-type'),
    evidenceMetaDesc: document.getElementById('evidence-meta-desc'),
    
    // Audio
    alertSound: document.getElementById('alert-sound')
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    initSettingsForm();
    setupEventListeners();
    updateDashboardStats();
});

// Load settings from LocalStorage
function loadSettings() {
    const saved = localStorage.getItem('watchout_settings');
    if (saved) {
        try {
            state.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
        } catch (e) {
            state.settings = { ...DEFAULT_SETTINGS };
        }
    } else {
        state.settings = { ...DEFAULT_SETTINGS };
    }
}

// Populate Settings Form inputs
function initSettingsForm() {
    els.settingApiUrl.value = state.settings.apiUrl;
    els.settingModel.value = state.settings.model;
    els.settingApiKey.value = state.settings.apiKey;
    els.settingInterval.value = state.settings.sampleInterval;
    els.settingThreshold.value = state.settings.confirmationFrames;
    els.settingAudioAlerts.checked = state.settings.audioAlerts;
}

// Save Settings to LocalStorage
function saveSettings() {
    state.settings.apiUrl = els.settingApiUrl.value;
    state.settings.model = els.settingModel.value;
    state.settings.apiKey = els.settingApiKey.value;
    state.settings.sampleInterval = parseFloat(els.settingInterval.value) || 1.0;
    state.settings.confirmationFrames = parseInt(els.settingThreshold.value) || 2;
    state.settings.audioAlerts = els.settingAudioAlerts.checked;

    localStorage.setItem('watchout_settings', JSON.stringify(state.settings));
    
    // Visual indicator
    const btn = els.btnSaveSettings;
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<i class="ti ti-check"></i> Configuration Saved!';
    btn.style.backgroundColor = 'var(--color-green)';
    setTimeout(() => {
        btn.innerHTML = origHtml;
        btn.style.backgroundColor = '';
    }, 2000);
}

// Reset Settings
function resetSettings() {
    if (confirm('Reset settings to default pipeline parameters?')) {
        state.settings = { ...DEFAULT_SETTINGS };
        initSettingsForm();
        localStorage.removeItem('watchout_settings');
    }
}

// Setup all event listeners
function setupEventListeners() {
    // Camera triggers
    els.btnStartCamera.addEventListener('click', startWebcam);
    els.btnStopCamera.addEventListener('click', stopWebcam);
    els.btnFullscreenCamera.addEventListener('click', toggleCameraFullscreen);
    els.btnViewportFullscreen.addEventListener('click', toggleCameraFullscreen);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    
    // Simulation state triggers
    els.btnSimCompliant.addEventListener('click', () => setSimState('compliant'));
    els.btnSimViolation.addEventListener('click', () => setSimState('violation'));
    
    // File upload triggers
    els.dropZone.addEventListener('click', () => els.fileInput.click());
    els.fileInput.addEventListener('change', handleFileSelect);
    
    // Drag & Drop event handlers
    els.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        els.dropZone.classList.add('dragover');
    });
    els.dropZone.addEventListener('dragleave', () => {
        els.dropZone.classList.remove('dragover');
    });
    els.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        els.dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Clear video file selection
    els.btnClearUpload.addEventListener('click', clearUploadedVideo);
    
    // Run analysis button
    els.btnRunAnalysis.addEventListener('click', runSimulatedVideoAnalysis);
    
    // Settings forms
    els.btnSaveSettings.addEventListener('click', saveSettings);
    els.btnResetSettings.addEventListener('click', resetSettings);
    
    // Modal controls
    els.btnCloseModal.addEventListener('click', closeModal);
    els.modalCloseBackdrop.addEventListener('click', closeModal);
    
    // Handle esc key for modal
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// Start Webcam Stream
async function startWebcam() {
    els.cameraStatusText.textContent = "Connecting...";
    els.cameraStatusText.className = "status-indicator active";
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            },
            audio: false
        });
        
        state.camera.stream = stream;
        els.webcam.srcObject = stream;
        els.webcam.style.display = 'block';
        els.cameraPlaceholder.style.display = 'none';
        els.btnStartCamera.disabled = true;
        els.btnStopCamera.disabled = false;
        els.btnFullscreenCamera.disabled = false;
        els.btnViewportFullscreen.style.display = 'flex';
        els.cameraSimControls.style.display = 'flex';
        state.camera.isActive = true;
        
        // Start rendering loops
        els.webcam.onloadedmetadata = () => {
            adjustCanvasSize(els.webcam, els.cameraOverlay);
            startCameraLoop();
            els.cameraStatusText.textContent = "Live Stream Active";
            els.cameraStatusText.className = "status-indicator online";
        };
        
        // Re-adjust canvas size on window resize
        window.addEventListener('resize', handleResize);
        
    } catch (err) {
        console.error("Webcam error: ", err);
        alert("Unable to access local webcam. Please check permissions.");
        els.cameraStatusText.textContent = "Connection Failed";
        els.cameraStatusText.className = "status-indicator offline";
    }
}

// Stop Webcam Stream
function stopWebcam() {
    if (state.camera.animationFrameId) {
        cancelAnimationFrame(state.camera.animationFrameId);
        state.camera.animationFrameId = null;
    }
    
    if (state.camera.stream) {
        state.camera.stream.getTracks().forEach(track => track.stop());
        state.camera.stream = null;
    }
    
    els.webcam.srcObject = null;
    els.webcam.style.display = 'none';
    els.cameraPlaceholder.style.display = 'flex';
    els.btnStartCamera.disabled = false;
    els.btnStopCamera.disabled = true;
    els.btnFullscreenCamera.disabled = true;
    els.btnViewportFullscreen.style.display = 'none';
    els.cameraSimControls.style.display = 'none';
    els.safetyAlarmBanner.classList.remove('active');
    els.cameraCard.classList.remove('alarm-active');
    
    // Clear overlay
    const ctx = els.cameraOverlay.getContext('2d');
    ctx.clearRect(0, 0, els.cameraOverlay.width, els.cameraOverlay.height);
    
    state.camera.isActive = false;
    state.camera.violationStreak = 0;
    state.camera.incidentActive = null;
    
    els.cameraStatusText.textContent = "Camera Offline";
    els.cameraStatusText.className = "status-indicator offline";
    
    window.removeEventListener('resize', handleResize);
}

// Toggle Fullscreen on the camera container
function toggleCameraFullscreen() {
    const container = document.getElementById('camera-viewport-container');
    if (!document.fullscreenElement) {
        if (container.requestFullscreen) {
            container.requestFullscreen().catch(err => {
                alert(`Error attempting to enable full-screen mode: ${err.message}`);
            });
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Handle entering / leaving fullscreen
function handleFullscreenChange() {
    const isFullscreen = !!document.fullscreenElement;
    if (isFullscreen && document.fullscreenElement.id === 'camera-viewport-container') {
        els.btnFullscreenCamera.innerHTML = '<i class="ti ti-minimize"></i> Exit Full Screen';
        els.btnViewportFullscreen.innerHTML = '<i class="ti ti-minimize"></i>';
    } else {
        els.btnFullscreenCamera.innerHTML = '<i class="ti ti-maximize"></i> Full Screen';
        els.btnViewportFullscreen.innerHTML = '<i class="ti ti-maximize"></i>';
    }
    
    // Re-adjust canvas size to fit the new dimensions
    setTimeout(() => {
        if (state.camera.isActive) {
            adjustCanvasSize(els.webcam, els.cameraOverlay);
        }
    }, 100);
}

function handleResize() {
    if (state.camera.isActive) {
        adjustCanvasSize(els.webcam, els.cameraOverlay);
    }
    if (state.video.url) {
        adjustCanvasSize(els.uploadedVideo, els.uploadOverlay);
    }
}

// Adjust canvas viewport size to match video element
function adjustCanvasSize(videoEl, canvasEl) {
    canvasEl.width = videoEl.clientWidth;
    canvasEl.height = videoEl.clientHeight;
}

// Camera simulation states (Compliant vs Violation toggle)
function setSimState(simState) {
    state.camera.complianceState = simState;
    if (simState === 'compliant') {
        els.btnSimCompliant.classList.add('active');
        els.btnSimViolation.classList.remove('active');
    } else {
        els.btnSimCompliant.classList.remove('active');
        els.btnSimViolation.classList.add('active');
    }
}

// Camera Loop for Realtime Bounding Boxes and Banners
function startCameraLoop() {
    if (!state.camera.isActive) return;
    
    renderCameraOverlay();
    processCameraSafetyLogic();
    
    state.camera.animationFrameId = requestAnimationFrame(startCameraLoop);
}

// Render bounding boxes over webcam frame
function renderCameraOverlay() {
    const canvas = els.cameraOverlay;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Simulated Person Bounding Box Dimensions
    // Centered, moves slightly with subtle sine wave to look "alive"
    const time = Date.now() * 0.0015;
    const offsetX = Math.sin(time) * 15;
    const offsetY = Math.cos(time * 0.8) * 8;
    
    const boxW = canvas.width * 0.35;
    const boxH = canvas.height * 0.7;
    const boxX = (canvas.width - boxW) / 2 + offsetX;
    const boxY = (canvas.height - boxH) / 2 + offsetY + 20;
    
    // Simulated Head Bounding Box (Helmet Area)
    const headW = boxW * 0.55;
    const headH = boxH * 0.28;
    const headX = boxX + (boxW - headW) / 2;
    const headY = boxY - 10;
    
    const isViolating = state.camera.complianceState === 'violation';
    const color = isViolating ? 'rgba(245, 63, 63, 1)' : 'rgba(0, 180, 42, 1)';
    const colorBg = isViolating ? 'rgba(245, 63, 63, 0.12)' : 'rgba(0, 180, 42, 0.12)';
    
    // 1. Draw Body Box
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]); // dashed border for secondary detection
    ctx.strokeRect(boxX, boxY, boxW, boxH);
    ctx.fillStyle = colorBg;
    ctx.fillRect(boxX, boxY, boxW, boxH);
    
    // Label for Body Box
    ctx.setLineDash([]); // reset dash
    ctx.fillStyle = color;
    ctx.fillRect(boxX, boxY - 22, 120, 22);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '11px Inter, sans-serif';
    ctx.fontWeight = 'bold';
    ctx.fillText('PERSON DETECTED', boxX + 8, boxY - 7);
    
    // 2. Draw Head/Helmet Box
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(headX, headY, headW, headH);
    ctx.fillStyle = isViolating ? 'rgba(245, 63, 63, 0.2)' : 'rgba(0, 180, 42, 0.2)';
    ctx.fillRect(headX, headY, headW, headH);
    
    // Label for Helmet Box
    ctx.fillStyle = color;
    ctx.fillRect(headX, headY - 24, headW, 24);
    
    // Helmet text & icon label
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 11px Inter, sans-serif';
    const labelText = isViolating ? '⚠️ NO HARD HAT' : '🛡️ HARD HAT OK';
    ctx.fillText(labelText, headX + 8, headY - 8);
    
    // Draw crosshair corners on head box for tech aesthetic
    drawCrosshairCorners(ctx, headX, headY, headW, headH, 8, color);
}

function drawCrosshairCorners(ctx, x, y, w, h, len, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    
    // Top-Left
    ctx.beginPath();
    ctx.moveTo(x, y + len);
    ctx.lineTo(x, y);
    ctx.lineTo(x + len, y);
    ctx.stroke();
    
    // Top-Right
    ctx.beginPath();
    ctx.moveTo(x + w - len, y);
    ctx.lineTo(x + w, y);
    ctx.lineTo(x + w, y + len);
    ctx.stroke();
    
    // Bottom-Left
    ctx.beginPath();
    ctx.moveTo(x, y + h - len);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x + len, y + h);
    ctx.stroke();
    
    // Bottom-Right
    ctx.beginPath();
    ctx.moveTo(x + w - len, y + h);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x + w, y + h - len);
    ctx.stroke();
}

// Logic dealing with persistent violations (streak counting, incident logs creation)
function processCameraSafetyLogic() {
    const isViolating = state.camera.complianceState === 'violation';
    
    // Increment global check count (simulated frames)
    state.stats.totalChecks++;
    if (!isViolating) state.stats.compliantChecks++;
    
    if (isViolating) {
        state.camera.violationStreak++;
        
        // Has violation sustained past threshold frames?
        if (state.camera.violationStreak >= state.settings.confirmationFrames) {
            
            // If no active incident is opened, create one
            if (!state.camera.incidentActive) {
                // Flash overlay & trigger banner
                els.safetyAlarmBanner.classList.add('active');
                els.cameraCard.classList.add('alarm-active');
                
                // Sound Alert
                triggerAudioAlert();
                
                // Set pipeline latency mock
                els.statLatency.textContent = Math.round(120 + Math.random() * 45) + ' ms';
                
                // Capture current video frame base64 snapshot
                const evidenceSnapshot = captureVideoFrameBase64(els.webcam);
                
                // Create incident data
                const incidentId = generateIncidentId();
                const newIncident = {
                    id: incidentId,
                    type: 'missing_hard_hat',
                    status: 'open',
                    time: new Date().toLocaleTimeString(),
                    date: new Date().toLocaleDateString(),
                    timestampSeconds: (state.stats.totalChecks * state.settings.sampleInterval).toFixed(1),
                    evidenceFrame: evidenceSnapshot,
                    confidence: 'High (98.4%)',
                    description: 'Safety check fail: worker detected in primary camera zone without visual presence of a safety hard hat. Frame check failed verification.'
                };
                
                state.camera.incidentActive = newIncident;
                state.incidents.push(newIncident);
                
                // Increment stats
                state.stats.violationsToday++;
                
                // Render list
                addIncidentToLogUI(newIncident);
                updateDashboardStats();
            }
        }
    } else {
        // Reset streak
        state.camera.violationStreak = 0;
        
        // If we had an active incident open, resolve it
        if (state.camera.incidentActive) {
            const activeId = state.camera.incidentActive.id;
            resolveIncident(activeId);
            state.camera.incidentActive = null;
            
            els.safetyAlarmBanner.classList.remove('active');
            els.cameraCard.classList.remove('alarm-active');
        }
    }
}

// Sound Alarms
function triggerAudioAlert() {
    if (state.settings.audioAlerts) {
        els.alertSound.currentTime = 0;
        els.alertSound.play().catch(e => console.log('Sound playback prevented: ', e));
    }
}

// Generate base64 screenshot from video elements
function captureVideoFrameBase64(videoEl) {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = 640;
    tempCanvas.height = 360;
    
    const ctx = tempCanvas.getContext('2d');
    // Draw current frame of the video
    ctx.drawImage(videoEl, 0, 0, tempCanvas.width, tempCanvas.height);
    
    // Draw a simulated overlay on the captured thumbnail so evidence shows bounding box
    const isViolating = state.camera.complianceState === 'violation';
    const color = isViolating ? '#F53F3F' : '#00B42A';
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    // Bounding Box around simulated head in 16:9 canvas
    ctx.strokeRect(260, 50, 120, 110);
    ctx.fillStyle = color;
    ctx.fillRect(260, 25, 120, 25);
    
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 9px Arial';
    ctx.fillText(isViolating ? '⚠️ NO HARD HAT' : '🛡️ HARD HAT OK', 268, 41);
    
    return tempCanvas.toDataURL('image/jpeg', 0.8);
}

// Generate incident counter string ID
function generateIncidentId() {
    const index = state.incidents.length + 1;
    return 'INC-' + String(index).padStart(4, '0');
}

// Update counters in Dashboard Header
function updateDashboardStats() {
    els.statViolations.textContent = state.stats.violationsToday;
    
    // Calculate simulated compliance percentage
    if (state.stats.totalChecks > 0) {
        const rate = (state.stats.compliantChecks / state.stats.totalChecks) * 100;
        state.stats.complianceRate = Math.round(rate);
    } else {
        state.stats.complianceRate = 100;
    }
    
    els.statCompliance.textContent = state.stats.complianceRate + '%';
    
    if (state.stats.complianceRate < 80) {
        els.statCompliance.className = 'stat-value text-orange';
    } else {
        els.statCompliance.className = 'stat-value text-green';
    }
    
    els.logsCounter.textContent = state.incidents.length + ' events';
}

// Add Incident element to Scroll Logs
function addIncidentToLogUI(incident) {
    els.logsEmptyState.style.display = 'none';
    
    const item = document.createElement('div');
    item.className = `incident-item ${incident.status === 'open' ? 'violation-active' : ''}`;
    item.id = `ui-incident-${incident.id}`;
    
    item.innerHTML = `
        <div class="incident-thumbnail" onclick="viewEvidence('${incident.id}')">
            <img src="${incident.evidenceFrame}" alt="Incident frame">
            <span class="hover-lens"><i class="ti ti-zoom-in"></i></span>
        </div>
        <div class="incident-content">
            <div class="incident-top-row">
                <span class="incident-id-badge">${incident.id}</span>
                <span class="incident-time">${incident.time}</span>
            </div>
            <span class="incident-title">Missing Safety Helmet</span>
            <p class="incident-desc">${incident.description}</p>
            <div class="incident-footer">
                <span class="incident-status-tag ${incident.status}" id="status-tag-${incident.id}">${incident.status}</span>
                <span class="incident-confidence">${incident.confidence}</span>
                ${incident.status === 'open' ? `<button class="btn-resolve" onclick="resolveIncident('${incident.id}')">Resolve</button>` : ''}
            </div>
        </div>
    `;
    
    els.incidentList.prepend(item);
}

// Resolve logged active violation
window.resolveIncident = function(incidentId) {
    const incident = state.incidents.find(inc => inc.id === incidentId);
    if (incident && incident.status === 'open') {
        incident.status = 'resolved';
        
        // Update list UI
        const tag = document.getElementById(`status-tag-${incidentId}`);
        if (tag) {
            tag.className = 'incident-status-tag resolved';
            tag.textContent = 'resolved';
        }
        
        const card = document.getElementById(`ui-incident-${incidentId}`);
        if (card) {
            card.classList.remove('violation-active');
            // Remove resolve button
            const resolveBtn = card.querySelector('.btn-resolve');
            if (resolveBtn) resolveBtn.remove();
        }
        
        // Check if webcam active incident matches, close it too
        if (state.camera.incidentActive && state.camera.incidentActive.id === incidentId) {
            state.camera.incidentActive = null;
            els.safetyAlarmBanner.classList.remove('active');
            els.cameraCard.classList.remove('alarm-active');
        }
        
        // Re-assess checks metrics
        state.stats.compliantChecks = state.stats.totalChecks; // smooth stats
        updateDashboardStats();
    }
};

// Handle file selection (Standard Browser click select)
function handleFileSelect(e) {
    if (e.target.files && e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

// Process and load video file in HTML player
function handleFile(file) {
    if (!file.type.startsWith('video/')) {
        alert('File format not supported. Please upload a valid MP4 or WebM video file.');
        return;
    }
    
    // Save metadata
    state.video.file = file;
    state.video.url = URL.createObjectURL(file);
    
    els.selectedFileName.textContent = file.name;
    els.selectedFileSize.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    
    // Load player
    els.uploadedVideo.src = state.video.url;
    els.uploadedVideo.style.display = 'block';
    els.dropZone.style.display = 'none';
    els.fileInfoBar.style.display = 'flex';
    els.btnRunAnalysis.disabled = false;
    
    els.uploadedVideo.onloadedmetadata = () => {
        adjustCanvasSize(els.uploadedVideo, els.uploadOverlay);
    };
    
    els.uploadStatusText.textContent = "Video File Loaded";
    els.uploadStatusText.className = "status-indicator online";
}

// Clear selected uploaded video player
function clearUploadedVideo() {
    if (state.video.url) {
        URL.revokeObjectURL(state.video.url);
    }
    
    state.video.file = null;
    state.video.url = null;
    state.video.analysisCompleted = false;
    
    els.uploadedVideo.src = "";
    els.uploadedVideo.style.display = 'none';
    els.dropZone.style.display = 'flex';
    els.fileInfoBar.style.display = 'none';
    els.btnRunAnalysis.disabled = true;
    els.fileInput.value = '';
    
    // Clear canvas
    const ctx = els.uploadOverlay.getContext('2d');
    ctx.clearRect(0, 0, els.uploadOverlay.width, els.uploadOverlay.height);
    
    els.uploadStatusText.textContent = "No File Loaded";
    els.uploadStatusText.className = "status-indicator offline";
}

// Run simulated progressive frame extraction pipeline analysis
function runSimulatedVideoAnalysis() {
    if (!state.video.file) return;
    
    state.video.isAnalyzing = true;
    els.analysisOverlay.classList.add('active');
    
    let progress = 0;
    els.progressBarFill.style.width = '0%';
    
    const steps = [
        { limit: 20, text: 'Extracting video stream frames...' },
        { limit: 45, text: 'Uploading sampled frames to NVIDIA Inference Service...' },
        { limit: 70, text: 'Classifying object bounding boxes (Llama-3.2-Vision)...' },
        { limit: 90, text: 'Evaluating PPE rules and safety compliance sequences...' },
        { limit: 100, text: 'Saving timestamped incident evidence logs...' }
    ];
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        progress += Math.floor(Math.random() * 5) + 3;
        
        if (progress > 100) progress = 100;
        
        els.progressBarFill.style.width = progress + '%';
        
        // Find current descriptive text step
        if (currentStep < steps.length && progress >= steps[currentStep].limit) {
            els.progressStepText.textContent = steps[currentStep].text;
            currentStep++;
        }
        
        if (progress === 100) {
            clearInterval(interval);
            setTimeout(() => {
                finishVideoAnalysis();
            }, 500);
        }
    }, 150);
}

// End of video analysis, mock incident logging
function finishVideoAnalysis() {
    state.video.isAnalyzing = false;
    state.video.analysisCompleted = true;
    els.analysisOverlay.classList.remove('active');
    
    els.uploadStatusText.textContent = "AI Analysis Completed";
    els.uploadStatusText.className = "status-indicator active";
    
    // Reset stats latency mock
    els.statLatency.textContent = Math.round(145 + Math.random() * 20) + ' ms';
    
    // Inject two mock incidents based on video file
    // 1st Incident
    const mockImage1 = generateMockVideoThumbnail(true);
    const id1 = generateIncidentId();
    const incident1 = {
        id: id1,
        type: 'missing_hard_hat',
        status: 'resolved',
        time: new Date(Date.now() - 360000).toLocaleTimeString(),
        date: new Date().toLocaleDateString(),
        timestampSeconds: '3.4s',
        evidenceFrame: mockImage1,
        confidence: 'Medium (87.2%)',
        description: `Visual validation warning: Worker entered scaffold ladder zone missing hard hat. Resolution check passed at 6.8s.`
    };
    state.incidents.push(incident1);
    addIncidentToLogUI(incident1);
    state.stats.violationsToday++;
    
    // 2nd Incident
    const mockImage2 = generateMockVideoThumbnail(false);
    const id2 = generateIncidentId();
    const incident2 = {
        id: id2,
        type: 'missing_hard_hat',
        status: 'resolved',
        time: new Date(Date.now() - 60000).toLocaleTimeString(),
        date: new Date().toLocaleDateString(),
        timestampSeconds: '14.2s',
        evidenceFrame: mockImage2,
        confidence: 'High (95.1%)',
        description: `Visual validation failure: Loading bay supervisor observed working without helmet safety gear. Corrective actions applied.`
    };
    state.incidents.push(incident2);
    addIncidentToLogUI(incident2);
    state.stats.violationsToday++;
    
    // Smooth total check items
    state.stats.totalChecks += 50;
    state.stats.compliantChecks += 46;
    
    updateDashboardStats();
    
    // Start drawing bounding boxes on video playback
    els.uploadedVideo.currentTime = 0;
    els.uploadedVideo.play().catch(e => console.log(e));
    startUploadedVideoRenderingOverlay();
}

// Generate static fallback graphic images inside canvas for mock evidence thumbnails
function generateMockVideoThumbnail(withPersonInRed) {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = 640;
    tempCanvas.height = 360;
    const ctx = tempCanvas.getContext('2d');
    
    // Background gradient representation
    const grad = ctx.createRadialGradient(320, 180, 50, 320, 180, 300);
    grad.addColorStop(0, '#2C3E50');
    grad.addColorStop(1, '#0F2027');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 640, 360);
    
    // Draw wireframe grid representation
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 640; i += 40) {
        ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 360); ctx.stroke();
    }
    for (let i = 0; i < 360; i += 40) {
        ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(640, i); ctx.stroke();
    }
    
    // Draw text representations of scaffolding or work site
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.font = '10px Courier New';
    ctx.fillText('CAM_SOURCE_01_BAY_B', 20, 30);
    ctx.fillText('NVIDIA_MODEL_CLASSIFICATION_LAYER', 20, 50);
    
    // Draw simulated stick worker character
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 4;
    // head
    ctx.beginPath(); ctx.arc(320, 140, 25, 0, Math.PI * 2); ctx.stroke();
    // spine
    ctx.beginPath(); ctx.moveTo(320, 165); ctx.lineTo(320, 260); ctx.stroke();
    // arms
    ctx.beginPath(); ctx.moveTo(280, 190); ctx.lineTo(360, 190); ctx.stroke();
    // legs
    ctx.beginPath(); ctx.moveTo(320, 260); ctx.lineTo(290, 320); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(320, 260); ctx.lineTo(350, 320); ctx.stroke();
    
    const color = withPersonInRed ? '#F53F3F' : '#FF6B00';
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    
    // Head box target
    ctx.strokeRect(285, 105, 70, 70);
    ctx.fillStyle = color;
    ctx.fillRect(285, 80, 70, 25);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 9px Arial';
    ctx.fillText(withPersonInRed ? '🚨 NO HELMET' : '⚠️ WARNING', 291, 96);
    
    return tempCanvas.toDataURL('image/jpeg');
}

// Overlay rendering for Uploaded Video playing
function startUploadedVideoRenderingOverlay() {
    if (!state.video.url || !state.video.analysisCompleted) return;
    
    const render = () => {
        if (els.uploadedVideo.paused || els.uploadedVideo.ended) {
            requestAnimationFrame(render);
            return;
        }
        
        const canvas = els.uploadOverlay;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const time = els.uploadedVideo.currentTime;
        
        // Show simulated bounding boxes at specific intervals to match video
        // e.g. violation active between 2.0s - 7.0s and 13.0s - 18.0s
        const isViolating = (time >= 2.0 && time <= 7.0) || (time >= 13.0 && time <= 18.0);
        
        const color = isViolating ? 'rgba(245, 63, 63, 1)' : 'rgba(0, 180, 42, 1)';
        const text = isViolating ? '⚠️ NO HARD HAT' : '🛡️ HARD HAT OK';
        
        // Render box shifts depending on play duration
        const boxX = canvas.width * 0.4 + Math.sin(time * 0.5) * 50;
        const boxY = canvas.height * 0.2 + Math.cos(time * 0.5) * 20;
        const boxW = canvas.width * 0.2;
        const boxH = canvas.height * 0.5;
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(boxX, boxY, boxW, boxH);
        
        ctx.fillStyle = color;
        ctx.fillRect(boxX, boxY - 24, boxW, 24);
        
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillText(text, boxX + 8, boxY - 8);
        
        drawCrosshairCorners(ctx, boxX, boxY, boxW, boxH, 8, color);
        
        requestAnimationFrame(render);
    };
    
    requestAnimationFrame(render);
}

// Open Evidence Modal View
window.viewEvidence = function(incidentId) {
    const incident = state.incidents.find(inc => inc.id === incidentId);
    if (!incident) return;
    
    els.evidenceMetaId.textContent = incident.id;
    els.evidenceMetaTime.textContent = incident.date + ' ' + incident.time;
    els.evidenceMetaType.textContent = incident.type;
    els.evidenceMetaDesc.textContent = incident.description;
    
    els.evidenceImage.src = incident.evidenceFrame;
    
    els.evidenceModal.classList.add('active');
    
    // Draw bounding box overlay in modal
    // Trigger modal size layout adjustment first
    setTimeout(() => {
        adjustCanvasSize(els.evidenceImage, els.evidenceOverlay);
        drawEvidenceOverlayVisual(els.evidenceOverlay);
    }, 100);
};

function drawEvidenceOverlayVisual(canvasEl) {
    const ctx = canvasEl.getContext('2d');
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    
    // Static overlay box centered to match the snapshot template
    ctx.strokeStyle = '#F53F3F';
    ctx.lineWidth = 3;
    
    const boxW = canvasEl.width * 0.25;
    const boxH = canvasEl.height * 0.35;
    const boxX = (canvasEl.width - boxW) / 2;
    const boxY = (canvasEl.height - boxH) / 2 - 10;
    
    ctx.strokeRect(boxX, boxY, boxW, boxH);
    ctx.fillStyle = '#F53F3F';
    ctx.fillRect(boxX, boxY - 24, boxW, 24);
    
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 11px Inter, sans-serif';
    ctx.fillText('⚠️ NO HARD HAT DETECTED', boxX + 8, boxY - 8);
    
    drawCrosshairCorners(ctx, boxX, boxY, boxW, boxH, 8, '#F53F3F');
}

// Close Modal
function closeModal() {
    els.evidenceModal.classList.remove('active');
}
