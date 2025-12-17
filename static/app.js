// Global state
let allPlayers = [];
let currentRoster = {
    backcourt: [null, null, null, null, null],
    frontcourt: [null, null, null, null, null]
};
let currentSlot = null;
let currentRecommendations = [];
let currentAnalysisData = null;
let selectedComparisonRecIndex = 0;
let lastAnalysisGameweek = null;
let lastAnalysisRosterSignature = null;

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
    
    // Comparison recommendation selector
    document.getElementById('comparison-rec-selector').addEventListener('change', async (e) => {
        const recIndex = parseInt(e.target.value);
        if (recIndex >= 0 && currentAnalysisData && currentAnalysisData.recommendations) {
            selectedComparisonRecIndex = recIndex;
            await updateRecommendedScheduleInComparison(currentAnalysisData, recIndex);
        }
    });
    
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
    const rosterSignature = playerIds.sort().join(',');
    
    // Check if we already have analysis for this roster and gameweek
    if (currentAnalysisData && 
        lastAnalysisGameweek === selectedGameweek && 
        lastAnalysisRosterSignature === rosterSignature) {
        // Use cached analysis
        displayAnalysis(currentAnalysisData);
        return;
    }
    
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
        
        // Store the analysis state
        lastAnalysisGameweek = selectedGameweek;
        lastAnalysisRosterSignature = rosterSignature;
        
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
    
    // Display roster fantasy points average
    if (data.roster_avg_fp !== undefined) {
        html += `<div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #4caf50;">`;
        html += `<p style="margin: 0; font-size: 1.1rem;"><strong>Current Roster Average:</strong> <span style="color: #2e7d32; font-size: 1.3rem; font-weight: bold;">${data.roster_avg_fp} FP/G</span></p>`;
        html += `<p style="margin: 5px 0 0 0; color: #666; font-size: 0.9rem;">Total projected: ${data.roster_total_fp.toFixed(1)} fantasy points per game</p>`;
        html += `</div>`;
    }
    
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
                const teamDaysStr = drop.team_game_days ? ` - ${drop.team} plays ${drop.team_game_days} days` : '';
                html += `<li>${drop.name} (${drop.position}, $${drop.salary}M${fpStr}${teamDaysStr})</li>`;
            });
            html += '</ul></div>';
            
            // Adds
            html += '<div class="transaction"><strong class="add">ADD:</strong><ul>';
            rec.adds.forEach(add => {
                const fpStr = add.fantasy_avg > 0 ? `, ${add.fantasy_avg.toFixed(1)} FP/G` : '';
                const minStr = add.avg_minutes > 0 ? `, ${add.avg_minutes.toFixed(1)} min/g` : '';
                const teamDaysStr = add.team_game_days ? ` - ${add.team} plays ${add.team_game_days} days` : '';
                const teamDaysEmoji = add.team_game_days >= 4 ? ' 🔥' : (add.team_game_days >= 3 ? ' ✨' : '');
                html += `<li>${add.name} (${add.position}, $${add.salary}M, ${add.games} games${fpStr}${minStr}${teamDaysStr}${teamDaysEmoji})</li>`;
            });
            html += '</ul></div>';
            
            // Impact summary
            html += '<div style="margin-top: 15px; padding: 10px; background: white; border-radius: 6px;">';
            const costStr = rec.cost >= 0 ? `+$${rec.cost.toFixed(1)}M` : `-$${Math.abs(rec.cost).toFixed(1)}M`;
            html += `<p><strong>Net Cost:</strong> ${costStr}</p>`;
            
            if (rec.games_improvement !== undefined) {
                const gamesColor = rec.games_improvement > 0 ? '#2ecc71' : (rec.games_improvement < 0 ? '#ff4757' : '#666');
                const gamesStr = rec.games_improvement >= 0 ? `+${rec.games_improvement}` : rec.games_improvement;
                html += `<p><strong>Total Games:</strong> <span style="color: ${gamesColor};">${gamesStr} games</span></p>`;
            }
            
            if (rec.fp_improvement !== undefined) {
                const fpColor = rec.fp_improvement > 0 ? '#2ecc71' : (rec.fp_improvement < -0.5 ? '#ff4757' : '#666');
                const fpStr = rec.fp_improvement >= 0 ? `+${rec.fp_improvement.toFixed(1)}` : rec.fp_improvement.toFixed(1);
                html += `<p><strong>Fantasy Points:</strong> <span style="color: ${fpColor};">${fpStr} FP/G</span></p>`;
            }
            
            if (rec.depth_score !== undefined && rec.depth_score > 0) {
                html += `<p><strong>Roster Depth:</strong> <span style="color: #2ecc71;">Improves coverage on problem days ✓</span></p>`;
            }
            
            if (rec.team_days_improvement !== undefined) {
                const teamColor = rec.team_days_improvement > 0 ? '#2ecc71' : (rec.team_days_improvement < 0 ? '#ff4757' : '#666');
                const teamStr = rec.team_days_improvement >= 0 ? `+${rec.team_days_improvement}` : rec.team_days_improvement;
                html += `<p><strong>Team Schedule:</strong> <span style="color: ${teamColor};">${teamStr} game days</span></p>`;
            }
            html += '</div>';
            
            // Display warnings/reasons if any
            if (rec.warnings && rec.warnings.length > 0) {
                html += '<div style="margin-top: 15px; padding: 12px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid #6c757d;">';
                html += '<div style="font-weight: 600; margin-bottom: 8px; color: #495057;">📋 Analysis:</div>';
                html += '<ul style="margin: 0; padding-left: 20px; font-size: 0.9rem;">';
                rec.warnings.forEach(warning => {
                    const isPositive = warning.startsWith('✅');
                    const isWarning = warning.startsWith('⚠️');
                    const color = isPositive ? '#2ecc71' : (isWarning ? '#ff9800' : '#6c757d');
                    html += `<li style="color: ${color}; margin: 4px 0;">${warning}</li>`;
                });
                html += '</ul></div>';
            }
            
            html += `<button class="view-recommendation-btn" onclick="viewRecommendationDetails(${index})">📊 View Schedule & Roster Details</button>`;
            
            html += '</div>';
        });
    } else if (data.insufficient_days && data.insufficient_days.length > 0) {
        // There are gaps but no recommendations found at all
        html += '<div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">';
        html += '<h4 style="color: #856404; margin-top: 0;">⚠️ No Valid Transaction Options</h4>';
        html += '<p style="color: #856404; margin-bottom: 10px;">Your roster has gaps but no valid transactions could be generated. This usually means:</p>';
        html += '<ul style="color: #856404; margin: 10px 0;">';
        html += '<li><strong>Budget constraint:</strong> Not enough budget to add players who cover problem days</li>';
        html += '<li><strong>Position balance:</strong> Can\'t maintain required position distribution (3-5 BC, 3-5 FC)</li>';
        html += '<li><strong>Limited candidates:</strong> No available players play on your problem days</li>';
        html += '</ul>';
        html += '<p style="color: #856404; font-weight: bold; margin-bottom: 0;">💡 Try this:</p>';
        html += '<ul style="color: #856404; margin-top: 5px;">';
        html += '<li>Increase available budget to $2-3M</li>';
        html += '<li>Check the Top Teams tab to see which teams have more games</li>';
        html += '<li>Manually search for free agents from teams with 4+ game days</li>';
        html += '</ul>';
        html += '</div>';
    } else {
        html += '<div style="background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 20px;">';
        html += '<p style="color: #155724;"><strong>✓ Your roster looks good!</strong> All days have sufficient player coverage.</p>';
        html += '</div>';
    }
    
    analysisContent.innerHTML = html;
    
    // Store recommendations and analysis data globally
    currentRecommendations = data.recommendations || [];
    currentAnalysisData = data;
    
    // Also populate the comparison view with recommended roster
    if (data.recommendations && data.recommendations.length > 0) {
        populateComparisonView(data);
    }
}

