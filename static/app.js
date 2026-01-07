// Global state
let allPlayers = [];
let currentRoster = {
    backcourt: [null, null, null, null, null],
    frontcourt: [null, null, null, null, null]
};
let currentSlot = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadPlayers();
    loadGameweeks();
    initializeRosterSlots();
    setupEventListeners();
    loadSavedRoster();
});

// Load all players from API
async function loadPlayers() {
    try {
        const response = await fetch('/api/players');
        allPlayers = await response.json();
        console.log(`Loaded ${allPlayers.length} players`);
    } catch (error) {
        console.error('Error loading players:', error);
        alert('Failed to load players. Please refresh the page.');
    }
}

// Load gameweeks
async function loadGameweeks() {
    try {
        const response = await fetch('/api/gameweeks');
        const gameweeks = await response.json();
        
        const selector = document.getElementById('gameweek-selector');
        selector.innerHTML = '';
        
        // Find the current or most recent active gameweek
        let defaultGameweek = gameweeks.find(gw => gw.status === 'active') || 
                             gameweeks.find(gw => gw.status === 'upcoming') ||
                             gameweeks[gameweeks.length - 1];
        
        gameweeks.forEach(gw => {
            const option = document.createElement('option');
            option.value = gw.gameweek;
            option.textContent = gw.label;
            
            // Select the current/active gameweek by default
            if (defaultGameweek && gw.gameweek === defaultGameweek.gameweek) {
                option.selected = true;
            }
            
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading gameweeks:', error);
    }
}

// Initialize empty roster slots
function initializeRosterSlots() {
    const backcourtContainer = document.getElementById('backcourt-roster');
    const frontcourtContainer = document.getElementById('frontcourt-roster');
    
    // Create 5 backcourt slots
    for (let i = 0; i < 5; i++) {
        backcourtContainer.appendChild(createPlayerSlot('backcourt', i));
    }
    
    // Create 5 frontcourt slots
    for (let i = 0; i < 5; i++) {
        frontcourtContainer.appendChild(createPlayerSlot('frontcourt', i));
    }
}

// Create a player slot
function createPlayerSlot(position, index) {
    const slot = document.createElement('div');
    slot.className = 'player-slot';
    slot.dataset.position = position;
    slot.dataset.index = index;
    
    slot.innerHTML = `
        <div class="player-info">
            <div class="player-name">Empty Slot</div>
            <div class="player-details">Click to select player</div>
        </div>
        <div class="player-salary">$0.0M</div>
    `;
    
    slot.addEventListener('click', () => openPlayerModal(position, index));
    
    return slot;
}

// Setup event listeners
function setupEventListeners() {
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Close modal
    document.querySelector('.close').addEventListener('click', closePlayerModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('player-modal');
        if (e.target === modal) {
            closePlayerModal();
        }
    });
    
    // Player search
    document.getElementById('player-search').addEventListener('input', (e) => {
        filterPlayers(e.target.value);
    });
    
    // Clear roster button
    document.getElementById('clear-roster-btn').addEventListener('click', clearRoster);
    
    // Budget input
    document.getElementById('available-budget').addEventListener('input', updateBudgetSummary);
    
    // Gameweek selector
    document.getElementById('gameweek-selector').addEventListener('change', () => {
        // Update schedule if roster is selected
        updateGameSchedule();
        // Update team schedule if on teams tab
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab && activeTab.dataset.tab === 'teams') {
            loadTeamSchedule();
        }
        // Auto-reload analysis if on analysis tab
        if (activeTab && activeTab.dataset.tab === 'analysis') {
            analyzeRoster();
        }
    });
}

// Open player selection modal
function openPlayerModal(position, index) {
    currentSlot = { position, index };
    const modal = document.getElementById('player-modal');
    
    // Filter players by position
    const validPlayers = allPlayers.filter(p => {
        if (position === 'backcourt') {
            return p.position.includes('G');
        } else {
            return p.position.includes('F') || p.position.includes('C');
        }
    });
    
    displayPlayerList(validPlayers);
    modal.style.display = 'block';
}

// Close player modal
function closePlayerModal() {
    document.getElementById('player-modal').style.display = 'none';
    document.getElementById('player-search').value = '';
    currentSlot = null;
}

