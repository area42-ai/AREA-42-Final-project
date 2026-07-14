// Watch Out - AI Safety & PPE Monitoring System Controller

// ----------------------------------------------------
// I18N TRANSLATIONS
// ----------------------------------------------------
const TRANSLATIONS = {
    en: {
        "nav.monitor": "Live Monitor",
        "nav.archive": "Video Archive",
        "nav.incidents": "Incident Reports",
        "sidebar.ppeRules": "PPE Compliance Rules",
        "ppe.helmet": "Hard Hat Protection",
        "ppe.vest": "High-Vis Vest",
        "ppe.glasses": "Safety Glasses",
        "stats.safetyRate": "Safety Rate",
        "stats.personnel": "Active Personnel",
        "stats.violations": "PPE Violations",
        "camera.detecting": "Detecting Cameras...",
        "camera.detectingDesc": "Connecting to backend to enumerate available camera devices.",
        "camera.none": "No Cameras Detected",
        "camera.noneDesc": "No camera devices found. Connect a camera and refresh, or upload a video file.",
        "btn.startMonitoring": "Start Monitoring",
        "btn.stopMonitoring": "Stop Monitoring",
        "btn.uploadVideo": "Upload Video",
        "btn.refresh": "Refresh List",
        "btn.refreshLogs": "Refresh Logs",
        "hazard.title": "Hazard Violation Logs",
        "hazard.safeTitle": "Site Safe & Compliant",
        "hazard.safeDesc": "No active PPE safety violations detected in the environment.",
        "archive.title": "Recorded Archives",
        "archive.subtitle": "Browse and export captured incident recordings and safety video logs.",
        "archive.empty": "No Recorded Archives Found",
        "archive.emptyDesc": "No event segment clips yet. Start monitoring to capture footage.",
        "incidents.title": "Incident Reports & Logs",
        "incidents.subtitle": "Detailed audit records of safety violations and manually reported incidents.",
        "incidents.empty": "No Reports Available",
        "incidents.emptyDesc": "PPE safety compliance violations log is empty.",
        "toast.settingsUpdated": "Detector settings updated",
        "toast.noCameras": "No cameras available to start",
        "toast.camerasActive": "camera stream(s) activated",
        "toast.camerasDeactivated": "All camera streams deactivated",
        "toast.monitoringStarted": "AI monitoring started",
        "toast.monitoringStopped": "AI monitoring stopped",
        "toast.monitoringFailed": "Failed to start monitoring",
        "toast.stopFailed": "Failed to stop monitoring",
        "toast.processingVideo": "Processing video file...",
        "toast.analysisComplete": "Analysis Complete",
        "toast.detected": "cameras detected",
        "toast.incident": "Incident logged",
        "status.initializing": "INITIALIZING",
        "status.ready": "READY",
        "status.active": "ACTIVE",
        "status.noCameras": "NO CAMERAS",
        "status.monitoring": "AI MONITORING",
        "viewSnap": "View Snapshot",
        "deleteFile": "File deleted",
        "deleteReport": "Incident report deleted",
    },
    ru: {
        "nav.monitor": "Живой монитор",
        "nav.archive": "Видеоархив",
        "nav.incidents": "Инциденты",
        "sidebar.ppeRules": "Правила СИЗ",
        "ppe.helmet": "Защитная каска",
        "ppe.vest": "Сигнальный жилет",
        "ppe.glasses": "Защитные очки",
        "stats.safetyRate": "Соответствие",
        "stats.personnel": "Персонал",
        "stats.violations": "Нарушения",
        "camera.detecting": "Поиск камер...",
        "camera.detectingDesc": "Подключение к серверу для обнаружения камер.",
        "camera.none": "Камеры не найдены",
        "camera.noneDesc": "Подключите камеру и обновите страницу, или загрузите видеофайл.",
        "btn.startMonitoring": "Начать мониторинг",
        "btn.stopMonitoring": "Остановить",
        "btn.uploadVideo": "Загрузить видео",
        "btn.refresh": "Обновить список",
        "btn.refreshLogs": "Обновить логи",
        "hazard.title": "Журнал нарушений",
        "hazard.safeTitle": "Зона безопасна",
        "hazard.safeDesc": "Нарушений СИЗ не обнаружено.",
        "archive.title": "Видеоархив",
        "archive.subtitle": "Просматривайте и экспортируйте записи инцидентов.",
        "archive.empty": "Архив пуст",
        "archive.emptyDesc": "Клипы событий отсутствуют. Запустите мониторинг для записи.",
        "incidents.title": "Отчёты об инцидентах",
        "incidents.subtitle": "Детальные записи о нарушениях безопасности.",
        "incidents.empty": "Отчётов нет",
        "incidents.emptyDesc": "Журнал нарушений СИЗ пуст.",
        "toast.settingsUpdated": "Настройки детектора обновлены",
        "toast.noCameras": "Нет доступных камер",
        "toast.camerasActive": "потока камер активированы",
        "toast.camerasDeactivated": "Все потоки камер остановлены",
        "toast.monitoringStarted": "ИИ-мониторинг запущен",
        "toast.monitoringStopped": "ИИ-мониторинг остановлен",
        "toast.monitoringFailed": "Не удалось запустить мониторинг",
        "toast.stopFailed": "Не удалось остановить мониторинг",
        "toast.processingVideo": "Обработка видеофайла...",
        "toast.analysisComplete": "Анализ завершён",
        "toast.detected": "камер обнаружено",
        "toast.incident": "Инцидент зафиксирован",
        "status.initializing": "ИНИЦИАЛИЗАЦИЯ",
        "status.ready": "ГОТОВО",
        "status.active": "АКТИВНО",
        "status.noCameras": "НЕТ КАМЕР",
        "status.monitoring": "ИИ-МОНИТОРИНГ",
        "viewSnap": "Открыть снимок",
        "deleteFile": "Файл удалён",
        "deleteReport": "Отчёт удалён",
    },
    az: {
        "nav.monitor": "Canlı monitor",
        "nav.archive": "Video arxivi",
        "nav.incidents": "Hadisə hesabatları",
        "sidebar.ppeRules": "FMM uyğunluq qaydaları",
        "ppe.helmet": "Qoruyucu dəbilqə",
        "ppe.vest": "Siqnal jimki",
        "ppe.glasses": "Qoruyucu eynək",
        "stats.safetyRate": "Uyğunluq",
        "stats.personnel": "Personal",
        "stats.violations": "Pozuntular",
        "camera.detecting": "Kameralar axtarılır...",
        "camera.detectingDesc": "Kamera cihazlarını müəyyən etmək üçün server ilə əlaqə.",
        "camera.none": "Kamera tapılmadı",
        "camera.noneDesc": "Kamera bağlayın və yeniləyin, ya da video faylı yükləyin.",
        "btn.startMonitoring": "Monitorinqə başla",
        "btn.stopMonitoring": "Dayandır",
        "btn.uploadVideo": "Video yüklə",
        "btn.refresh": "Siyahını yenilə",
        "btn.refreshLogs": "Qeydləri yenilə",
        "hazard.title": "Pozuntu jurnalı",
        "hazard.safeTitle": "Zona təhlükəsizdir",
        "hazard.safeDesc": "FMM pozuntusu aşkar edilmədi.",
        "archive.title": "Video arxivi",
        "archive.subtitle": "Hadisə qeydlərini baxın və ixrac edin.",
        "archive.empty": "Arxiv boşdur",
        "archive.emptyDesc": "Hadisə klipləri yoxdur. Qeyd etmək üçün monitorinqə başlayın.",
        "incidents.title": "Hadisə hesabatları",
        "incidents.subtitle": "Təhlükəsizlik pozuntularının ətraflı qeydləri.",
        "incidents.empty": "Hesabat yoxdur",
        "incidents.emptyDesc": "FMM uyğunluq pozuntuları jurnalı boşdur.",
        "toast.settingsUpdated": "Detektor parametrləri yeniləndi",
        "toast.noCameras": "İstifadə oluna bilən kamera yoxdur",
        "toast.camerasActive": "kamera axını aktivləşdirildi",
        "toast.camerasDeactivated": "Bütün kamera axınları dayandırıldı",
        "toast.monitoringStarted": "AI monitorinqi başladı",
        "toast.monitoringStopped": "AI monitorinqi dayandırıldı",
        "toast.monitoringFailed": "Monitorinqi başlatmaq alınmadı",
        "toast.stopFailed": "Monitorinqi dayandırmaq alınmadı",
        "toast.processingVideo": "Video faylı emal edilir...",
        "toast.analysisComplete": "Analiz tamamlandı",
        "toast.detected": "kamera aşkar edildi",
        "toast.incident": "Hadisə qeydə alındı",
        "status.initializing": "İNİSİALİZASİYA",
        "status.ready": "HAZIR",
        "status.active": "AKTİV",
        "status.noCameras": "KAMERA YOX",
        "status.monitoring": "AI MONİTORİNQ",
        "viewSnap": "Şəkilə bax",
        "deleteFile": "Fayl silindi",
        "deleteReport": "Hesabat silindi",
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function t(key) {
    return (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) || key;
}

function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    document.querySelectorAll('[data-lang]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        const val = TRANSLATIONS[lang] && TRANSLATIONS[lang][key];
        if (val) el.textContent = val;
    });
    // Update dynamic elements that were set via JS
    if (elements && elements.consoleLog) {
        if (!state.isStreaming && !state.isFilePlaying && !state.cameraStreaming) {
            elements.consoleLog.textContent = '{ "status": "system_idle", "message": "Awaiting active camera stream or video file upload..." }';
        }
    }
}

