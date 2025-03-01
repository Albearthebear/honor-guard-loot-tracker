// Dragon Soul Loot Manager - Frontend Application

// Global state
const state = {
    activePage: 'dashboard',
    wsConnected: false,
    activeRaid: null,
    players: [],
    priorities: [],
    lootHistory: [],
    raidSessions: [],
    stats: {}
};

// DOM Elements
const elements = {
    navLinks: document.querySelectorAll('.nav-link'),
    pages: document.querySelectorAll('.page'),
    
    // Dashboard elements
    lootDistributionChart: document.getElementById('lootDistributionChart'),
    tokenDistributionChart: document.getElementById('tokenDistributionChart'),
    recentLootTable: document.getElementById('recentLootTable'),
    
    // Priorities elements
    prioritiesTable: document.getElementById('prioritiesTable'),
    tokenFilter: document.getElementById('tokenFilter'),
    statFilter: document.getElementById('statFilter'),
    roleFilter: document.getElementById('roleFilter'),
    
    // History elements
    historyTable: document.getElementById('historyTable'),
    playerSearch: document.getElementById('playerSearch'),
    itemTypeFilter: document.getElementById('itemTypeFilter'),
    raidTypeFilter: document.getElementById('raidTypeFilter'),
    
    // Raid elements
    noActiveRaid: document.getElementById('noActiveRaid'),
    activeRaidInfo: document.getElementById('activeRaidInfo'),
    currentBoss: document.getElementById('currentBoss'),
    raidStartTime: document.getElementById('raidStartTime'),
    participantCount: document.getElementById('participantCount'),
    startRaidBtn: document.getElementById('startRaidBtn'),
    endRaidBtn: document.getElementById('endRaidBtn'),
    lootAssignForm: document.getElementById('lootAssignForm'),
    itemName: document.getElementById('itemName'),
    playerName: document.getElementById('playerName'),
    bossName: document.getElementById('bossName'),
    assignLootBtn: document.getElementById('assignLootBtn'),
    currentRaidLootTable: document.getElementById('currentRaidLootTable'),
    
    // Modal elements
    startRaidModal: new bootstrap.Modal(document.getElementById('startRaidModal')),
    raidBoss: document.getElementById('raidBoss'),
    participantsList: document.getElementById('participantsList'),
    confirmStartRaid: document.getElementById('confirmStartRaid'),
    
    // WebSocket status
    wsStatus: new bootstrap.Toast(document.getElementById('wsStatus')),
    wsStatusBody: document.querySelector('#wsStatus .toast-body')
};

// API endpoints
const API = {
    priorities: '/api/priorities',
    players: '/api/players',
    items: '/api/items',
    raidStatus: '/api/raid/status',
    raidStart: '/api/raid/start',
    raidEnd: '/api/raid/end',
    raidBoss: '/api/raid/boss',
    lootAssign: '/api/loot/assign',
    stats: '/api/stats',
    history: '/api/history',
    sessions: '/api/sessions',
    processData: '/api/process-data'
};

// WebSocket connection
let ws = null;

// Initialize the application
function init() {
    // Set up navigation
    setupNavigation();
    
    // Load initial data
    loadData();
    
    // Connect to WebSocket
    connectWebSocket();
    
    // Set up event listeners
    setupEventListeners();
}

// Set up navigation between pages
function setupNavigation() {
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            navigateTo(page);
        });
    });
}