// View recommendation details in a modal or expanded view
async function viewRecommendationDetails(recIndex) {
    if (!currentRecommendations || recIndex >= currentRecommendations.length) {
        alert('Recommendation not found');
        return;
    }
    
    const rec = currentRecommendations[recIndex];
    const selectedGameweek = parseInt(document.getElementById('gameweek-selector').value) || 9;
    
    // Build recommended roster
    const dropsIds = new Set(rec.drops.map(d => d.player_id));
    const currentPlayerIds = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined)
        .map(p => p.player_id);
    
    const remainingIds = currentPlayerIds.filter(id => !dropsIds.has(id));
    const recommendedIds = [...remainingIds, ...rec.adds.map(a => a.player_id)];
    
    // Get schedule for recommended roster
    try {
        const response = await fetch('/api/game_schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_ids: recommendedIds,
                gameweek: selectedGameweek
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Build player roster list with FA averages
        const rosterList = [];
        currentRoster.backcourt.concat(currentRoster.frontcourt).forEach(p => {
            if (p && !dropsIds.has(p.player_id)) {
                rosterList.push(p);
            }
        });
        rec.adds.forEach(add => {
            rosterList.push({
                player_id: add.player_id,
                player_name: add.name,
                position: add.position,
                team: add.team || '',
                salary: add.salary,
                fantasy_avg: add.fantasy_avg
            });
        });
        
        // Build HTML for modal/expanded view
        let html = `
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; max-width: 900px; margin: 20px auto;">
                <h3 style="color: #0a2540; margin-bottom: 15px;">📊 Option ${recIndex + 1} - Detailed View</h3>
                
                <div style="background: #fff3cd; padding: 12px; border-radius: 6px; margin-bottom: 20px;">
                    <p style="margin: 0; color: #856404;"><strong>Transaction Summary:</strong></p>
                    <p style="margin: 5px 0 0 0;">🔴 OUT: ${rec.drops.map(d => d.name).join(', ')}</p>
                    <p style="margin: 5px 0 0 0;">🟢 IN: ${rec.adds.map(a => a.name).join(', ')}</p>
                </div>
                
                <h4 style="margin-bottom: 10px;">Recommended Roster (10 Players)</h4>
                <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #0a2540; color: white;">
                                <th style="padding: 8px; text-align: left;">Player</th>
                                <th style="padding: 8px;">Position</th>
                                <th style="padding: 8px;">Team</th>
                                <th style="padding: 8px;">Salary</th>
                                <th style="padding: 8px;">FP/G</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        rosterList.forEach(player => {
            const isNew = rec.adds.some(a => a.player_id === player.player_id);
            const rowStyle = isNew ? 'background: #d1fae5;' : '';
            const fpAvg = player.fantasy_avg ? player.fantasy_avg.toFixed(1) : 'N/A';
            html += `
                <tr style="${rowStyle}">
                    <td style="padding: 8px; border-top: 1px solid #e2e8f0;">${player.player_name} ${isNew ? '🟢' : ''}</td>
                    <td style="padding: 8px; border-top: 1px solid #e2e8f0; text-align: center;">${player.position}</td>
                    <td style="padding: 8px; border-top: 1px solid #e2e8f0; text-align: center;">${player.team}</td>
                    <td style="padding: 8px; border-top: 1px solid #e2e8f0; text-align: center;">$${player.salary}M</td>
                    <td style="padding: 8px; border-top: 1px solid #e2e8f0; text-align: center;">${fpAvg}</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
                
                <h4 style="margin-bottom: 10px;">Gameweek ${selectedGameweek} Schedule</h4>
        `;
        
        html += buildScheduleHTML(data, rosterList);
        
        html += `
                <button onclick="document.getElementById('rec-details-modal').style.display='none'" 
                        style="margin-top: 20px; padding: 10px 20px; background: #0a2540; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    Close
                </button>
            </div>
        `;
        
        // Show in modal
        let modal = document.getElementById('rec-details-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'rec-details-modal';
            modal.className = 'modal';
            document.body.appendChild(modal);
        }
        
        modal.innerHTML = `<div class="modal-content" style="max-width: 950px; max-height: 90vh; overflow-y: auto;">${html}</div>`;
        modal.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading recommendation details:', error);
        alert('Failed to load recommendation details');
    }
}

// Populate schedule comparison view
async function populateComparisonView(analysisData) {
    // Populate recommendation selector
    const selector = document.getElementById('comparison-rec-selector');
    selector.innerHTML = '<option value="-1">Select a recommendation...</option>';
    
    if (analysisData.recommendations && analysisData.recommendations.length > 0) {
        analysisData.recommendations.forEach((rec, index) => {
            const option = document.createElement('option');
            option.value = index;
            
            // Determine warning icon based on warning text content
            let warningIcon = '✅';
            if (rec.warnings && rec.warnings.length > 0) {
                const hasWarning = rec.warnings.some(w => w.includes('⚠️'));
                const hasSuccess = rec.warnings.some(w => w.includes('✅'));
                if (hasWarning) warningIcon = '⚠️';
                else if (hasSuccess) warningIcon = '✅';
                else warningIcon = 'ℹ️';
            }
            
            // Get player name from adds array (first player being added)
            const playerName = rec.adds && rec.adds.length > 0 ? rec.adds[0].name : 'Unknown';
            const playerTeam = rec.adds && rec.adds.length > 0 ? rec.adds[0].team : '';
            
            option.textContent = `${index + 1}. ${playerName} (${playerTeam}) ${warningIcon}`;
            if (index === 0) option.selected = true;
            selector.appendChild(option);
        });
        selectedComparisonRecIndex = 0;
    }
    
    // Get current roster schedule
    await updateCurrentScheduleInComparison();
    
    // Get recommended roster schedule (using selected recommendation)
    if (analysisData.recommendations && analysisData.recommendations.length > 0) {
        await updateRecommendedScheduleInComparison(analysisData, selectedComparisonRecIndex);
    }
}

// Update current roster schedule in comparison view
async function updateCurrentScheduleInComparison() {
    const currentScheduleDiv = document.getElementById('current-schedule');
    const selectedPlayers = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined);
    
    if (selectedPlayers.length === 0) {
        currentScheduleDiv.innerHTML = '<p class="schedule-placeholder">Select your roster to view schedule</p>';
        return;
    }
    
    const selectedGameweek = parseInt(document.getElementById('gameweek-selector').value) || 9;
    const playerIds = selectedPlayers.map(p => p.player_id);
    
    try {
        const response = await fetch('/api/game_schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_ids: playerIds,
                gameweek: selectedGameweek
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentScheduleDiv.innerHTML = buildScheduleHTML(data, selectedPlayers);
    } catch (error) {
        console.error('Error loading current schedule:', error);
        currentScheduleDiv.innerHTML = '<p class="error">Failed to load schedule</p>';
    }
}

// Update recommended roster schedule in comparison view
async function updateRecommendedScheduleInComparison(analysisData, recIndex = 0) {
    const recommendedScheduleDiv = document.getElementById('recommended-schedule');
    const selectedRec = analysisData.recommendations[recIndex];
    
    if (!selectedRec) {
        recommendedScheduleDiv.innerHTML = '<p class="schedule-placeholder">No recommendations available</p>';
        return;
    }
    
    // Build recommended roster: current roster - drops + adds
    const dropsIds = new Set(firstRec.drops.map(d => d.player_id));
    const currentPlayerIds = [...currentRoster.backcourt, ...currentRoster.frontcourt]
        .filter(p => p !== null && p !== undefined)
        .map(p => p.player_id);
    
    // Remove drops
    const remainingIds = currentPlayerIds.filter(id => !dropsIds.has(id));
    
    // Add the new players
    const recommendedIds = [...remainingIds, ...selectedRec.adds.map(a => a.player_id)];
    
    console.log('Current roster IDs:', currentPlayerIds);
    console.log('Drops:', dropsIds);
    console.log('Recommended roster IDs:', recommendedIds);
    
    const selectedGameweek = parseInt(document.getElementById('gameweek-selector').value) || 9;
    
    try {
        const response = await fetch('/api/game_schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_ids: recommendedIds,
                gameweek: selectedGameweek
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Build player objects for display
        const recommendedPlayers = [];
        // Add remaining players
        currentRoster.backcourt.concat(currentRoster.frontcourt).forEach(p => {
            if (p && !dropsIds.has(p.player_id)) {
                recommendedPlayers.push(p);
            }
        });
        // Add new players
        selectedRec.adds.forEach(add => {
            recommendedPlayers.push({
                player_id: add.player_id,
                player_name: add.name,
                position: add.position,
                team: add.team || '',
                salary: add.salary
            });
        });
        
        recommendedScheduleDiv.innerHTML = buildScheduleHTML(data, recommendedPlayers, selectedRec);
    } catch (error) {
        console.error('Error loading recommended schedule:', error);
        recommendedScheduleDiv.innerHTML = '<p class="error">Failed to load schedule</p>';
    }
}

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
        </div>
        
        <div class="schedule-table-container">
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
        
        html += `
            <tr class="schedule-day-row ${statusClass}">
                <td class="day-name"><strong>${dayName}</strong></td>
                <td class="player-count">${playerCount}</td>
                <td class="position-count">${bcCount}</td>
                <td class="position-count">${fcCount}</td>
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
    
    // Trigger analysis when switching to analysis tab
    if (tabName === 'analysis') {
        analyzeRoster();
    }
    
    // Populate comparison view if switching to comparison tab and we have analysis data
    if (tabName === 'comparison') {
        if (currentAnalysisData && currentAnalysisData.recommendations && currentAnalysisData.recommendations.length > 0) {
            populateComparisonView(currentAnalysisData);
        } else {
            // Show message if no analysis data
            const currentScheduleDiv = document.getElementById('current-schedule');
            const recommendedScheduleDiv = document.getElementById('recommended-schedule');
            const message = '<p class="schedule-placeholder">👈 Run analysis first to compare schedules</p>';
            currentScheduleDiv.innerHTML = message;
            recommendedScheduleDiv.innerHTML = message;
        }
    }
    
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
        
        games.forEach(game => {
            game.players.forEach(p => {
                playersThisDay.add(p.player_id);
                const playerData = selectedPlayers.find(sp => sp.player_id === p.player_id);
                if (playerData) {
                    const position = playerData.position.includes('G') ? 'backcourt' : 'frontcourt';
                    if (!playersByPosition[position].some(existing => existing.player_id === p.player_id)) {
                        playersByPosition[position].push({
                            ...p,
                            matchup: game.matchup
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
        
        // Build player list for this day
        let playerList = [];
        if (dayPlayerDetails[day].backcourt.length > 0) {
            playerList.push(...dayPlayerDetails[day].backcourt.map(p => 
                `<span class="player-chip bc">${p.player_name}</span>`
            ));
        }
        if (dayPlayerDetails[day].frontcourt.length > 0) {
            playerList.push(...dayPlayerDetails[day].frontcourt.map(p => 
                `<span class="player-chip fc">${p.player_name}</span>`
            ));
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
        
        let html = `
            <div class="teams-header">
                <h3>🏆 Top 10 Teams - Gameweek ${data.gameweek}</h3>
                <p style="color: #666; margin-bottom: 20px;">${data.date_range}</p>
            </div>
            <div class="teams-list">
        `;
        
        data.teams.forEach((team, index) => {
            const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            const rankClass = index < 3 ? 'top-three' : '';
            
            html += `
                <div class="team-card ${rankClass}">
                    <div class="team-header">
                        <span class="team-rank">${rankEmoji}</span>
                        <span class="team-name">${team.team_name}</span>
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