// ----------------------------------------------------
// GLOBAL APP STATE
// ----------------------------------------------------
const state = {
    stream: null,
    videoElement: null,
    canvasElement: null,
    canvasCtx: null,
    isStreaming: false,
    isFilePlaying: false,
    isMonitoring: false,
    currentView: 'dashboard',
    settings: {
        require_helmet: true,
        require_vest: true,
        require_goggles: true
    },
    isBackendConnected: false,
    fps: 0,
    fpsIntervalTimer: null,
    drawLoopRequest: null,
    lastFrameTime: Date.now(),
    latency: 0,
    frameCount: 0,
    localAlerts: [],
    localRecordings: [],
    cameras: [],
    cameraStreaming: false,
    shownAlertIds: new Set(),
};

// UI Elements Cache
const elements = {
    menuDashboard: document.getElementById('menu-dashboard'),
    menuRecordings: document.getElementById('menu-recordings'),
    menuAlerts: document.getElementById('menu-alerts'),
    views: {
        dashboard: document.getElementById('view-dashboard'),
        recordings: document.getElementById('view-recordings'),
        alerts: document.getElementById('view-alerts')
    },
    liveClock: document.getElementById('live-clock'),
    statusDot: document.getElementById('system-status-dot'),
    statusText: document.getElementById('system-status-text'),
    statusIndicator: document.getElementById('system-status-indicator'),
    metricSafetyRate: document.getElementById('metric-safety-rate'),
    metricActivePersonnel: document.getElementById('metric-active-personnel'),
    metricViolationsCount: document.getElementById('metric-violations-count'),
    violationsCountBadge: document.getElementById('violations-count-badge'),
    cameraGrid: document.getElementById('camera-grid'),
    cameraGridPlaceholder: document.getElementById('camera-grid-placeholder'),
    cameraCanvas: document.getElementById('camera-canvas'),
    sourceVideo: document.getElementById('source-video-element'),
    videoFileInput: document.getElementById('video-file-input'),
    btnStartStream: document.getElementById('btn-start-stream'),
    btnPauseStream: document.getElementById('btn-pause-stream'),
    btnUploadTrigger: document.getElementById('btn-upload-trigger'),
    reqHelmet: document.getElementById('req-helmet'),
    reqVest: document.getElementById('req-vest'),
    reqGoggles: document.getElementById('req-goggles'),
    consoleLog: document.getElementById('console-log-stream'),
    consoleFps: document.getElementById('console-fps'),
    consoleLatency: document.getElementById('console-latency'),
    liveAlertFeed: document.getElementById('live-alert-feed'),
    recordingsGrid: document.getElementById('recordings-grid'),
    alertsGrid: document.getElementById('alerts-grid'),
    btnRefreshRecordings: document.getElementById('btn-refresh-recordings'),
    btnRefreshAlerts: document.getElementById('btn-refresh-alerts'),
    modal: document.getElementById('video-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalMediaBody: document.getElementById('modal-media-body'),
    modalClose: document.getElementById('modal-close'),
    toastContainer: document.getElementById('toast-container'),
    sidebar: document.getElementById('sidebar'),
    btnSidebarToggle: document.getElementById('btn-sidebar-toggle'),
    btnThemeToggle: document.getElementById('btn-theme-toggle'),
    themeIconSun: document.getElementById('theme-icon-sun'),
    themeIconMoon: document.getElementById('theme-icon-moon'),
};

// ----------------------------------------------------
// INITIALIZATION
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    applyLanguage(currentLang);
    setupViewNavigation();
    setupControlsListeners();
    setupClock();
    setupThemeToggle();
    setupSidebarToggle();
    setupLanguageSwitcher();

    state.canvasElement = document.createElement('canvas');
    state.canvasCtx = state.canvasElement.getContext('2d');
    syncSettingsState();

    state.isBackendConnected = true;
    fetchAndBuildCameraGrid();
});

