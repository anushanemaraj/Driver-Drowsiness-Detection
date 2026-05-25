/**
 * Premium AI Driver Monitor - Frontend Logic
 */

let earChart, marChart;
let currentSection = 'dashboard';
let systemRunning = false;
let updateInterval;

// Initialize Charts
function initCharts() {
    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#8b949e', font: { size: 10 } }
            },
            x: {
                grid: { display: false },
                ticks: { display: false }
            }
        },
        elements: {
            line: { tension: 0.4, borderWidth: 2, borderColor: '#00f3ff' },
            point: { radius: 0 }
        }
    };

    const earCtx = document.getElementById('earChart').getContext('2d');
    earChart = new Chart(earCtx, {
        type: 'line',
        data: {
            labels: Array(50).fill(''),
            datasets: [{
                data: [],
                borderColor: '#00f3ff',
                backgroundColor: 'rgba(0, 243, 255, 0.1)',
                fill: true
            }]
        },
        options: chartDefaults
    });

    const marCtx = document.getElementById('marChart').getContext('2d');
    marChart = new Chart(marCtx, {
        type: 'line',
        data: {
            labels: Array(50).fill(''),
            datasets: [{
                data: [],
                borderColor: '#7000ff',
                backgroundColor: 'rgba(112, 0, 255, 0.1)',
                fill: true
            }]
        },
        options: chartDefaults
    });
}

// Section Navigation
function showSection(sectionId) {
    currentSection = sectionId;
    
    // Update Sidebar
    document.querySelectorAll('.nav-item').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('onclick').includes(sectionId)) {
            link.classList.add('active');
        }
    });

    // Update Content
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('hidden');
    });
    document.getElementById(`${sectionId}-section`).classList.remove('hidden');

    // Update Header
    const titles = {
        dashboard: 'Command Center',
        monitoring: 'Live Monitoring',
        analytics: 'Analytics',
        logs: 'Telemetry',
        recordings: 'Archive',
        settings: 'Settings'
    };
    document.getElementById('header-title').innerText = titles[sectionId] || 'Dashboard';

    if (sectionId === 'recordings') fetchRecordings();
    if (sectionId === 'analytics') updateAnalytics();
}

