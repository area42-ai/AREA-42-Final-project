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
        "camera.noneDesc": "No camera devices found. Connect a camera and refresh the page.",
        "camera.selectAll": "Select All",
        "btn.startMonitoring": "Start Stream",
        "btn.stopMonitoring": "Stop Stream",
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
        "toast.noCameras": "No cameras selected",
        "toast.camerasActive": "camera stream(s) activated",
        "toast.camerasDeactivated": "All camera streams deactivated",
        "toast.monitoringStarted": "AI monitoring started",
        "toast.monitoringStopped": "AI monitoring stopped",
        "toast.monitoringFailed": "Failed to start monitoring",
        "toast.stopFailed": "Failed to stop monitoring",
        "toast.detected": "cameras detected",
        "toast.incident": "Incident logged",
        "toast.clickEye": "Click the eye icon on a camera to activate AI",
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
        "camera.noneDesc": "Подключите камеру и обновите страницу.",
        "camera.selectAll": "Выбрать все",
        "btn.startMonitoring": "Запустить стрим",
        "btn.stopMonitoring": "Остановить стрим",
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
        "toast.noCameras": "Камеры не выбраны",
        "toast.camerasActive": "потока камер активированы",
        "toast.camerasDeactivated": "Все потоки камер остановлены",
        "toast.monitoringStarted": "ИИ-мониторинг запущен",
        "toast.monitoringStopped": "ИИ-мониторинг остановлен",
        "toast.monitoringFailed": "Не удалось запустить мониторинг",
        "toast.stopFailed": "Не удалось остановить мониторинг",
        "toast.detected": "камер обнаружено",
        "toast.incident": "Инцидент зафиксирован",
        "toast.clickEye": "Нажмите на глаз на камере для запуска ИИ",
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
        "camera.noneDesc": "Kamera bağlayın və səhifəni yeniləyin.",
        "camera.selectAll": "Hamısını seç",
        "btn.startMonitoring": "Yayımı başlat",
        "btn.stopMonitoring": "Yayımı dayandır",
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
        "toast.noCameras": "Kamera seçilməyib",
        "toast.camerasActive": "kamera axını aktivləşdirildi",
        "toast.camerasDeactivated": "Bütün kamera axınları dayandırıldı",
        "toast.monitoringStarted": "AI monitorinqi başladı",
        "toast.monitoringStopped": "AI monitorinqi dayandırıldı",
        "toast.monitoringFailed": "Monitorinqi başlatmaq alınmadı",
        "toast.stopFailed": "Monitorinqi dayandırmaq alınmadı",
        "toast.detected": "kamera aşkar edildi",
        "toast.incident": "Hadisə qeydə alındı",
        "toast.clickEye": "AI-ı aktivləşdirmək üçün kameradakı göz ikonuna basın",
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
}