// ----------------------------------------------------
// THEME
// ----------------------------------------------------
function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function updateThemeIcon(theme) {
    if (!elements.themeIconSun || !elements.themeIconMoon) return;
    if (theme === 'dark') {
        elements.themeIconSun.style.display = 'none';
        elements.themeIconMoon.style.display = 'block';
    } else {
        elements.themeIconSun.style.display = 'block';
        elements.themeIconMoon.style.display = 'none';
    }
}

function setupThemeToggle() {
    if (!elements.btnThemeToggle) return;
    elements.btnThemeToggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(next);
    });
}

// ----------------------------------------------------
// SIDEBAR COLLAPSE
// ----------------------------------------------------
function setupSidebarToggle() {
    if (!elements.btnSidebarToggle) return;
    const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (collapsed) elements.sidebar.classList.add('collapsed');

    elements.btnSidebarToggle.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', elements.sidebar.classList.contains('collapsed'));
    });
}

// ----------------------------------------------------
// LANGUAGE SWITCHER
// ----------------------------------------------------
function setupLanguageSwitcher() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => applyLanguage(btn.dataset.lang));
    });
}

// ----------------------------------------------------
// MULTI-CAMERA GRID
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

    if (placeholder) placeholder.remove();

    if (state.cameras.length === 0) {
        grid.innerHTML = `
            <div class="camera-grid-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M23 7l-7 5 7 5V7z"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
                <h4>${t('camera.none')}</h4>
                <p>${t('camera.noneDesc')}</p>
            </div>
        `;
        updateStatusText(t('status.noCameras'), 'red');
        return;
    }

    if (state.cameras.length === 1) {
        grid.classList.add('single-camera');
    } else {
        grid.classList.remove('single-camera');
    }

    grid.innerHTML = '';
    state.cameras.forEach(cam => grid.appendChild(buildCameraCard(cam)));

    const countLabel = `${state.cameras.length} ${t('status.ready')}`;
    updateStatusText(countLabel, 'green');
    showToast(`${state.cameras.length} ${t('toast.detected')}`, 'success');
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
// CLOCK & HEADER METRICS
// ----------------------------------------------------
function setupClock() {
    setInterval(() => {
        elements.liveClock.textContent = new Date().toTimeString().split(' ')[0];
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
        elements.metricSafetyRate.className = rate >= 90 ? "stat-val green" : rate >= 70 ? "stat-val orange" : "stat-val red";
    }
}

function updateHeaderMetricsFromAlerts(alerts) {
    const violations = alerts.length;
    updateHeaderMetrics(violations > 0 ? violations : 0, violations);
}

// ----------------------------------------------------
// TABS NAVIGATION
// ----------------------------------------------------
function setupViewNavigation() {
    const tabs = [
        { menu: elements.menuDashboard, view: 'dashboard' },
        { menu: elements.menuRecordings, view: 'recordings', loadAction: fetchRecordings },
        { menu: elements.menuAlerts, view: 'alerts', loadAction: fetchAlerts }
    ];

    tabs.forEach(tab => {
        tab.menu.addEventListener('click', () => {
            tabs.forEach(t => {
                t.menu.classList.remove('active');
                elements.views[t.view].classList.remove('active');
            });
            tab.menu.classList.add('active');
            elements.views[tab.view].classList.add('active');
            state.currentView = tab.view;
            if (tab.loadAction) tab.loadAction();
        });
    });

    elements.btnRefreshRecordings.addEventListener('click', fetchRecordings);
    elements.btnRefreshAlerts.addEventListener('click', fetchAlerts);
}

function syncSettingsState() {
    state.settings.require_helmet = elements.reqHelmet.checked;
    state.settings.require_vest = elements.reqVest.checked;
    state.settings.require_goggles = elements.reqGoggles.checked;
}

function setupControlsListeners() {
    [elements.reqHelmet, elements.reqVest, elements.reqGoggles].forEach(input => {
        if (input) input.addEventListener('change', () => {
            syncSettingsState();
            showToast(t('toast.settingsUpdated'), "warning");
        });
    });

    elements.btnStartStream.addEventListener('click', startMonitoring);
    elements.btnPauseStream.addEventListener('click', stopMonitoring);

    elements.btnUploadTrigger.addEventListener('click', () => elements.videoFileInput.click());
    elements.videoFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleUploadedVideoFile(e.target.files[0]);
    });

    elements.modalClose.addEventListener('click', closeModal);
}