// Update Dashboard Status
async function updateStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();

        // Update Global State
        systemRunning = data.running;
        
        // Update System Status Indicator
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        if (data.running) {
            statusDot.className = 'w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_#22c55e] pulse';
            statusText.innerText = 'System Active';
        } else {
            statusDot.className = 'w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444]';
            statusText.innerText = 'Standby';
        }

        // Update Start/Stop Button
        const btn = document.getElementById('systemToggleBtn');
        btn.innerText = data.running ? 'STOP SYSTEM' : 'INITIALIZE CORE';
        btn.classList.toggle('btn-accent', !data.running);
        btn.classList.toggle('btn-outline', data.running);

        // Update Live Cards
        document.getElementById('live-ear').innerText = data.current_ear.toFixed(3);
        document.getElementById('live-mar').innerText = data.current_mar.toFixed(3);
        document.getElementById('live-alerts').innerText = data.total_alerts;
        document.getElementById('live-yawns').innerText = data.total_yawns;
        document.getElementById('fatigue-score-val').innerText = `${Math.round(data.fatigue_score)}%`;
        
        // Update Fatigue Progress Bar
        const progressBar = document.getElementById('fatigue-progress');
        if (progressBar) {
            progressBar.style.width = `${data.fatigue_score}%`;
            if (data.fatigue_score > 70) progressBar.style.background = 'var(--danger)';
            else if (data.fatigue_score > 40) progressBar.style.background = 'var(--warning)';
            else progressBar.style.background = 'linear-gradient(to right, var(--accent), #00ffaa)';
        }

        // Update Alerts & Badges
        document.getElementById('drowsy-alert').classList.toggle('hidden', !data.drowsy);
        document.getElementById('yawning-alert').classList.toggle('hidden', !data.yawning);
        document.getElementById('scanning-overlay').classList.toggle('hidden', !data.running);
        
        // Update Driver Status Badge
        const statusBadge = document.getElementById('driver-status-badge');
        statusBadge.innerText = data.fatigue_status;
        if (data.fatigue_status === 'Normal') statusBadge.className = 'text-2xl font-black font-cyber text-glow-blue uppercase';
        else if (data.fatigue_status === 'Sleepy') statusBadge.className = 'text-2xl font-black font-cyber text-warning uppercase';
        else statusBadge.className = 'text-2xl font-black font-cyber text-danger uppercase animate-pulse';

        // Update Charts
        if (data.ear_history && data.ear_history.length > 0) {
            earChart.data.datasets[0].data = data.ear_history;
            earChart.update('none');
        }
        if (data.mar_history && data.mar_history.length > 0) {
            marChart.data.datasets[0].data = data.mar_history;
            marChart.update('none');
        }

        // Update Logs Table (Telemetry)
        if (data.logs) {
            const tbody = document.getElementById('log-tbody');
            if (tbody) {
                tbody.innerHTML = data.logs.slice(-10).reverse().map(log => {
                    const parts = log.match(/\[(.*?)\] \[(.*?)\] (.*)/);
                    if (!parts) return '';
                    const [_, time, type, msg] = parts;
                    const typeColor = type === 'ALERT' ? 'var(--danger)' : 'var(--accent)';
                    return `
                        <tr>
                            <td class="font-mono text-[10px] opacity-60">${time}</td>
                            <td><span style="color: ${typeColor}; font-weight: bold; font-size: 10px;">${type}</span></td>
                            <td>${msg}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        // Update Session Time
        const h = Math.floor(data.session_duration / 3600).toString().padStart(2, '0');
        const m = Math.floor((data.session_duration % 3600) / 60).toString().padStart(2, '0');
        const s = (data.session_duration % 60).toString().padStart(2, '0');
        document.getElementById('session-timer').innerText = `SESSION: ${h}:${m}:${s}`;

        // Update Settings UI from state
        const alarmBtn = document.getElementById('alarm-switch');
        const voiceBtn = document.getElementById('voice-switch');
        const recBtn = document.getElementById('rec-switch');
        
        if (alarmBtn) alarmBtn.innerText = data.alarm_enabled ? 'ENABLED' : 'DISABLED';
        if (voiceBtn) voiceBtn.innerText = data.voice_enabled ? 'ENABLED' : 'DISABLED';
        if (recBtn) recBtn.innerText = data.recording_enabled ? 'ENABLED' : 'DISABLED';

    } catch (err) {
        console.error('Telemetry Sync Error:', err);
    }
}

// Analytics View Update
async function updateAnalytics() {
    try {
        const response = await fetch('/analytics');
        const data = await response.json();
        // Custom analytics update logic here if needed
    } catch (err) {
        console.error('Analytics Update Error:', err);
    }
}

// System Controls
async function toggleSystem() {
    const endpoint = systemRunning ? '/stop' : '/start';
    await fetch(endpoint, { method: 'POST' });
    updateStatus();
}

async function updateSetting(key) {
    const response = await fetch('/status');
    const data = await response.json();
    
    const settings = {
        alarm: data.alarm_enabled,
        voice: data.voice_enabled,
        recording: data.recording_enabled
    };
    
    settings[key] = !settings[key];

    await fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    });
    updateStatus();
}

async function calibrate() {
    await fetch('/calibrate', { method: 'POST' });
    alert("Calibration Initialized. Keep a neutral face.");
}

async function fetchRecordings() {
    try {
        const response = await fetch('/recordings');
        const files = await response.json();
        const container = document.getElementById('recordings-grid');
        
        if (!container) return;

        if (files.length === 0) {
            container.innerHTML = '<div class="col-span-full text-center text-gray-500 py-20">No archives found.</div>';
            return;
        }

        container.innerHTML = files.map(file => `
            <div class="card p-4 flex flex-col gap-3">
                <div class="aspect-video bg-black rounded-xl flex items-center justify-center">
                    <i class="fas fa-file-video text-3xl opacity-20"></i>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-[10px] font-mono opacity-60">${file}</span>
                    <a href="/recordings/${file}" download class="text-accent hover:text-white"><i class="fas fa-download"></i></a>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load archive:', err);
    }
}

function updateClock() {
    const now = new Date();
    document.getElementById('top-clock').innerText = now.toLocaleTimeString([], { hour12: false });
}

// Fullscreen Camera
function toggleFullscreen() {
    const elem = document.querySelector('.video-viewport img');
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}

// Initialization
window.onload = () => {
    initCharts();
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(updateStatus, 1000);
    showSection('dashboard');
    
    // Connect fullscreen button
    const fsBtn = document.querySelector('button[onclick="calibrate()"]').parentElement.querySelector('.btn-outline');
    if (fsBtn) {
        fsBtn.onclick = toggleFullscreen;
        fsBtn.innerHTML = '<i class="fas fa-expand"></i>';
    }
};