// Navigate to a specific page
function navigateTo(page) {
    // Update active state in navigation
    elements.navLinks.forEach(link => {
        if (link.dataset.page === page) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Show the selected page, hide others
    elements.pages.forEach(pageEl => {
        if (pageEl.id === `${page}-page`) {
            pageEl.style.display = 'block';
        } else {
            pageEl.style.display = 'none';
        }
    });
    
    // Update state
    state.activePage = page;
    
    // Refresh page data if needed
    refreshPageData(page);
}

// Refresh data for the current page
function refreshPageData(page) {
    switch (page) {
        case 'dashboard':
            renderDashboard();
            break;
        case 'priorities':
            loadPriorities();
            break;
        case 'history':
            loadLootHistory();
            break;
        case 'raid':
            loadRaidStatus();
            break;
    }
}

// Load all initial data
async function loadData() {
    try {
        // Load players
        const playersResponse = await fetch(API.players);
        const playersData = await playersResponse.json();
        if (playersData.status === 'success') {
            state.players = playersData.data;
        }
        
        // Load stats
        const statsResponse = await fetch(API.stats);
        const statsData = await statsResponse.json();
        if (statsData.status === 'success') {
            state.stats = statsData.data;
        }
        
        // Load raid status
        await loadRaidStatus();
        
        // Render dashboard
        renderDashboard();
        
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

// Load priorities data
async function loadPriorities() {
    try {
        // Get filter values
        const tokenType = elements.tokenFilter.value;
        const stat = elements.statFilter.value;
        const role = elements.roleFilter.value;
        
        // Build query parameters
        let url = API.priorities;
        const params = [];
        if (tokenType) params.push(`token_type=${tokenType}`);
        if (stat) params.push(`stat=${stat}`);
        if (role) params.push(`role=${role}`);
        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }
        
        // Fetch priorities
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            state.priorities = data.data;
            renderPriorities();
        }
    } catch (error) {
        console.error('Error loading priorities:', error);
    }
}

// Load loot history
async function loadLootHistory() {
    try {
        // Get filter values
        const player = elements.playerSearch.value;
        const itemType = elements.itemTypeFilter.value;
        const raidType = elements.raidTypeFilter.value;
        
        // Build query parameters
        let url = API.history;
        const params = [];
        if (player) params.push(`player=${player}`);
        if (itemType) params.push(`item_type=${itemType}`);
        if (raidType) params.push(`raid_type=${raidType}`);
        if (params.length > 0) {
            url += `?${params.join('&')}`;
        }
        
        // Fetch history
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            state.lootHistory = data.data;
            renderLootHistory();
        }
    } catch (error) {
        console.error('Error loading loot history:', error);
    }
}

// Load raid status
async function loadRaidStatus() {
    try {
        const response = await fetch(API.raidStatus);
        const data = await response.json();
        
        if (data.status === 'success') {
            state.activeRaid = data.data;
            renderRaidStatus();
        }
    } catch (error) {
        console.error('Error loading raid status:', error);
    }
}

// Connect to WebSocket
function connectWebSocket() {
    // Close existing connection if any
    if (ws) {
        ws.close();
    }
    
    // Create new WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    // WebSocket event handlers
    ws.onopen = () => {
        console.log('WebSocket connected');
        state.wsConnected = true;
        updateWebSocketStatus(true);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        state.wsConnected = false;
        updateWebSocketStatus(false);
        
        // Try to reconnect after a delay
        setTimeout(connectWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        state.wsConnected = false;
        updateWebSocketStatus(false);
    };
    
    ws.onmessage = (event) => {
        handleWebSocketMessage(event.data);
    };
}

// Update WebSocket connection status UI
function updateWebSocketStatus(connected) {
    const statusEl = elements.wsStatusBody;
    const toastEl = document.getElementById('wsStatus');
    
    if (connected) {
        statusEl.textContent = 'WebSocket connected';
        toastEl.classList.add('ws-connected');
        toastEl.classList.remove('ws-disconnected');
    } else {
        statusEl.textContent = 'WebSocket disconnected. Reconnecting...';
        toastEl.classList.add('ws-disconnected');
        toastEl.classList.remove('ws-connected');
    }
    
    elements.wsStatus.show();
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(data) {
    try {
        const message = JSON.parse(data);
        
        switch (message.type) {
            case 'raid_status':
                state.activeRaid = message.data;
                renderRaidStatus();
                break;
                
            case 'loot_assignment':
                // Add to active raid loot if we're on the raid page
                if (state.activeRaid && state.activeRaid.active) {
                    state.activeRaid.loot_assignments.push(message.data);
                    renderCurrentRaidLoot();
                }
                
                // Refresh dashboard if we're on it
                if (state.activePage === 'dashboard') {
                    loadData();
                }
                break;
                
            case 'priorities':
                state.priorities = message.data;
                if (state.activePage === 'priorities') {
                    renderPriorities();
                }
                break;
                
            default:
                console.log('Received message:', message);
        }
    } catch (error) {
        console.error('Error handling WebSocket message:', error);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Priorities filters
    elements.tokenFilter.addEventListener('change', loadPriorities);
    elements.statFilter.addEventListener('change', loadPriorities);
    elements.roleFilter.addEventListener('change', loadPriorities);
    
    // History filters
    elements.playerSearch.addEventListener('input', debounce(loadLootHistory, 300));
    elements.itemTypeFilter.addEventListener('change', loadLootHistory);
    elements.raidTypeFilter.addEventListener('change', loadLootHistory);
    
    // Raid controls
    elements.startRaidBtn.addEventListener('click', showStartRaidModal);
    elements.endRaidBtn.addEventListener('click', endRaid);
    elements.confirmStartRaid.addEventListener('click', startRaid);
    elements.lootAssignForm.addEventListener('submit', assignLoot);
}

// Render dashboard
function renderDashboard() {
    renderLootDistributionChart();
    renderTokenDistributionChart();
    renderRecentLoot();
}

// Render loot distribution chart
function renderLootDistributionChart() {
    if (!state.stats.slot_distribution) return;
    
    const ctx = elements.lootDistributionChart.getContext('2d');
    
    // Prepare data
    const labels = Object.keys(state.stats.slot_distribution);
    const data = Object.values(state.stats.slot_distribution);
    
    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Items per Slot',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Render token distribution chart
function renderTokenDistributionChart() {
    if (!state.stats.token_distribution) return;
    
    const ctx = elements.tokenDistributionChart.getContext('2d');
    
    // Prepare data
    const labels = Object.keys(state.stats.token_distribution);
    const data = Object.values(state.stats.token_distribution);
    
    // Token colors
    const colors = {
        'Vanquisher': 'rgba(196, 31, 59, 0.7)',
        'Conqueror': 'rgba(245, 140, 186, 0.7)',
        'Protector': 'rgba(0, 112, 222, 0.7)'
    };
    
    const backgroundColor = labels.map(label => colors[label] || 'rgba(128, 128, 128, 0.7)');
    
    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor,
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Render recent loot
function renderRecentLoot() {
    if (!state.lootHistory) return;
    
    const tbody = elements.recentLootTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Get the 10 most recent loot assignments
    const recentLoot = [...state.lootHistory].sort((a, b) => {
        return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
    }).slice(0, 10);
    
    recentLoot.forEach(loot => {
        const row = document.createElement('tr');
        
        // Find player info
        const playerInfo = state.players.find(p => p.name === loot.player) || {};
        const playerClass = playerInfo.class || '';
        
        row.innerHTML = `
            <td class="class-${playerClass.toLowerCase()}">${loot.player}</td>
            <td>${loot.item}</td>
            <td>${loot.item_type}</td>
            <td>${loot.raid_type}</td>
            <td>${loot.date}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Render priorities
function renderPriorities() {
    const tbody = elements.prioritiesTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    state.priorities.forEach((priority, index) => {
        const row = document.createElement('tr');
        
        // Apply class color
        const playerClass = priority.Class || '';
        const tokenClass = priority.Token ? `token-${priority.Token.toLowerCase()}` : '';
        const roleClass = priority.Role ? `role-${priority.Role.toLowerCase()}` : '';
        const statClass = priority.Stat ? `stat-${priority.Stat.toLowerCase()}` : '';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td class="class-${playerClass.toLowerCase()}">${priority.Player}</td>
            <td>${priority.Class}</td>
            <td>${priority.Spec}</td>
            <td><span class="${tokenClass}">${priority.Token}</span></td>
            <td class="${statClass}">${priority.Stat}</td>
            <td>${priority.Score.toFixed(2)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Render loot history
function renderLootHistory() {
    const tbody = elements.historyTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    state.lootHistory.forEach(loot => {
        const row = document.createElement('tr');
        
        // Find player info
        const playerInfo = state.players.find(p => p.name === loot.player) || {};
        const playerClass = playerInfo.class || '';
        
        row.innerHTML = `
            <td class="class-${playerClass.toLowerCase()}">${loot.player}</td>
            <td>${loot.item}</td>
            <td>${loot.item_type}</td>
            <td>${loot.item_slot}</td>
            <td>${loot.raid_type}</td>
            <td>${loot.boss}</td>
            <td>${loot.date}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Render raid status
function renderRaidStatus() {
    if (state.activeRaid && state.activeRaid.active) {
        // We have an active raid
        elements.noActiveRaid.style.display = 'none';
        elements.activeRaidInfo.style.display = 'block';
        elements.startRaidBtn.style.display = 'none';
        elements.endRaidBtn.style.display = 'inline-block';
        elements.assignLootBtn.disabled = false;
        
        // Update raid info
        elements.currentBoss.textContent = state.activeRaid.current_boss || 'Unknown';
        elements.participantCount.textContent = state.activeRaid.participants.length;
        
        // Format start time
        const startTime = new Date(state.activeRaid.start_time);
        elements.raidStartTime.textContent = startTime.toLocaleString();
        
        // Render current raid loot
        renderCurrentRaidLoot();
        
    } else {
        // No active raid
        elements.noActiveRaid.style.display = 'block';
        elements.activeRaidInfo.style.display = 'none';
        elements.startRaidBtn.style.display = 'inline-block';
        elements.endRaidBtn.style.display = 'none';
        elements.assignLootBtn.disabled = true;
        
        // Clear current raid loot
        elements.currentRaidLootTable.querySelector('tbody').innerHTML = '';
    }
    
    // Populate player dropdown for loot assignment
    populatePlayerDropdown();
}

// Render current raid loot
function renderCurrentRaidLoot() {
    if (!state.activeRaid || !state.activeRaid.active) return;
    
    const tbody = elements.currentRaidLootTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    state.activeRaid.loot_assignments.forEach(loot => {
        const row = document.createElement('tr');
        
        // Find player info
        const playerInfo = state.players.find(p => p.name === loot.player) || {};
        const playerClass = playerInfo.class || '';
        
        // Format time
        const time = new Date(loot.timestamp);
        const timeStr = time.toLocaleTimeString();
        
        row.innerHTML = `
            <td class="class-${playerClass.toLowerCase()}">${loot.player}</td>
            <td>${loot.item}</td>
            <td>${loot.boss}</td>
            <td>${timeStr}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Populate player dropdown
function populatePlayerDropdown() {
    const select = elements.playerName;
    
    // Clear existing options except the first one
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // Add players from state
    state.players.forEach(player => {
        const option = document.createElement('option');
        option.value = player.name;
        option.textContent = player.display_name || player.name;
        select.appendChild(option);
    });
}

// Show start raid modal
function showStartRaidModal() {
    // Clear previous values
    elements.raidBoss.value = '';
    elements.participantsList.innerHTML = '';
    
    // Populate participants list
    state.players.forEach(player => {
        const div = document.createElement('div');
        div.innerHTML = `
            <label>
                <input type="checkbox" class="participant-checkbox" value="${player.name}">
                <span class="class-${player.class.toLowerCase()}">${player.display_name || player.name}</span>
            </label>
        `;
        elements.participantsList.appendChild(div);
    });
    
    // Show modal
    elements.startRaidModal.show();
}

// Start a new raid
async function startRaid() {
    try {
        // Get boss name
        const bossName = elements.raidBoss.value.trim();
        if (!bossName) {
            alert('Please enter a boss name');
            return;
        }
        
        // Get selected participants
        const checkboxes = elements.participantsList.querySelectorAll('.participant-checkbox:checked');
        const participants = Array.from(checkboxes).map(cb => cb.value);
        
        if (participants.length === 0) {
            alert('Please select at least one participant');
            return;
        }
        
        // Send request to start raid
        const response = await fetch(API.raidStart, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                boss_name: bossName,
                participants: participants
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Update state and UI
            state.activeRaid = data.data;
            renderRaidStatus();
            
            // Hide modal
            elements.startRaidModal.hide();
        } else {
            alert(`Error starting raid: ${data.message}`);
        }
    } catch (error) {
        console.error('Error starting raid:', error);
        alert('Error starting raid. Please try again.');
    }
}

// End the current raid
async function endRaid() {
    if (!confirm('Are you sure you want to end the current raid?')) {
        return;
    }
    
    try {
        const response = await fetch(API.raidEnd, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Update state and UI
            state.activeRaid = data.data;
            renderRaidStatus();
        } else {
            alert(`Error ending raid: ${data.message}`);
        }
    } catch (error) {
        console.error('Error ending raid:', error);
        alert('Error ending raid. Please try again.');
    }
}

// Assign loot
async function assignLoot(e) {
    e.preventDefault();
    
    try {
        // Get form values
        const itemName = elements.itemName.value.trim();
        const playerName = elements.playerName.value;
        const bossName = elements.bossName.value.trim();
        
        if (!itemName || !playerName) {
            alert('Please enter item name and select a player');
            return;
        }
        
        // Prepare request body
        const body = {
            item_name: itemName,
            player_name: playerName
        };
        
        // Add boss name if provided
        if (bossName) {
            body.boss_name = bossName;
        }
        
        // Send request
        const response = await fetch(API.lootAssign, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Clear form
            elements.itemName.value = '';
            elements.playerName.value = '';
            elements.bossName.value = '';
            
            // Update UI if needed
            if (!state.activeRaid.loot_assignments.some(la => 
                la.item === data.data.item && 
                la.player === data.data.player &&
                la.timestamp === data.data.timestamp
            )) {
                state.activeRaid.loot_assignments.push(data.data);
                renderCurrentRaidLoot();
            }
        } else {
            alert(`Error assigning loot: ${data.message}`);
        }
    } catch (error) {
        console.error('Error assigning loot:', error);
        alert('Error assigning loot. Please try again.');
    }
}

// Utility function: Debounce
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', init); 