// ----------------------------------------------------
// UNIFIED START / STOP  (cameras + AI pipeline)
// ----------------------------------------------------
async function startMonitoring() {
    if (state.cameraStreaming || state.isFilePlaying) return;

    if (state.cameras.length === 0) {
        showToast(t('toast.noCameras'), "danger");
        return;
    }

    // 1. Start MJPEG preview for each camera
    state.cameras.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);

        if (placeholder) placeholder.style.display = 'none';

        let imgEl = feedWrapper.querySelector('img.mjpeg-feed');
        if (!imgEl) {
            imgEl = document.createElement('img');
            imgEl.className = 'mjpeg-feed';
            imgEl.alt = `Camera ${cam.id} Feed`;
            feedWrapper.insertBefore(imgEl, feedWrapper.firstChild);
        }
        imgEl.src = `/api/stream/${cam.id}`;

        if (badge) { badge.textContent = 'LIVE'; badge.classList.remove('disconnected'); }
        if (dot) dot.className = 'camera-status-dot online';
        if (card) card.classList.add('camera-active');

        if (timeEl) {
            cam._timeInterval = setInterval(() => {
                timeEl.textContent = new Date().toLocaleTimeString();
            }, 1000);
            timeEl.textContent = new Date().toLocaleTimeString();
        }
    });

    state.cameraStreaming = true;
    state.isStreaming = true;

    elements.btnStartStream.disabled = true;
    elements.btnPauseStream.disabled = false;

    updateStatusText(t('status.monitoring'), 'orange');
    showToast(`${state.cameras.length} ${t('toast.camerasActive')}`, "success");

    // 2. Start AI pipeline
    try {
        const response = await fetch("/api/live/start", { method: "POST" });
        const result = await response.json();
        if (result.success) {
            state.isMonitoring = true;
            showToast(t('toast.monitoringStarted'), "success");
            updateConsoleForMonitoring();
            startAlertPolling();
        } else {
            showToast(result.error || t('toast.monitoringFailed'), "danger");
        }
    } catch (err) {
        console.error(err);
        showToast(t('toast.monitoringFailed'), "danger");
    }
}

