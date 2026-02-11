// --- Global Auth Check ---
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = '/login.html';
}

const API_URL = '/api';

// Helper for Fetch with Auth
async function authFetch(url, options = {}) {
    const headers = options.headers || {};
    headers['Authorization'] = `Bearer ${token}`;
    options.headers = headers;

    const response = await fetch(url, options);
    if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login.html';
        return;
    }
    return response;
}

document.addEventListener('DOMContentLoaded', () => {
    // Logout Button Logic (assuming we add one)
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('token');
            window.location.href = '/login.html';
        });
    }

    // Navigation
    const navLinks = document.querySelectorAll('.nav-link');
    const views = document.querySelectorAll('.view');
    const titles = { 'dashboard': 'Visão Geral', 'machines': 'Lista de Ativos', 'settings': 'Configurações' };

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.getAttribute('data-page');

            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Show view
            views.forEach(view => {
                view.style.display = 'none';
                if (view.id === `${targetPage}-view`) {
                    view.style.display = 'block';
                }
            });

            // Update Header
            document.querySelector('.top-bar h1').textContent = titles[targetPage];

            // Load specific data
            if (targetPage === 'machines') loadMachines();
            if (targetPage === 'dashboard') loadStats();
        });
    });

    // Initial Load
    loadStats();
    loadMachines();

    // Modal Close
    const closeModal = document.querySelector('.close-modal');
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            document.getElementById('machine-details-modal').style.display = "none";
        });
    }
});