// Display player list in modal
function displayPlayerList(players) {
    const playerList = document.getElementById('player-list');
    playerList.innerHTML = '';
    
    players.forEach(player => {
        const item = document.createElement('div');
        item.className = 'player-item';
        const fpAvg = player.fantasy_avg ? player.fantasy_avg.toFixed(1) : 'N/A';
        item.innerHTML = `
            <div class="player-item-name">${player.player_name}</div>
            <div class="player-item-info">
                ${player.team} | ${player.position} | $${player.salary}M | ${fpAvg} FP/G
            </div>
        `;
        
        item.addEventListener('click', () => selectPlayer(player));
        playerList.appendChild(item);
    });
}

// Filter players by search term
function filterPlayers(searchTerm) {
    const term = searchTerm.toLowerCase();
    const filtered = allPlayers.filter(p => {
        const matchesSearch = p.player_name.toLowerCase().includes(term) ||
                            p.team.toLowerCase().includes(term);
        
        if (currentSlot.position === 'backcourt') {
            return matchesSearch && p.position.includes('G');
        } else {
            return matchesSearch && (p.position.includes('F') || p.position.includes('C'));
        }
    });
    
    displayPlayerList(filtered);
}

// Select a player for a slot
function selectPlayer(player) {
    const { position, index } = currentSlot;
    
    // Add to roster
    currentRoster[position][index] = player;
    
    // Clear cached analysis since roster changed
    lastAnalysisRosterSignature = null;
    currentAnalysisData = null;
    
    // Update UI
    updatePlayerSlot(position, index, player);
    updateBudgetSummary();
    updateGameSchedule();
    closePlayerModal();
    
    // Save roster to localStorage
    saveRoster();
}

// Update player slot UI
function updatePlayerSlot(position, index, player) {
    const container = document.getElementById(`${position}-roster`);
    const slot = container.children[index];
    
    slot.classList.add('filled');
    const fpAvg = player.fantasy_avg ? player.fantasy_avg.toFixed(1) : 'N/A';
    slot.innerHTML = `
        <div class="player-info">
            <div class="player-name">${player.player_name}</div>
            <div class="player-details">${player.team} | ${player.position} | ${fpAvg} FP/G</div>
        </div>
        <div class="player-salary">$${player.salary}M</div>
        <button class="remove-btn" onclick="removePlayer('${position}', ${index})">×</button>
    `;
}

// Remove player from slot
function removePlayer(position, index) {
    currentRoster[position][index] = null;
    
    // Clear cached analysis since roster changed
    lastAnalysisRosterSignature = null;
    currentAnalysisData = null;
    
    const container = document.getElementById(`${position}-roster`);
    const slot = container.children[index];
    
    slot.className = 'player-slot';
    slot.innerHTML = `
        <div class="player-info">
            <div class="player-name">Empty Slot</div>
            <div class="player-details">Click to select player</div>
        </div>
        <div class="player-salary">$0.0M</div>
    `;
    
    slot.addEventListener('click', () => openPlayerModal(position, index));
    updateBudgetSummary();
    updateGameSchedule();
    
    // Save roster to localStorage
    saveRoster();
}

// Update budget summary
function updateBudgetSummary() {
    const allPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined);
    
    const totalSalary = allPlayers.reduce((sum, p) => sum + (p.salary || 0), 0);
    const availableBudget = parseFloat(document.getElementById('available-budget').value) || 0;
    const totalBudget = totalSalary + availableBudget;
    
    document.getElementById('total-salary').textContent = totalSalary.toFixed(1);
    document.getElementById('total-budget').textContent = totalBudget.toFixed(1);
}

// Analyze roster and get recommendations