async function stopMonitoring() {
    // 1. Stop MJPEG streams
    if (state.drawLoopRequest) cancelAnimationFrame(state.drawLoopRequest);
    state.drawLoopRequest = null;

    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
        state.stream = null;
    }

    elements.sourceVideo.pause();
    elements.sourceVideo.src = '';
    elements.sourceVideo.srcObject = null;

    state.cameras.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);

        if (feedWrapper) {
            const imgEl = feedWrapper.querySelector('img.mjpeg-feed');
            if (imgEl) { imgEl.src = ''; imgEl.remove(); }
        }

        if (placeholder) placeholder.style.display = 'flex';
        if (badge) { badge.textContent = 'OFFLINE'; badge.classList.add('disconnected'); }
        if (dot) dot.className = 'camera-status-dot offline';
        if (card) card.classList.remove('camera-active');

        if (cam._timeInterval) { clearInterval(cam._timeInterval); cam._timeInterval = null; }
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        if (timeEl) timeEl.textContent = '--:--:--';
    });

    state.isStreaming = false;
    state.isFilePlaying = false;
    state.cameraStreaming = false;

    elements.btnStartStream.disabled = false;
    elements.btnPauseStream.disabled = true;

    updateHeaderMetrics(0, 0);
    const camCount = state.cameras.length;
    updateStatusText(`${camCount} ${t('status.ready')}`, 'green');
    elements.consoleLog.textContent = '{ "status": "system_idle", "message": "Awaiting active camera stream or video file upload..." }';
    showToast(t('toast.camerasDeactivated'), "warning");

    // 2. Stop AI pipeline
    if (state.isMonitoring) {
        try {
            const response = await fetch("/api/live/stop", { method: "POST" });
            const result = await response.json();
            if (result.success) {
                state.isMonitoring = false;
                showToast(t('toast.monitoringStopped'), "warning");
            } else {
                showToast(result.error || t('toast.stopFailed'), "danger");
            }
        } catch (err) {
            console.error(err);
            showToast(t('toast.stopFailed'), "danger");
        }
    }

    stopAlertPolling();
}

