// Global state
let allPlayers = [];
let currentRoster = {
    backcourt: [],
    frontcourt: []
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
        
        gameweeks.forEach(gw => {
            const option = document.createElement('option');
            option.value = gw.gameweek;
            option.textContent = gw.label;
            if (gw.gameweek === 9) {  // Default to gameweek 9
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
    
    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeRoster);
    
    // Clear roster button
    document.getElementById('clear-roster-btn').addEventListener('click', clearRoster);
    
    // Budget input
    document.getElementById('available-budget').addEventListener('input', updateBudgetSummary);
    
    // Gameweek selector
    document.getElementById('gameweek-selector').addEventListener('change', () => {
        // Clear previous analysis when gameweek changes
        const analysisContent = document.getElementById('analysis-content');
        analysisContent.innerHTML = '<p class="analysis-placeholder">👈 Click "Analyze" to see recommendations for the selected gameweek</p>';
        // Update schedule if roster is selected
        updateGameSchedule();
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
        item.innerHTML = `
            <div class="player-item-name">${player.player_name}</div>
            <div class="player-item-info">
                ${player.team} | ${player.position} | $${player.salary}M
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
    slot.innerHTML = `
        <div class="player-info">
            <div class="player-name">${player.player_name}</div>
            <div class="player-details">${player.team} | ${player.position}</div>
        </div>
        <div class="player-salary">$${player.salary}M</div>
        <button class="remove-btn" onclick="removePlayer('${position}', ${index})">×</button>
    `;
}

// Remove player from slot
function removePlayer(position, index) {
    currentRoster[position][index] = null;
    
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
async function analyzeRoster() {
    const allPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined);
    
    if (allPlayers.length < 10) {
        alert('Please select all 10 players before analyzing.');
        return;
    }
    
    const availableBudget = parseFloat(document.getElementById('available-budget').value) || 0;
    const selectedGameweek = parseInt(document.getElementById('gameweek-selector').value) || 9;
    const playerIds = allPlayers.map(p => p.player_id);
    
    const analysisContent = document.getElementById('analysis-content');
    analysisContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analyzing your roster...</p></div>';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_roster: playerIds,
                available_budget: availableBudget,
                gameweek: selectedGameweek
            })
        });
        
        const data = await response.json();
        displayAnalysis(data);
    } catch (error) {
        console.error('Error analyzing roster:', error);
        analysisContent.innerHTML = '<p class="error">Failed to analyze roster. Please try again.</p>';
    }
}

// Display analysis results
function displayAnalysis(data) {
    const analysisContent = document.getElementById('analysis-content');
    
    let html = `<h3>📊 Roster Coverage Analysis - Gameweek ${data.gameweek}</h3>`;
    html += `<p style="color: #666; font-size: 0.9rem; margin-bottom: 15px;">${data.date_range}</p>`;
    
    // Day coverage table
    html += '<table class="coverage-table"><thead><tr><th>Game Day</th><th>Players</th><th>BC</th><th>FC</th><th>Status</th></tr></thead><tbody>';
    
    for (const [label, coverage] of Object.entries(data.day_coverage)) {
        const status = coverage.total >= 5 ? 
            '<span class="status-ok">✓ Can field 5</span>' : 
            `<span class="status-warning">⚠️ Need ${5 - coverage.total} more</span>`;
        
        html += `<tr>
            <td><strong>${label}</strong></td>
            <td>${coverage.total}</td>
            <td>${coverage.bc}</td>
            <td>${coverage.fc}</td>
            <td>${status}</td>
        </tr>`;
    }
    html += '</tbody></table>';
    
    // Insufficient days warning
    if (data.insufficient_days.length > 0) {
        html += '<div class="warning-box" style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">';
        html += '<h4 style="color: #856404; margin-bottom: 10px;">⚠️ Problem Days Detected</h4>';
        html += '<p>The following days have insufficient players to field a starting 5:</p><ul>';
        data.insufficient_days.forEach(day => {
            html += `<li><strong>${day.label}</strong>: ${day.total} players (need ${day.needed} more)</li>`;
        });
        html += '</ul></div>';
    }
    
    // Recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += '<h3 style="margin-top: 30px;">💡 Recommended Transactions</h3>';
        html += '<p style="color: #666; margin-bottom: 15px;">Here are the best transaction options to improve your roster depth:</p>';
        
        data.recommendations.forEach((rec, index) => {
            html += `<div class="recommendation-card">`;
            html += `<h4>Option ${index + 1}</h4>`;
            
            // Drops
            html += '<div class="transaction"><strong class="drop">DROP:</strong><ul>';
            rec.drops.forEach(drop => {
                const fpStr = drop.fantasy_avg > 0 ? `, ${drop.fantasy_avg.toFixed(1)} FP/G` : '';
                html += `<li>${drop.name} (${drop.position}, $${drop.salary}M${fpStr})</li>`;
            });
            html += '</ul></div>';
            
            // Adds
            html += '<div class="transaction"><strong class="add">ADD:</strong><ul>';
            rec.adds.forEach(add => {
                const fpStr = add.fantasy_avg > 0 ? `, ${add.fantasy_avg.toFixed(1)} FP/G` : '';
                html += `<li>${add.name} (${add.position}, $${add.salary}M, ${add.games} games${fpStr})</li>`;
            });
            html += '</ul></div>';
            
            // Impact summary
            html += '<div style="margin-top: 15px; padding: 10px; background: white; border-radius: 6px;">';
            const costStr = rec.cost >= 0 ? `+$${rec.cost.toFixed(1)}M` : `-$${Math.abs(rec.cost).toFixed(1)}M`;
            html += `<p><strong>Net Cost:</strong> ${costStr}</p>`;
            
            if (rec.fp_improvement !== undefined) {
                const fpColor = rec.fp_improvement > 0 ? '#2ecc71' : '#ff4757';
                const fpStr = rec.fp_improvement >= 0 ? `+${rec.fp_improvement.toFixed(1)}` : rec.fp_improvement.toFixed(1);
                html += `<p><strong>Fantasy Points:</strong> <span style="color: ${fpColor};">${fpStr} FP/G</span></p>`;
            }
            
            if (rec.depth_score !== undefined && rec.depth_score > 0) {
                html += `<p><strong>Roster Depth:</strong> <span style="color: #2ecc71;">Improves coverage on problem days ✓</span></p>`;
            }
            html += '</div>';
            
            html += '</div>';
        });
    } else {
        html += '<div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 20px;">';
        html += '<p style="color: #155724;"><strong>✓ Your roster looks good!</strong> All days have sufficient player coverage.</p>';
        html += '</div>';
    }
    
    analysisContent.innerHTML = html;
}

// Save roster to localStorage
function saveRoster() {
    const rosterData = {
        backcourt: currentRoster.backcourt.filter(p => p !== null && p !== undefined),
        frontcourt: currentRoster.frontcourt.filter(p => p !== null && p !== undefined)
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
                // Find the full player object from allPlayers
                const player = allPlayers.find(p => p.player_id === playerData.player_id);
                if (player && index < 5) {
                    currentRoster.backcourt[index] = player;
                    updatePlayerSlot('backcourt', index, player);
                }
            });
        }
        
        // Restore frontcourt
        if (rosterData.frontcourt) {
            rosterData.frontcourt.forEach((playerData, index) => {
                const player = allPlayers.find(p => p.player_id === playerData.player_id);
                if (player && index < 5) {
                    currentRoster.frontcourt[index] = player;
                    updatePlayerSlot('frontcourt', index, player);
                }
            });
        }
        
        updateBudgetSummary();
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
    analysisContent.innerHTML = '<p class="analysis-placeholder">👈 Select your roster and click "Analyze" to see recommendations</p>';
    
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
}

// Update game schedule for current roster
async function updateGameSchedule() {
    const scheduleContent = document.getElementById('schedule-content');
    const gameweek = parseInt(document.getElementById('gameweek-selector').value);
    
    // Get all selected players
    const allPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined);
    
    if (allPlayers.length === 0) {
        scheduleContent.innerHTML = '<p class="schedule-placeholder">📅 Select your roster to see the game schedule for the selected gameweek</p>';
        return;
    }
    
    scheduleContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading game schedule...</p></div>';
    
    try {
        const playerIds = allPlayers.map(p => p.player_id);
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
        
        const data = await response.json();
        displayGameSchedule(data, allPlayers);
    } catch (error) {
        console.error('Error loading game schedule:', error);
        scheduleContent.innerHTML = '<p class="error">Failed to load game schedule. Please try again.</p>';
    }
}

// Display game schedule
function displayGameSchedule(data, allPlayers) {
    const scheduleContent = document.getElementById('schedule-content');
    
    if (!data.games_by_day || Object.keys(data.games_by_day).length === 0) {
        scheduleContent.innerHTML = '<div class="no-games"><p>No games found for the selected gameweek.</p></div>';
        return;
    }
    
    // Create summary
    const totalGames = Object.values(data.games_by_day).reduce((sum, games) => sum + games.length, 0);
    const playersWithGames = new Set();
    Object.values(data.games_by_day).forEach(games => {
        games.forEach(game => {
            game.players.forEach(p => playersWithGames.add(p.player_id));
        });
    });
    
    let html = `
        <div class="schedule-summary">
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-value">${totalGames}</div>
                    <div class="stat-label">Total Games</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${playersWithGames.size}</div>
                    <div class="stat-label">Players with Games</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${allPlayers.length - playersWithGames.size}</div>
                    <div class="stat-label">Players without Games</div>
                </div>
            </div>
        </div>
        <div class="schedule-grid">
    `;
    
    // Sort days chronologically
    const sortedDays = Object.keys(data.games_by_day).sort();
    
    sortedDays.forEach(day => {
        const games = data.games_by_day[day];
        const dayDate = new Date(day);
        const dayName = dayDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
        
        html += `
            <div class="game-day">
                <div class="game-day-header">${dayName} - ${games.length} game${games.length !== 1 ? 's' : ''}</div>
                <div class="game-list">
        `;
        
        games.forEach(game => {
            html += `
                <div class="game-item">
                    <div class="game-matchup">${game.matchup}</div>
                    <div class="game-time">${game.time || 'TBD'}</div>
                    <div class="game-players">
                        ${game.players.map(p => `<span class="player-badge">${p.player_name} (${p.team})</span>`).join('')}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    scheduleContent.innerHTML = html;
}