// ----------------------------------------------------
// GLOBAL APP STATE
// ----------------------------------------------------
const state = {
    isStreaming: false,
    isMonitoring: false,
    currentView: 'dashboard',
    settings: {
        require_helmet: true,
        require_vest: true,
        require_goggles: true,
    },
    isBackendConnected: false,
    localAlerts: [],
    localRecordings: [],
    cameras: [],
    selectedCameraIds: new Set(),
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
    violationsCountBadge: document.getElementById('violations-count-badge'),
    cameraGrid: document.getElementById('camera-grid'),
    cameraGridPlaceholder: document.getElementById('camera-grid-placeholder'),
    cameraSelectionBar: document.getElementById('camera-selection-bar'),
    selAllCameras: document.getElementById('sel-all-cameras'),
    camSelInfo: document.getElementById('cam-sel-info'),
    btnStartStream: document.getElementById('btn-start-stream'),
    btnPauseStream: document.getElementById('btn-pause-stream'),
    reqHelmet: document.getElementById('req-helmet'),
    reqVest: document.getElementById('req-vest'),
    reqGoggles: document.getElementById('req-goggles'),
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
    violationLogPanel: document.getElementById('violation-log-panel'),
    violationLogToggle: document.getElementById('violation-log-toggle'),
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
    setupViolationLogToggle();

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
// VIOLATION LOG COLLAPSE
// ----------------------------------------------------
function setupViolationLogToggle() {
    const toggle = elements.violationLogToggle;
    const panel = elements.violationLogPanel;
    if (!toggle || !panel) return;
    toggle.addEventListener('click', () => {
        panel.classList.toggle('log-collapsed');
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
    state.selectedCameraIds.clear();
    state.cameras.forEach(cam => {
        state.selectedCameraIds.add(cam.id);
        grid.appendChild(buildCameraCard(cam));
    });

    // Show camera selection bar
    if (elements.cameraSelectionBar) {
        elements.cameraSelectionBar.style.display = 'flex';
    }
    updateCameraSelectionInfo();

    // Wire up "Select All" checkbox
    if (elements.selAllCameras) {
        elements.selAllCameras.addEventListener('change', function () {
            state.cameras.forEach(cam => {
                const cb = document.getElementById(`cam-sel-${cam.id}`);
                if (cb) cb.checked = this.checked;
                if (this.checked) {
                    state.selectedCameraIds.add(cam.id);
                } else {
                    state.selectedCameraIds.delete(cam.id);
                }
            });
            updateCameraSelectionInfo();
        });
    }

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
                <input type="checkbox" class="cam-select-checkbox" id="cam-sel-${cam.id}" checked
                    onchange="toggleCameraSelection(${cam.id}, this.checked)">
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
            <button class="cam-monitor-btn" id="cam-monitor-btn-${cam.id}"
                onclick="toggleMonitoring()" title="Toggle AI Monitoring">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
            </button>
            <div class="camera-feed-overlay">
                <span class="camera-overlay-badge disconnected" id="cam-badge-${cam.id}">OFFLINE</span>
                <span class="camera-overlay-timestamp" id="cam-time-${cam.id}">--:--:--</span>
            </div>
        </div>
    `;
    return card;
}

window.toggleCameraSelection = function (camId, checked) {
    if (checked) {
        state.selectedCameraIds.add(camId);
    } else {
        state.selectedCameraIds.delete(camId);
    }
    updateCameraSelectionInfo();
};

function updateCameraSelectionInfo() {
    if (elements.camSelInfo) {
        elements.camSelInfo.textContent = `${state.selectedCameraIds.size} / ${state.cameras.length}`;
    }
    if (elements.selAllCameras) {
        elements.selAllCameras.checked = state.selectedCameraIds.size === state.cameras.length;
        elements.selAllCameras.indeterminate =
            state.selectedCameraIds.size > 0 && state.selectedCameraIds.size < state.cameras.length;
    }
}

window.toggleCameraFullscreen = function (camId) {
    const feedWrapper = document.getElementById(`cam-feed-${camId}`);
    if (!feedWrapper) return;
    if (!document.fullscreenElement) {
        feedWrapper.requestFullscreen().catch(() => {});
    } else {
        document.exitFullscreen();
    }
};

// ----------------------------------------------------
// CLOCK & HEADER METRICS
// ----------------------------------------------------
function setupClock() {
    setInterval(() => {
        elements.liveClock.textContent = new Date().toTimeString().split(' ')[0];
    }, 1000);
}

function updateHeaderMetrics(activeCount, violationsCount) {
    if (elements.violationsCountBadge) elements.violationsCountBadge.textContent = violationsCount;
}

function updateHeaderMetricsFromAlerts(alerts) {
    updateHeaderMetrics(alerts.length, alerts.length);
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
    [elements.reqHelmet, elements.reqVest, elements.reqGoggles].filter(Boolean).forEach(input => {
        if (input) input.addEventListener('change', () => {
            syncSettingsState();
            showToast(t('toast.settingsUpdated'), "warning");
        });
    });

    elements.btnStartStream.addEventListener('click', startStream);
    elements.btnPauseStream.addEventListener('click', stopStream);
    elements.modalClose.addEventListener('click', closeModal);
}

// ----------------------------------------------------
// START / STOP STREAM  (camera preview only)
// ----------------------------------------------------
function resetViolationJournal() {
    state.shownAlertIds = new Set();
    state.localAlerts = [];
    if (elements.liveAlertFeed) {
        elements.liveAlertFeed.innerHTML = `
            <div class="empty-state-card">
                <div class="empty-icon-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <h5>${t('hazard.safeTitle')}</h5>
                <p>${t('hazard.safeDesc')}</p>
            </div>`;
    }
    if (elements.violationsCountBadge) elements.violationsCountBadge.textContent = '0';
}

async function startStream() {
    if (state.cameraStreaming) return;

    // Reset journal on each new stream session
    resetViolationJournal();

    const selectedCams = state.cameras.filter(cam => state.selectedCameraIds.has(cam.id));
    if (selectedCams.length === 0) {
        showToast(t('toast.noCameras'), "danger");
        return;
    }

    selectedCams.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);
        const eyeBtn = document.getElementById(`cam-monitor-btn-${cam.id}`);

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
        if (eyeBtn) eyeBtn.style.display = 'flex';

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

    updateStatusText(t('status.active'), 'green');
    showToast(`${selectedCams.length} ${t('toast.camerasActive')}`, "success");
    setTimeout(() => showToast(t('toast.clickEye'), "warning"), 1200);
}

async function stopStream() {
    // Stop all camera streams
    state.cameras.forEach(cam => {
        const feedWrapper = document.getElementById(`cam-feed-${cam.id}`);
        const placeholder = document.getElementById(`cam-placeholder-${cam.id}`);
        const badge = document.getElementById(`cam-badge-${cam.id}`);
        const dot = document.getElementById(`cam-dot-${cam.id}`);
        const card = document.getElementById(`camera-card-${cam.id}`);
        const eyeBtn = document.getElementById(`cam-monitor-btn-${cam.id}`);

        if (feedWrapper) {
            const imgEl = feedWrapper.querySelector('img.mjpeg-feed');
            if (imgEl) { imgEl.src = ''; imgEl.remove(); }
        }

        if (placeholder) placeholder.style.display = 'flex';
        if (badge) { badge.textContent = 'OFFLINE'; badge.classList.add('disconnected'); }
        if (dot) dot.className = 'camera-status-dot offline';
        if (card) card.classList.remove('camera-active');
        if (eyeBtn) { eyeBtn.style.display = 'none'; eyeBtn.classList.remove('monitoring-active'); }

        if (cam._timeInterval) { clearInterval(cam._timeInterval); cam._timeInterval = null; }
        const timeEl = document.getElementById(`cam-time-${cam.id}`);
        if (timeEl) timeEl.textContent = '--:--:--';
    });

    state.isStreaming = false;
    state.cameraStreaming = false;

    elements.btnStartStream.disabled = false;
    elements.btnPauseStream.disabled = true;

    const camCount = state.cameras.length;
    updateStatusText(`${camCount} ${t('status.ready')}`, 'green');
    showToast(t('toast.camerasDeactivated'), "warning");

    // Stop AI pipeline if running
    if (state.isMonitoring) {
        try {
            await fetch("/api/live/stop", { method: "POST" });
            state.isMonitoring = false;
        } catch {}
        stopAlertPolling();
        showToast(t('toast.monitoringStopped'), "warning");
    }
}

// ----------------------------------------------------
// AI MONITORING TOGGLE  (eye icon on camera card)
// ----------------------------------------------------
window.toggleMonitoring = async function () {
    if (!state.cameraStreaming) return;

    if (state.isMonitoring) {
        // Stop AI monitoring
        try {
            const response = await fetch("/api/live/stop", { method: "POST" });
            const result = await response.json();
            if (result.success) {
                state.isMonitoring = false;
                setEyeButtonsState(false);
                stopAlertPolling();
                updateStatusText(t('status.active'), 'green');
                showToast(t('toast.monitoringStopped'), "warning");
            } else {
                showToast(result.error || t('toast.stopFailed'), "danger");
            }
        } catch (err) {
            console.error(err);
            showToast(t('toast.stopFailed'), "danger");
        }
    } else {
        // Start AI monitoring
        try {
            const response = await fetch("/api/live/start", { method: "POST" });
            const result = await response.json();
            if (result.success) {
                state.isMonitoring = true;
                setEyeButtonsState(true);
                startAlertPolling();
                updateStatusText(t('status.monitoring'), 'orange');
                showToast(t('toast.monitoringStarted'), "success");
            } else {
                showToast(result.error || t('toast.monitoringFailed'), "danger");
            }
        } catch (err) {
            console.error(err);
            showToast(t('toast.monitoringFailed'), "danger");
        }
    }
};

function setEyeButtonsState(active) {
    document.querySelectorAll('.cam-monitor-btn').forEach(btn => {
        btn.classList.toggle('monitoring-active', active);
    });
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
// STATUS HELPERS
// ----------------------------------------------------
function updateStatusText(text, colorClass) {
    elements.statusText.textContent = text;
    elements.statusDot.className = `status-dot ${colorClass}`;
}

// ----------------------------------------------------
// VIOLATION SIDEBAR
// ----------------------------------------------------
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
// MODAL
// ----------------------------------------------------
window.openSnapshotByUrl = function (imageUrl, alertId) {
    elements.modalTitle.textContent = `Incident Frame // ID: ${alertId.toUpperCase()}`;
    elements.modalMediaBody.innerHTML = `
        <img src="${imageUrl}" style="width:100%;aspect-ratio:16/9;object-fit:contain;border-radius:8px;border:1px solid #1E293B;">
    `;
    elements.modal.classList.add('active');
};

window.openSnapshot = function (alertId) {
    const alert = state.localAlerts.find(a => a.id === alertId);
    if (!alert || !alert.image_path) return;
    openSnapshotByUrl(alert.image_path, alertId);
};

window.playArchiveVideo = function (url, filename) {
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

window.deleteAlert = async function (alertId) {
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