// ----------------------------------------------------
// ALERT AUTO-POLLING
// ----------------------------------------------------
let _alertPollInterval = null;

function startAlertPolling() {
    if (_alertPollInterval) return;
    _alertPollInterval = setInterval(pollAndUpdateSidebar, 5000);
}

function stopAlertPolling() {
    if (_alertPollInterval) { clearInterval(_alertPollInterval); _alertPollInterval = null; }
}

async function pollAndUpdateSidebar() {
    try {
        const res = await fetch('/api/alerts');
        if (!res.ok) return;
        const alerts = await res.json();
        let newCount = 0;
        for (const alert of alerts) {
            if (!state.shownAlertIds.has(alert.id) && alert.id) {
                state.shownAlertIds.add(alert.id);
                addViolationToSidebar(alert);
                newCount++;
            }
        }
        if (newCount > 0) {
            updateHeaderMetricsFromAlerts(alerts);
        }
    } catch {}
}

// ----------------------------------------------------
// CONSOLE OUTPUT DURING MONITORING
// ----------------------------------------------------
function updateConsoleForMonitoring() {
    const logData = {
        status: "pipeline_active",
        engine: "Nemotron-VLM + Gemma",
        message: "Event-driven live stream pipeline running. Awaiting PPE violation events...",
        camera_source: state.cameras.length > 0 ? `Camera ${state.cameras[0].id} (${state.cameras[0].resolution})` : "unknown",
    };
    elements.consoleLog.innerHTML = syntaxHighlightJson(JSON.stringify(logData, null, 2));
}

// ----------------------------------------------------
// VIDEO FILE UPLOAD & ANALYSIS
// ----------------------------------------------------
function handleUploadedVideoFile(file) {
    if (state.isStreaming || state.isFilePlaying || state.cameraStreaming) {
        stopMonitoring();
    }

    const url = URL.createObjectURL(file);
    elements.sourceVideo.srcObject = null;
    elements.sourceVideo.src = url;
    elements.sourceVideo.play();
    state.isFilePlaying = true;

    elements.btnStartStream.disabled = true;
    elements.btnPauseStream.disabled = false;

    showToast(t('toast.processingVideo'), "success");
    elements.consoleLog.innerHTML = '<div style="color: #FBBF24;">{ "status": "system_busy", "message": "Waiting for API response..." }</div>';

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/upload', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            return fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_name: data.filename, pipeline: "video_frame_pipeline" })
            });
        })
        .then(async response => {
            if (!response.ok) throw new Error('API Request Failed');
            const result = await response.json();
            const incidents = (result.data && result.data.incidents) || [];
            updateConsoleOutput(incidents, result.data && result.data.incident_detected);
            if (incidents.length > 0) {
                incidents.forEach(inc => {
                    addViolationToSidebar({
                        id: inc.incident_id,
                        timestamp: new Date().toLocaleDateString() + ' ' + new Date().toLocaleTimeString(),
                        description: `PPE violation: ${(inc.violated_items || []).join(', ')} missing`,
                        image_path: "",
                        violators_details: [{ person_id: inc.person_id || 1, missing: inc.violated_items || [] }],
                        confidence: inc.confidence || 0.85
                    });
                });
            }
            showToast(t('toast.analysisComplete'), "success");
        })
        .catch(err => {
            console.error("Analysis Error:", err);
            showToast("Error: " + err.message, "danger");
        });
}

// ----------------------------------------------------
// VIOLATION SIDEBAR
// ----------------------------------------------------
let lastAlertedTime = {};