async function loadStats() {
    try {
        const response = await authFetch(`${API_URL}/stats`);
        if (!response) return; // Auth failure handling inside authFetch
        const data = await response.json();

        document.getElementById('total-machines').textContent = data.total_machines;
        // Mock online/disk data for now as API doesn't fully support it yet
        document.getElementById('online-machines').textContent = data.total_machines;

        // Update Chart
        updateChart(data.os_distribution);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadMachines() {
    try {
        const response = await authFetch(`${API_URL}/machines`);
        if (!response) return;
        const machines = await response.json();
        const tbody = document.getElementById('machines-table-body');
        tbody.innerHTML = '';

        machines.forEach(machine => {
            let statusColor = '#10b981'; // green
            let statusText = 'Online';

            if (machine.status === 'warning') {
                statusColor = '#f59e0b';
                statusText = 'Warning';
            } else if (machine.status === 'critical') {
                statusColor = '#ef4444';
                statusText = 'Critical';
            }

            // Online/Offline check (rough check based on last_seen > 5 min)
            const lastSeen = new Date(machine.last_seen);
            const now = new Date();
            const diffMs = now - lastSeen;
            const diffMins = Math.round(((diffMs % 86400000) % 3600000) / 60000); // rough

            // Better diff
            const diffSeconds = (now - lastSeen) / 1000;
            if (diffSeconds > 300) { // 5 mins
                statusColor = '#94a3b8'; // gray
                statusText = 'Offline';
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><span style="background-color: ${statusColor}; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">${statusText}</span></td>
                <td>${machine.hostname}
                    ${machine.alert_message ? `<br><small style="color:${statusColor}">${machine.alert_message}</small>` : ''}
                </td>
                <td>${machine.ip_address || 'N/A'}</td>
                <td>${machine.cpu_usage !== null ? machine.cpu_usage + '%' : '-'}</td>
                <td>${machine.memory_usage !== null ? machine.memory_usage + '%' : '-'}</td>
                <td>${machine.disk_usage !== null ? machine.disk_usage + '%' : '-'}</td>
                <td>${machine.os_info || 'N/A'}</td>
                <td>${new Date(machine.last_seen).toLocaleString()}</td>
                <td><button onclick="viewDetails(${machine.id})">Detalhes</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error loading machines:', error);
    }
}

async function viewDetails(id) {
    try {
        const response = await authFetch(`${API_URL}/machines/${id}`);
        if (!response) return;
        const machine = await response.json();

        const modal = document.getElementById('machine-details-modal');
        // const modalBody = document.getElementById('modal-body'); // Not used?

        document.getElementById('modal-hostname').textContent = machine.hostname;

        // Info Tab
        document.getElementById('modal-info-body').innerHTML = `
            <div class="detail-item"><strong>IP:</strong> ${machine.ip_address}</div>
            <div class="detail-item"><strong>SO:</strong> ${machine.os_info}</div>
            <div class="detail-item"><strong>Fabricante:</strong> ${machine.manufacturer || 'N/A'}</div>
            <div class="detail-item"><strong>Modelo:</strong> ${machine.model || 'N/A'}</div>
            <div class="detail-item"><strong>Serial:</strong> ${machine.serial_number || 'N/A'}</div>
            <div class="detail-item"><strong>Processador:</strong> ${machine.processor}</div>
            <div class="detail-item"><strong>Memória:</strong> ${machine.ram_gb} GB</div>
            <div class="detail-item"><strong>Disco:</strong> ${machine.disk_gb} GB</div>
            <div class="detail-item"><strong>Última Conexão:</strong> ${new Date(machine.last_seen).toLocaleString()}</div>
        `;

        // Software Tab
        const softwareHtml = machine.softwares && machine.softwares.length > 0
            ? machine.softwares.map(s => `
                <div class="detail-item">
                    <strong>${s.name}</strong> <span style="color: #94a3b8; font-size: 0.9em;">(${s.version || 'v?'})</span><br>
                    <small>${s.publisher || ''}</small>
                </div>`).join('')
            : '<div class="detail-item">Nenhum software registrado.</div>';
        document.getElementById('modal-software-body').innerHTML = softwareHtml;

        // Setup Export Button
        const exportBtn = document.getElementById('btn-export-software');
        // Remove old event listeners to prevent duplicates (cloning is a simple trick)
        const newExportBtn = exportBtn.cloneNode(true);
        exportBtn.parentNode.replaceChild(newExportBtn, exportBtn);

        newExportBtn.addEventListener('click', () => {
            exportSoftwareToCSV(machine.softwares, machine.hostname);
        });

        // Show/Hide export button based on data
        if (!machine.softwares || machine.softwares.length === 0) {
            newExportBtn.style.display = 'none';
        } else {
            newExportBtn.style.display = 'inline-block';
        }

        // Services Tab
        const servicesHtml = machine.services && machine.services.length > 0
            ? machine.services.map(s => `
                <div class="detail-item" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${s.display_name || s.name}</strong> <small>(${s.name})</small><br>
                        <span style="color: ${s.status === 'running' ? '#10b981' : '#94a3b8'}">${s.status}</span> - ${s.start_type}
                    </div>
                    <div style="flex-shrink: 0;">
                        <button onclick="controlService(${machine.id}, '${s.name}', 'start')" style="background: #10b981; padding: 2px 6px; font-size: 0.8em; margin-right: 2px;">Start</button>
                        <button onclick="controlService(${machine.id}, '${s.name}', 'stop')" style="background: #ef4444; padding: 2px 6px; font-size: 0.8em; margin-right: 2px;">Stop</button>
                        <button onclick="controlService(${machine.id}, '${s.name}', 'restart')" style="background: #3b82f6; padding: 2px 6px; font-size: 0.8em;">Restart</button>
                    </div>
                </div>`).join('')
            : '<div class="detail-item">Nenhum serviço registrado.</div>';
        document.getElementById('modal-services-body').innerHTML = servicesHtml;

        // Reset to first tab
        switchTab('info');

        // Init Terminal
        setupTerminal(machine.id);

        modal.style.display = "block";
    } catch (error) {
        console.error('Error details:', error);
    }
}

async function controlService(machineId, serviceName, action) {
    if (!confirm(`Deseja realmente executar "${action}" no serviço "${serviceName}"?`)) return;

    // Switch to terminal tab to show progress
    switchTab('terminal');
    appendToTerminal(`Requesting service ${action} for ${serviceName}...`, 'command');

    try {
        const response = await authFetch(`${API_URL}/machines/${machineId}/services/${serviceName}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });

        if (!response.ok) throw new Error('Failed to send action');

        const commandData = await response.json();
        const commandId = commandData.id;

        pollCommandResult(commandId);

    } catch (error) {
        appendToTerminal(`Error: ${error.message}`, 'error');
    }
}

function exportSoftwareToCSV(softwares, hostname) {
    if (!softwares || softwares.length === 0) {
        alert("Não há softwares para exportar.");
        return;
    }

    // CSV Header
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Nome,Versão,Fabricante\n";

    // CSV Rows
    softwares.forEach(sw => {
        const name = (sw.name || "").replace(/,/g, ""); // Remove commas to avoid breaking CSV
        const version = (sw.version || "").replace(/,/g, "");
        const publisher = (sw.publisher || "").replace(/,/g, "");
        csvContent += `${name},${version},${publisher}\n`;
    });

    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `software_inventory_${hostname}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// --- Terminal Logic ---
let currentMachineId = null;

function setupTerminal(machineId) {
    currentMachineId = machineId;
    const input = document.getElementById('terminal-input');
    const btn = document.getElementById('btn-run-command');

    // Clear previous output if new machine (optional, maybe keep history?)
    // document.getElementById('terminal-output').innerHTML = 'Microsoft Windows [Version 10.0.xxx]...';

    // Remove old listeners
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);

    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    // Add listeners
    newInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            runCommand(newInput.value);
            newInput.value = '';
        }
    });

    newBtn.addEventListener('click', () => {
        runCommand(newInput.value);
        newInput.value = '';
    });
}

function appendToTerminal(text, type = 'output') {
    const term = document.getElementById('terminal-output');
    const div = document.createElement('div');
    div.textContent = text;
    if (type === 'command') {
        div.style.color = '#fff';
        div.textContent = `PS > ${text}`;
    } else if (type === 'error') {
        div.style.color = '#ef4444';
    }
    term.appendChild(div);
    term.scrollTop = term.scrollHeight;
}

async function runCommand(cmd) {
    if (!cmd.trim()) return;

    appendToTerminal(cmd, 'command');

    try {
        // Send command
        const response = await authFetch(`${API_URL}/machines/${currentMachineId}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd })
        });

        if (!response.ok) throw new Error('Failed to send command');

        const commandData = await response.json();
        const commandId = commandData.id;

        // Poll for result
        pollCommandResult(commandId);

    } catch (error) {
        appendToTerminal(`Error: ${error.message}`, 'error');
    }
}

async function pollCommandResult(commandId) {
    let attempts = 0;
    const maxAttempts = 20; // 60 seconds (3s interval)

    const interval = setInterval(async () => {
        try {
            const response = await authFetch(`${API_URL}/commands/${commandId}`);
            const cmd = await response.json();

            if (cmd.status === 'completed' || cmd.status === 'error') {
                clearInterval(interval);
                appendToTerminal(cmd.output || "[No Output]");
            }

            attempts++;
            if (attempts >= maxAttempts) {
                clearInterval(interval);
                appendToTerminal("Timeout waiting for response.", 'error');
            }

        } catch (error) {
            clearInterval(interval);
            appendToTerminal(`Polling error: ${error.message}`, 'error');
        }
    }, 3000);
}


function switchTab(tabName) {
    // Hide all content
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    // Show active
    document.getElementById(`tab-${tabName}`).style.display = 'block';

    // Highlight button
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(tabName)) {
            btn.classList.add('active');
        }
    });
}

let osChartInstance = null;

function updateChart(osData) {
    const ctx = document.getElementById('osChart').getContext('2d');

    if (osChartInstance) {
        osChartInstance.destroy();
    }

    osChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(osData),
            datasets: [{
                data: Object.values(osData),
                backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8' }
                }
            }
        });
}

// --- Settings Logic ---

// Auto Refresh
let autoRefreshInterval = null;

function setupSettings() {
    // Auto Refresh Toggle
    const toggleRefresh = document.getElementById('toggle-autorefresh');
    if (toggleRefresh) {
        toggleRefresh.addEventListener('change', (e) => {
            if (e.target.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
        // Initial state
        if (toggleRefresh.checked) startAutoRefresh();
    }

    // Compact Mode Toggle
    const toggleCompact = document.getElementById('toggle-compact');
    if (toggleCompact) {
        toggleCompact.addEventListener('change', (e) => {
            if (e.target.checked) {
                document.body.classList.add('compact-mode');
            } else {
                document.body.classList.remove('compact-mode');
            }
        });
    }

    // Set Token (Mock for now, normally fetch from /api/config or similar)
    const tokenInput = document.getElementById('agent-token');
    if (localStorage.getItem('token')) {
        // Just showing the auth token as the "enrollment" token for simplicity in this demo
        // In production, you'd likely have a separate enrollment key.
        tokenInput.value = localStorage.getItem('token');
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(() => {
        // Only refresh if tab is active to save resources? 
        // For now just check if dashboard or machines view is active
        const dashboard = document.getElementById('dashboard-view');
        const machines = document.getElementById('machines-view');

        if (dashboard.style.display !== 'none') loadStats();
        if (machines.style.display !== 'none') loadMachines();

    }, 30000); // 30 seconds
    console.log('Auto-refresh started');
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Auto-refresh stopped');
    }
}

function copyToken() {
    const copyText = document.getElementById("agent-token");
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(copyText.value)
        .then(() => alert("Token copiado!"))
        .catch(() => alert("Falha ao copiar"));
}

async function exportFullInventory() {
    try {
        const response = await authFetch(`${API_URL}/machines`);
        if (!response) return;
        const machines = await response.json();

        let csv = "data:text/csv;charset=utf-8,";
        // Header
        csv += "Client Code,Hostname,IP,OS,CPU%,RAM,Disk,Software Name,Version,Publisher,Last Seen\n";

        machines.forEach(m => {
            // Base machine info
            const baseInfo = `${m.client_code || 'DEFAULT'},${m.hostname},${m.ip_address},${m.os_info},${m.cpu_usage}%,${m.ram_gb}GB,${m.disk_gb}GB`;

            // If no software, just print machine info
            if (!m.softwares || m.softwares.length === 0) {
                csv += `${baseInfo},,,${m.last_seen}\n`;
            } else {
                // One row per software
                m.softwares.forEach(s => {
                    // Escape commas in names
                    const cleanName = s.name ? `"${s.name.replace(/"/g, '""')}"` : "";
                    const cleanVer = s.version ? `"${s.version.replace(/"/g, '""')}"` : "";
                    const cleanPub = s.publisher ? `"${s.publisher.replace(/"/g, '""')}"` : "";

                    csv += `${baseInfo},${cleanName},${cleanVer},${cleanPub},${m.last_seen}\n`;
                });
            }
        });

        const encodedUri = encodeURI(csv);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `full_inventory_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (e) {
        alert("Erro ao exportar dados: " + e.message);
    }
}

async function pruneOfflineAgents() {
    if (!confirm("Isso removerá do banco de dados todas as máquinas que não se conectam há mais de 30 dias. Continuar?")) return;

    // Implementation would require a backend endpoint like DELETE /api/machines/prune
    // For now, just mock the alert
    alert("Funcionalidade de limpeza solicitada ao servidor. (Backend endpoint pending)");
}

// Call setup on load
document.addEventListener('DOMContentLoaded', setupSettings);