// Build schedule HTML (reusable for both views)
function buildScheduleHTML(data, playersList, recommendation = null) {
    if (!data.games_by_day || Object.keys(data.games_by_day).length === 0) {
        return '<p class="schedule-placeholder">No games found for this gameweek</p>';
    }
    
    console.log('Building schedule for', playersList.length, 'players');
    
    // Count players per day
    const dayPlayerCounts = {};
    const dayPlayerDetails = {};
    
    for (const [day, dayData] of Object.entries(data.games_by_day)) {
        const games = dayData.games || dayData;
        dayPlayerCounts[day] = 0;
        dayPlayerDetails[day] = { backcourt: [], frontcourt: [] };
        
        const playersThisDay = new Set();
        
        games.forEach(game => {
            game.players.forEach(player => {
                if (!playersThisDay.has(player.player_id)) {
                    playersThisDay.add(player.player_id);
                    dayPlayerCounts[day]++;
                    
                    if (player.position === 'Backcourt') {
                        dayPlayerDetails[day].backcourt.push(player);
                    } else {
                        dayPlayerDetails[day].frontcourt.push(player);
                    }
                }
            });
        });
    }
    
    const totalGames = Object.values(data.games_by_day).reduce((sum, dayData) => {
        const games = dayData.games || dayData;
        return sum + (Array.isArray(games) ? games.length : 0);
    }, 0);
    
    let html = '';
    
    // Show transaction summary if this is a recommended roster
    if (recommendation) {
        html += '<div style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 3px solid #3b82f6;">';
        html += '<p style="margin: 0 0 8px 0; font-weight: bold; color: #1e40af;">Changes:</p>';
        html += '<p style="margin: 0; font-size: 0.9rem;">🔴 <strong>OUT:</strong> ' + recommendation.drops.map(d => d.name).join(', ') + '</p>';
        html += '<p style="margin: 5px 0 0 0; font-size: 0.9rem;">🟢 <strong>IN:</strong> ' + recommendation.adds.map(a => a.name).join(', ') + '</p>';
        html += '</div>';
    }
    
    // Calculate total projected FP across all days
    const totalProjectedFP = Object.values(data.games_by_day).reduce((sum, dayData) => {
        return sum + (dayData.projected_fp || 0);
    }, 0);
    
    html += `
        <div class="schedule-summary">
            <div class="summary-stat">
                <div class="stat-value">${playersList.length}</div>
                <div class="stat-label">Players</div>
            </div>
            <div class="summary-stat">
                <div class="stat-value">${totalGames}</div>
                <div class="stat-label">Total Games</div>
            </div>
            <div class="summary-stat" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div class="stat-value" style="color: white;">${totalProjectedFP.toFixed(1)}</div>
                <div class="stat-label" style="color: rgba(255,255,255,0.9);">Projected FP</div>
            </div>
        </div>
        
        <div class="schedule-table-container">
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th>Game Day</th>
                        <th>Players</th>
                        <th>BC</th>
                        <th>FC</th>
                        <th>Proj. FP</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Sort days
    const sortedDays = Object.keys(data.games_by_day).sort((a, b) => {
        const gwRegex = /GW(\d+) Day (\d+)/;
        const matchA = a.match(gwRegex);
        const matchB = b.match(gwRegex);
        
        if (matchA && matchB) {
            const gwA = parseInt(matchA[1]);
            const gwB = parseInt(matchB[1]);
            if (gwA !== gwB) return gwA - gwB;
            return parseInt(matchA[2]) - parseInt(matchB[2]);
        }
        return new Date(a) - new Date(b);
    });
    
    sortedDays.forEach(day => {
        let dayName;
        if (day.includes('GW')) {
            dayName = day;
        } else {
            const dayDate = new Date(day + 'T00:00:00');
            dayName = dayDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
        }
        
        const playerCount = dayPlayerCounts[day];
        const bcCount = dayPlayerDetails[day].backcourt.length;
        const fcCount = dayPlayerDetails[day].frontcourt.length;
        const isReady = playerCount >= 5;
        const statusClass = isReady ? 'status-ready' : 'status-warning';
        const statusIcon = isReady ? '✓' : '⚠';
        
        const dayData = data.games_by_day[day];
        const projectedFP = dayData.projected_fp || 0;
        const playerProjections = dayData.player_projections || [];
        
        // Create tooltip with player breakdown and starter indicators
        let tooltipHTML = '';
        if (playerProjections.length > 0) {
            tooltipHTML = '<div class="fp-tooltip"><div class="fp-tooltip-header">Projected Points:</div>';
            playerProjections.forEach(pp => {
                const starterIcon = pp.is_starter ? '👑 ' : '';
                const starterClass = pp.is_starter ? 'starter-player' : '';
                tooltipHTML += `<div class="fp-tooltip-row ${starterClass}">${starterIcon}${pp.player_name} (${pp.team}): <strong>${pp.projected_fp} FP</strong></div>`;
            });
            tooltipHTML += '<div class="fp-tooltip-footer">👑 = Top 5 starters (based on last 5 games avg + total FP)</div></div>';
        }
        
        html += `
            <tr class="schedule-day-row ${statusClass}" data-day="${day}">
                <td class="day-name"><strong>${dayName}</strong></td>
                <td class="player-count">${playerCount}</td>
                <td class="position-count">${bcCount}</td>
                <td class="position-count">${fcCount}</td>
                <td class="projected-fp" title="Based on last 7 games average">
                    <span class="fp-value">${projectedFP.toFixed(1)}</span>
                    ${tooltipHTML}
                </td>
                <td class="day-status">
                    <span class="status-badge ${statusClass}">${statusIcon} ${isReady ? 'Ready' : `Need ${5 - playerCount}`}</span>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// Save roster to localStorage
function saveRoster() {
    const rosterData = {
        backcourt: currentRoster.backcourt.map(p => p ? { player_id: p.player_id, player_name: p.player_name, position: p.position, salary: p.salary, team: p.team } : null),
        frontcourt: currentRoster.frontcourt.map(p => p ? { player_id: p.player_id, player_name: p.player_name, position: p.position, salary: p.salary, team: p.team } : null)
    };
    localStorage.setItem('nba_fantasy_roster', JSON.stringify(rosterData));
}

// Load saved roster from localStorage
async function loadSavedRoster() {
    // Wait for players to be loaded
    while (allPlayers.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    const savedData = localStorage.getItem('nba_fantasy_roster');
    if (!savedData) {
        return;
    }
    
    try {
        const rosterData = JSON.parse(savedData);
        
        // Restore backcourt
        if (rosterData.backcourt) {
            rosterData.backcourt.forEach((playerData, index) => {
                if (playerData && index < 5) {
                    // Find the full player object from allPlayers
                    const player = allPlayers.find(p => p.player_id === playerData.player_id);
                    if (player) {
                        currentRoster.backcourt[index] = player;
                        updatePlayerSlot('backcourt', index, player);
                    }
                }
            });
        }
        
        // Restore frontcourt
        if (rosterData.frontcourt) {
            rosterData.frontcourt.forEach((playerData, index) => {
                if (playerData && index < 5) {
                    const player = allPlayers.find(p => p.player_id === playerData.player_id);
                    if (player) {
                        currentRoster.frontcourt[index] = player;
                        updatePlayerSlot('frontcourt', index, player);
                    }
                }
            });
        }
        
        updateBudgetSummary();
        updateGameSchedule();
        console.log('Loaded saved roster from localStorage');
    } catch (error) {
        console.error('Error loading saved roster:', error);
        localStorage.removeItem('nba_fantasy_roster');
    }
}

// Clear entire roster
function clearRoster() {
    if (!confirm('Are you sure you want to clear your entire roster?')) {
        return;
    }
    
    // Clear backcourt
    for (let i = 0; i < 5; i++) {
        if (currentRoster.backcourt[i]) {
            removePlayer('backcourt', i);
        }
    }
    
    // Clear frontcourt
    for (let i = 0; i < 5; i++) {
        if (currentRoster.frontcourt[i]) {
            removePlayer('frontcourt', i);
        }
    }
    
    // Clear localStorage
    localStorage.removeItem('nba_fantasy_roster');
    
    // Clear analysis
    const analysisContent = document.getElementById('analysis-content');
    analysisContent.innerHTML = '<p class="analysis-placeholder">👈 Select your roster and click "Analysis & Recommendations" tab</p>';
    
    // Clear schedule
    const scheduleContent = document.getElementById('schedule-content');
    scheduleContent.innerHTML = '<p class="schedule-placeholder">📅 Select your roster to see the game schedule for the selected gameweek</p>';
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load team schedule if switching to teams tab
    if (tabName === 'teams') {
        loadTeamSchedule();
    }
}

// Update game schedule for current roster
async function updateGameSchedule() {
    const scheduleContent = document.getElementById('schedule-content');
    const gameweek = parseInt(document.getElementById('gameweek-selector').value);
    
    // Get all selected players
    const selectedPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined);
    
    if (selectedPlayers.length === 0) {
        scheduleContent.innerHTML = '<p class="schedule-placeholder">📅 Select your roster to see the game schedule for the selected gameweek</p>';
        return;
    }
    
    scheduleContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading game schedule...</p></div>';
    
    try {
        const playerIds = selectedPlayers.map(p => p.player_id);
        const response = await fetch('/api/game_schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_ids: playerIds,
                gameweek: gameweek
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayGameSchedule(data, selectedPlayers);
    } catch (error) {
        console.error('Error loading game schedule:', error);
        scheduleContent.innerHTML = '<p class="error">Failed to load game schedule. Please try again.</p>';
    }
}

// Display game schedule
function displayGameSchedule(data, selectedPlayers) {
    const scheduleContent = document.getElementById('schedule-content');
    
    if (!data.games_by_day || Object.keys(data.games_by_day).length === 0) {
        scheduleContent.innerHTML = '<div class="no-games"><p>No games found for the selected gameweek.</p></div>';
        return;
    }
    
    // Calculate player counts per fantasy gameday
    // Sort fantasy gamedays: GW format first, then dates
    const sortedDays = Object.keys(data.games_by_day).sort((a, b) => {
        // Extract gameweek and day numbers if in GW format
        const gwRegex = /GW(\d+) Day (\d+)/;
        const matchA = a.match(gwRegex);
        const matchB = b.match(gwRegex);
        
        if (matchA && matchB) {
            // Both are GW format, compare by week then day
            const gwA = parseInt(matchA[1]);
            const gwB = parseInt(matchB[1]);
            if (gwA !== gwB) return gwA - gwB;
            return parseInt(matchA[2]) - parseInt(matchB[2]);
        } else if (matchA) {
            return -1;  // GW format comes first
        } else if (matchB) {
            return 1;
        } else {
            // Both are dates, sort chronologically
            return a.localeCompare(b);
        }
    });
    const dayPlayerCounts = {};
    const dayPlayerDetails = {};
    
    sortedDays.forEach(day => {
        const playersThisDay = new Set();
        const playersByPosition = { backcourt: [], frontcourt: [] };
        
        const dayData = data.games_by_day[day];
        const games = dayData.games || dayData;  // Handle both old and new format
        const playerProjections = dayData.player_projections || [];
        
        // Create a map of player_id to projection data for quick lookup
        const projectionMap = {};
        playerProjections.forEach(proj => {
            projectionMap[proj.player_id] = proj;
        });
        
        games.forEach(game => {
            game.players.forEach(p => {
                playersThisDay.add(p.player_id);
                const playerData = selectedPlayers.find(sp => sp.player_id === p.player_id);
                if (playerData) {
                    const position = playerData.position.includes('G') ? 'backcourt' : 'frontcourt';
                    const projection = projectionMap[p.player_id];
                    if (!playersByPosition[position].some(existing => existing.player_id === p.player_id)) {
                        playersByPosition[position].push({
                            ...p,
                            matchup: game.matchup,
                            is_starter: projection ? projection.is_starter : false
                        });
                    }
                }
            });
        });
        
        dayPlayerCounts[day] = playersThisDay.size;
        dayPlayerDetails[day] = playersByPosition;
    });
    
    // Summary stats
    const totalGames = Object.values(data.games_by_day).reduce((sum, dayData) => {
        const games = dayData.games || dayData;  // Handle both formats
        return sum + (Array.isArray(games) ? games.length : 0);
    }, 0);
    const daysWithEnoughPlayers = Object.values(dayPlayerCounts).filter(count => count >= 5).length;
    const daysWithIssues = sortedDays.length - daysWithEnoughPlayers;
    
    let html = `
        <div class="schedule-summary">
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">${totalGames}</div>
                    <div class="stat-label">Total Games</div>
                </div>
                <div class="stat-item ${daysWithEnoughPlayers === sortedDays.length ? 'stat-ok' : ''}">
                    <div class="stat-value">${daysWithEnoughPlayers}</div>
                    <div class="stat-label">Days Ready</div>
                </div>
                <div class="stat-item ${daysWithIssues > 0 ? 'stat-warning' : ''}">
                    <div class="stat-value">${daysWithIssues}</div>
                    <div class="stat-label">Days Need Attention</div>
                </div>
            </div>
        </div>
        
        <div class="schedule-table-wrapper">
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th>Game Day</th>
                        <th>Players</th>
                        <th>BC</th>
                        <th>FC</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    sortedDays.forEach(day => {
        // Handle fantasy gameday labels like "GW9 Day 1" or fallback to date
        let dayName = day;
        if (day.includes('GW')) {
            dayName = day;  // Already formatted as "GW9 Day 1"
        } else {
            const dayDate = new Date(day + 'T00:00:00');
            dayName = dayDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
        }
        
        const playerCount = dayPlayerCounts[day];
        const bcCount = dayPlayerDetails[day].backcourt.length;
        const fcCount = dayPlayerDetails[day].frontcourt.length;
        const isReady = playerCount >= 5;
        const statusClass = isReady ? 'status-ready' : 'status-warning';
        const statusIcon = isReady ? '✓' : '⚠';
        
        // Build player list for this day with starter indicators and FP average
        const dayData = data.games_by_day[day];
        const playerProjections = dayData.player_projections || [];
        const projectionMap = {};
        playerProjections.forEach(proj => {
            projectionMap[proj.player_id] = proj;
        });
        
        let playerList = [];
        if (dayPlayerDetails[day].backcourt.length > 0) {
            playerList.push(...dayPlayerDetails[day].backcourt.map(p => {
                const starterIcon = p.is_starter ? '👑 ' : '';
                const starterClass = p.is_starter ? 'starter-chip' : '';
                const projection = projectionMap[p.player_id];
                const avgFP = projection ? ` (${projection.avg_last_5.toFixed(1)})` : '';
                return `<span class="player-chip bc ${starterClass}">${starterIcon}${p.player_name}${avgFP}</span>`;
            }));
        }
        if (dayPlayerDetails[day].frontcourt.length > 0) {
            playerList.push(...dayPlayerDetails[day].frontcourt.map(p => {
                const starterIcon = p.is_starter ? '👑 ' : '';
                const starterClass = p.is_starter ? 'starter-chip' : '';
                const projection = projectionMap[p.player_id];
                const avgFP = projection ? ` (${projection.avg_last_5.toFixed(1)})` : '';
                return `<span class="player-chip fc ${starterClass}">${starterIcon}${p.player_name}${avgFP}</span>`;
            }));
        }
        
        html += `
            <tr class="schedule-day-row ${statusClass}">
                <td class="day-name">
                    <strong>${dayName}</strong>
                </td>
                <td class="player-count ${playerCount < 5 ? 'count-warning' : 'count-ok'}">${playerCount}</td>
                <td class="position-count">${bcCount}</td>
                <td class="position-count">${fcCount}</td>
                <td class="day-status">
                    <span class="status-badge ${statusClass}">${statusIcon} ${isReady ? 'Ready' : `Need ${5 - playerCount}`}</span>
                </td>
            </tr>
            <tr class="day-players-row">
                <td colspan="5">
                    <div class="day-players-content">
                        ${playerList.length > 0 ? playerList.join(' ') : '<span class="no-players">No players scheduled</span>'}
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    scheduleContent.innerHTML = html;
}

// Load team schedule for the top teams tab
async function loadTeamSchedule() {
    const teamsContent = document.getElementById('teams-content');
    const gameweek = parseInt(document.getElementById('gameweek-selector').value) || 9;
    
    teamsContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading team data...</p></div>';
    
    try {
        const response = await fetch(`/api/team_schedule/${gameweek}`);
        const data = await response.json();
        
        // Get team IDs from current roster
        const rosterTeamIds = new Set();
        const allRosterPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
            .filter(p => p !== null && p !== undefined);
        allRosterPlayers.forEach(player => {
            if (player.team_id) {
                rosterTeamIds.add(player.team_id);
            }
        });
        
        let html = `
            <div class="teams-header">
                <h3>🏆 All Teams - Gameweek ${data.gameweek}</h3>
                <p style="color: #666; margin-bottom: 20px;">${data.date_range}</p>
            </div>
            <div class="teams-list">
        `;
        
        data.teams.forEach((team, index) => {
            const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            const rankClass = index < 3 ? 'top-three' : '';
            const hasRosterPlayer = rosterTeamIds.has(team.team_id);
            const rosterClass = hasRosterPlayer ? 'has-roster-player' : '';
            const rosterIndicator = hasRosterPlayer ? ' <span class="roster-indicator">👤 Your Team</span>' : '';
            
            html += `
                <div class="team-card ${rankClass} ${rosterClass}" onclick="showTeamPlayers(${team.team_id}, '${team.team_name}')" style="cursor: pointer;">
                    <div class="team-header">
                        <span class="team-rank">${rankEmoji}</span>
                        <span class="team-name">${team.team_name}${rosterIndicator}</span>
                        <span class="team-abbr">${team.team_abbreviation}</span>
                        <span class="team-stats">
                            <strong>${team.game_days}</strong> ${team.game_days === 1 ? 'day' : 'days'} • 
                            <strong>${team.total_games}</strong> ${team.total_games === 1 ? 'game' : 'games'}
                        </span>
                    </div>
                    <div class="team-games">
            `;
            
            // Group games by date
            const gamesByDate = {};
            team.games.forEach(game => {
                if (!gamesByDate[game.date]) {
                    gamesByDate[game.date] = [];
                }
                gamesByDate[game.date].push(game);
            });
            
            // Display games by date
            Object.keys(gamesByDate).sort().forEach(date => {
                const dateObj = new Date(date + 'T00:00:00');
                const formattedDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });
                
                html += `<div class="game-date-group">`;
                html += `<span class="game-date">${formattedDate}</span>`;
                
                gamesByDate[date].forEach(game => {
                    const gameType = game.type === 'vs' ? '🏠 vs' : '✈️ @';
                    html += `<span class="game-matchup">${gameType} ${game.opponent}</span>`;
                });
                
                html += `</div>`;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
        
        teamsContent.innerHTML = html;
    } catch (error) {
        console.error('Error loading team schedule:', error);
        teamsContent.innerHTML = '<p style="color: #ff4757;">Failed to load team data. Please try again.</p>';
    }
}

// Show team players modal when clicking on a team
async function showTeamPlayers(teamId, teamName) {
    const modal = document.getElementById('team-players-modal');
    const modalBody = modal.querySelector('.modal-body');
    
    modal.style.display = 'block';
    modal.querySelector('h2').textContent = `${teamName} - Players`;
    modalBody.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading team players...</p></div>';
    
    try {
        const response = await fetch(`/api/team_players/${teamId}`);
        const data = await response.json();
        
        if (data.error) {
            modalBody.innerHTML = `<p style="color: #ff4757;">${data.error}</p>`;
            return;
        }
        
        let html = '';
        
        // Display backcourt
        if (data.backcourt && data.backcourt.length > 0) {
            html += `
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #2196f3; margin-bottom: 15px; border-bottom: 2px solid #2196f3; padding-bottom: 8px;">🔵 Backcourt (${data.backcourt.length} players)</h3>
                    <div style="display: grid; gap: 12px;">
            `;
            
            data.backcourt.forEach(player => {
                const avgFp = player.fantasy_avg ? player.fantasy_avg.toFixed(1) : 'N/A';
                const avgMin = player.avg_minutes ? player.avg_minutes.toFixed(1) : 'N/A';
                html += `
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div>
                            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 5px;">${player.player_name}</div>
                            <div style="font-size: 0.85rem; color: #666;">
                                ${player.position} | $${player.salary}M
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 600; color: #2196f3; font-size: 1.2rem;">${avgFp} FP/G</div>
                            <div style="font-size: 0.8rem; color: #666;">${avgMin} min/g</div>
                            <div style="font-size: 0.75rem; color: #999; margin-top: 2px;">${player.games_played} games</div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div></div>`;
        }
        
        // Display frontcourt
        if (data.frontcourt && data.frontcourt.length > 0) {
            html += `
                <div>
                    <h3 style="color: #f44336; margin-bottom: 15px; border-bottom: 2px solid #f44336; padding-bottom: 8px;">🔴 Frontcourt (${data.frontcourt.length} players)</h3>
                    <div style="display: grid; gap: 12px;">
            `;
            
            data.frontcourt.forEach(player => {
                const avgFp = player.fantasy_avg ? player.fantasy_avg.toFixed(1) : 'N/A';
                const avgMin = player.avg_minutes ? player.avg_minutes.toFixed(1) : 'N/A';
                html += `
                    <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #f44336; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div>
                            <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 5px;">${player.player_name}</div>
                            <div style="font-size: 0.85rem; color: #666;">
                                ${player.position} | $${player.salary}M
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 600; color: #f44336; font-size: 1.2rem;">${avgFp} FP/G</div>
                            <div style="font-size: 0.8rem; color: #666;">${avgMin} min/g</div>
                            <div style="font-size: 0.75rem; color: #999; margin-top: 2px;">${player.games_played} games</div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div></div>`;
        }
        
        if (!data.backcourt.length && !data.frontcourt.length) {
            html = '<p style="text-align: center; color: #666; padding: 20px;">No player data available for this team.</p>';
        }
        
        modalBody.innerHTML = html;
    } catch (error) {
        console.error('Error loading team players:', error);
        modalBody.innerHTML = '<p style="color: #ff4757;">Failed to load team players. Please try again.</p>';
    }
}

// Close team players modal
function closeTeamPlayersModal() {
    document.getElementById('team-players-modal').style.display = 'none';
}