function addViolationToSidebar(alert) {
    if (elements.liveAlertFeed.querySelector('.empty-state-card')) {
        elements.liveAlertFeed.innerHTML = '';
    }

    const missingArr = (alert.violators_details && alert.violators_details[0] && alert.violators_details[0].missing) || [];
    const missingStr = missingArr.join(', ') || 'PPE';
    const isCritical = missingArr.some(m => m.toLowerCase().includes('hard_hat') || m.toLowerCase().includes('helmet') || m.toLowerCase().includes('vest'));
    const timeStr = alert.timestamp ? alert.timestamp.split('T')[1]?.slice(0, 8) || alert.timestamp.split(' ')[1] || '' : '';

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
                <span class="violation-time">${timeStr}</span>
                <span class="violation-conf">${Math.round((alert.confidence || 0.9) * 100)}% Match</span>
            </div>
            <h4 class="violation-title">No ${missingStr.replace(/_/g, ' ')}</h4>
            <p class="violation-desc">${alert.description || ''}</p>
            ${alert.image_path ? `
            <div class="violation-actions">
                <button class="violation-snap-btn" onclick="openSnapshotByUrl('${alert.image_path}', '${alert.id}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                        <circle cx="12" cy="13" r="4"/>
                    </svg>
                    ${t('viewSnap')}
                </button>
            </div>` : ''}
        </div>
    `;

    elements.liveAlertFeed.insertBefore(item, elements.liveAlertFeed.firstChild);
    state.localAlerts.unshift(alert);

    if (isCritical) {
        showToast(`${t('toast.incident')}: ${missingStr.replace(/_/g, ' ')}!`, "danger");
    }
}

// ----------------------------------------------------
// CONSOLE OUTPUT
// ----------------------------------------------------
function updateConsoleOutput(detections, violationDetected) {
    const logData = {
        timestamp: new Date().toISOString(),
        engine: "Nemotron-VLM + Gemma",
        site_compliance: {
            secure: !violationDetected,
            incident_count: (detections || []).length
        },
        incidents: (detections || []).map(d => ({
            incident_id: d.incident_id || "unknown",
            confidence: d.confidence ? parseFloat(d.confidence) : 0.0,
            violated_items: d.violated_items || [],
            status: d.status || "unknown",
        }))
    };
    elements.consoleLog.innerHTML = syntaxHighlightJson(JSON.stringify(logData, null, 2));
}

function syntaxHighlightJson(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
        let cls = 'json-val-num';
        if (/^"/.test(match)) {
            cls = /:$/.test(match) ? 'json-key' : 'json-val-str';
            if (cls === 'json-key') return `<span class="${cls}">${match.slice(0, -1)}</span>:`;
        } else if (/true|false/.test(match)) {
            cls = 'json-val-bool';
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

// ----------------------------------------------------
// STATUS HELPERS
// ----------------------------------------------------
function updateStatusText(text, colorClass) {
    elements.statusText.textContent = text;
    elements.statusDot.className = `status-dot ${colorClass}`;
}

// ----------------------------------------------------
// MODAL
// ----------------------------------------------------
window.openSnapshotByUrl = function(imageUrl, alertId) {
    elements.modalTitle.textContent = `Incident Frame // ID: ${alertId.toUpperCase()}`;
    elements.modalMediaBody.innerHTML = `
        <img src="${imageUrl}" style="width:100%;aspect-ratio:16/9;object-fit:contain;border-radius:8px;border:1px solid #1E293B;">
    `;
    elements.modal.classList.add('active');
};

window.openSnapshot = function(alertId) {
    const alert = state.localAlerts.find(a => a.id === alertId);
    if (!alert || !alert.image_path) return;
    openSnapshotByUrl(alert.image_path, alertId);
};

window.playArchiveVideo = function(url, filename) {
    elements.modalTitle.textContent = `Video Archive // ${filename}`;
    elements.modalMediaBody.innerHTML = `
        <video id="modal-video-player" class="modal-video" controls autoplay>
            <source src="${url}" type="video/mp4">
        </video>
    `;
    elements.modal.classList.add('active');
};

function closeModal() {
    elements.modal.classList.remove('active');
    const player = document.getElementById('modal-video-player');
    if (player) player.pause();
    elements.modalMediaBody.innerHTML = '';
}

