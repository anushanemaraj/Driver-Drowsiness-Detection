let earChart, marChart;
let systemRunning = false;
let updateInterval;

// Chart configurations
const chartOptions = {
    responsive: true,
    scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.1)' }, ticks: { color: '#8b949e' } },
        x: { grid: { display: false }, ticks: { color: '#8b949e' } }
    },
    plugins: { legend: { display: false } },
    elements: { line: { tension: 0.4 }, point: { radius: 0 } }
};

function initCharts() {
    const earCtx = document.getElementById('earChart').getContext('2d');
    const marCtx = document.getElementById('marChart').getContext('2d');

    earChart = new Chart(earCtx, {
        type: 'line',
        data: { labels: Array(50).fill(''), datasets: [{ data: [], borderColor: '#00f3ff', borderWidth: 2, fill: true, backgroundColor: 'rgba(0, 243, 255, 0.1)' }] },
        options: chartOptions
    });

    marChart = new Chart(marCtx, {
        type: 'line',
        data: { labels: Array(50).fill(''), datasets: [{ data: [], borderColor: '#ff003c', borderWidth: 2, fill: true, backgroundColor: 'rgba(255, 0, 60, 0.1)' }] },
        options: chartOptions
    });
}

async function updateStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();

        // Update basic metrics
        document.getElementById('live-ear').innerText = data.current_ear.toFixed(2);
        document.getElementById('live-mar').innerText = data.current_mar.toFixed(2);
        document.getElementById('total-alerts').innerText = data.total_alerts;
        document.getElementById('total-yawns').innerText = data.total_yawns;
        document.getElementById('fatigue-value').innerText = data.fatigue_score + '%';
        document.getElementById('fatigue-status').innerText = data.fatigue_status;
        
        // Update fatigue meter
        const path = document.getElementById('fatigue-path');
        path.style.strokeDasharray = `${data.fatigue_score}, 100`;
        if (data.fatigue_score > 70) path.classList.replace('text-blue-500', 'text-red-500');
        else if (data.fatigue_score > 40) path.classList.replace('text-blue-500', 'text-yellow-500');
        else {
            path.classList.remove('text-red-500', 'text-yellow-500');
            path.classList.add('text-blue-500');
        }

        // Session time
        const h = Math.floor(data.session_duration / 3600).toString().padStart(2, '0');
        const m = Math.floor((data.session_duration % 3600) / 60).toString().padStart(2, '0');
        const s = (data.session_duration % 60).toString().padStart(2, '0');
        document.getElementById('session-time').innerText = `${h}:${m}:${s}`;

        // Badges & Indicators
        document.getElementById('drowsy-badge').classList.toggle('hidden', !data.drowsy);
        
        const yawnBadge = document.getElementById('yawn-badge');
        yawnBadge.classList.toggle('hidden', !data.yawning);
        if (data.total_yawns >= 5) {
            yawnBadge.innerText = "CRITICAL: HIGH FATIGUE";
            yawnBadge.classList.replace('bg-yellow-500', 'bg-red-600');
            yawnBadge.classList.add('animate-pulse');
        } else {
            yawnBadge.innerText = "YAWNING";
            yawnBadge.classList.replace('bg-red-600', 'bg-yellow-500');
        }

        document.getElementById('rec-indicator').classList.toggle('hidden', !data.drowsy);

        // Update Charts
        if (earChart && data.ear_history) {
            earChart.data.datasets[0].data = data.ear_history;
            earChart.update('none');
        }
        if (marChart && data.mar_history) {
            marChart.data.datasets[0].data = data.mar_history;
            marChart.update('none');
        }

        // Update Logs
        const logContainer = document.getElementById('log-container');
        logContainer.innerHTML = data.logs.map(log => `<div>${log}</div>`).join('');
        logContainer.scrollTop = logContainer.scrollHeight;

        // Update Alert History
        const alertHist = document.getElementById('alert-history');
        if (data.alert_history.length > 0) {
            alertHist.innerHTML = data.alert_history.map(time => `
                <div class="flex-shrink-0 bg-[#0d1117] p-3 rounded-xl border border-red-900 border-opacity-30">
                    <span class="text-xs text-red-500 font-bold block">ALERT</span>
                    <span class="text-sm font-mono">${time}</span>
                </div>
            `).join('');
        }

        systemRunning = data.running;
        const btn = document.getElementById('startStopBtn');
        btn.innerText = systemRunning ? 'STOP SYSTEM' : 'START SYSTEM';
        btn.classList.toggle('bg-red-600', systemRunning);
        btn.classList.toggle('hover:bg-red-500', systemRunning);

    } catch (err) {
        console.error("Status update failed:", err);
    }
}

async function toggleSystem() {
    const endpoint = systemRunning ? '/stop' : '/start';
    await fetch(endpoint, { method: 'POST' });
    updateStatus();
}

function showSection(sectionId) {
    ['dashboard', 'analytics', 'logs', 'settings'].forEach(id => {
        document.getElementById(`${id}-section`).classList.add('hidden');
    });
    document.getElementById(`${sectionId}-section`).classList.remove('hidden');
    
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.innerText.toLowerCase().includes(sectionId)) item.classList.add('active');
    });

    // Update headers
    const titles = {
        dashboard: ["Dashboard Overview", "Real-time driver monitoring and fatigue analysis."],
        analytics: ["Advanced Analytics", "Detailed breakdown of eye and mouth metrics over time."],
        logs: ["System Event Logs", "Historical record of all detection events and system status."],
        settings: ["System Configuration", "Customize alert thresholds and system behavior."]
    };
    document.getElementById('section-title').innerText = titles[sectionId][0];
    document.getElementById('section-subtitle').innerText = titles[sectionId][1];
}

async function saveSettings() {
    const settings = {
        alarm: document.getElementById('alarmToggle').checked,
        voice: document.getElementById('voiceToggle').checked,
        recording: document.getElementById('recordingToggle').checked
    };
    await fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    });
}

async function calibrate() {
    await fetch('/calibrate', { method: 'POST' });
    alert("Calibration started! Please look straight at the camera with a neutral expression for 5 seconds.");
}

async function clearLogs() {
    if (confirm("Clear all system logs?")) {
        await fetch('/clear_logs', { method: 'POST' });
        updateStatus();
    }
}

// Initialization
window.onload = () => {
    initCharts();
    updateInterval = setInterval(updateStatus, 1000);
    showSection('dashboard');
};