// ----------------------------------------------------
// RECORDINGS & ALERTS TABS
// ----------------------------------------------------
async function fetchRecordings() {
    try {
        const response = await fetch('/api/recordings');
        const data = await response.json();
        renderRecordingsList(Array.isArray(data) ? data : []);
    } catch (e) {
        renderRecordingsList(state.localRecordings);
    }
}

async function fetchAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        const combined = [...state.localAlerts.filter(a => !data.find(b => b.id === a.id)), ...data];
        combined.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        renderAlertsList(combined);
    } catch (e) {
        renderAlertsList(state.localAlerts);
    }
}

function renderRecordingsList(data) {
    elements.recordingsGrid.innerHTML = '';

    if (!data || data.length === 0) {
        elements.recordingsGrid.innerHTML = `
            <div class="empty-state-card" style="grid-column:1/-1;">
                <h5>${t('archive.empty')}</h5>
                <p>${t('archive.emptyDesc')}</p>
            </div>
        `;
        return;
    }

    data.forEach(rec => {
        const sizeMB = (rec.size / (1024 * 1024)).toFixed(2);
        const videoUrl = rec.url || `/data/${rec.path}`;
        const card = document.createElement('div');
        card.className = 'rec-card';
        card.innerHTML = `
            <div class="rec-thumbnail">
                <button class="play-overlay-icon" onclick="playArchiveVideo('${videoUrl}', '${rec.filename}')">
                    <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                </button>
            </div>
            <div class="rec-card-body">
                <h4 class="rec-name">${rec.filename}</h4>
                <div class="rec-meta">
                    <span>Size: ${sizeMB} MB</span>
                </div>
                <div class="rec-meta-dt">Timestamp: ${rec.timestamp}</div>
                <div class="rec-actions">
                    <a class="btn-icon" href="${videoUrl}" download="${rec.filename}" title="Download">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                        </svg>
                    </a>
                </div>
            </div>
        `;
        elements.recordingsGrid.appendChild(card);
    });
}

function renderAlertsList(data) {
    elements.alertsGrid.innerHTML = '';

    if (!data || data.length === 0) {
        elements.alertsGrid.innerHTML = `
            <div class="empty-state-card" style="grid-column:1/-1;">
                <h5>${t('incidents.empty')}</h5>
                <p>${t('incidents.emptyDesc')}</p>
            </div>
        `;
        return;
    }

    data.forEach(alert => {
        const card = document.createElement('div');
        card.className = 'alert-archive-card';

        const mediaHtml = alert.image_path
            ? `<img src="${alert.image_path}" class="alert-archive-img" alt="Snapshot" onclick="openSnapshotByUrl('${alert.image_path}', '${alert.id}')" style="cursor:zoom-in;">`
            : `<div class="alert-archive-img alert-img-placeholder">
                   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                       <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                       <circle cx="12" cy="13" r="4"/>
                   </svg>
               </div>`;

        const ts = alert.timestamp ? alert.timestamp.replace('T', ' ').slice(0, 19) : '';
        card.innerHTML = `
            ${mediaHtml}
            <div class="alert-archive-body">
                <div class="alert-archive-header">
                    <span class="alert-archive-id">${(alert.id || '').toUpperCase()}</span>
                    <span class="alert-archive-time">${ts}</span>
                </div>
                <p class="alert-archive-desc">${alert.description || ''}</p>
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

window.deleteAlert = async function(alertId) {
    if (!confirm(`Delete incident log "${alertId}"?`)) return;
    try { await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' }); } catch {}
    state.localAlerts = state.localAlerts.filter(a => a.id !== alertId);
    showToast(t('deleteReport'), "warning");
    fetchAlerts();
};

// ----------------------------------------------------
// TOAST NOTIFICATIONS
// ----------------------------------------------------
function showToast(message, type = "success") {
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'danger' ? 'danger' : type === 'warning' ? 'warning' : ''}`;
    const iconColor = type === 'danger' ? 'var(--color-danger)' : type === 'warning' ? 'var(--color-warning)' : 'var(--color-success)';
    toast.innerHTML = `
        <span style="font-weight:800;font-family:var(--font-logo);color:${iconColor};">
            ${type === 'danger' ? '!' : type === 'warning' ? 'i' : '✓'}
        </span>
        <span class="toast-msg">${message}</span>
    `;
    elements.toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s cubic-bezier(0.16,1,0.3,1) reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
