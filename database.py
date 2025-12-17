"""
NBA Fantasy Database
Local database for storing player info, team assignments, gameweek calendars, and fantasy stats.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# Use environment variable for Docker, fall back to local path
DB_PATH = Path(os.getenv('DB_PATH', Path(__file__).parent / "nba_fantasy.db"))


def init_database():
    """Initialize the database with all required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Teams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT NOT NULL UNIQUE,
            team_abbreviation TEXT NOT NULL UNIQUE,
            city TEXT,
            state TEXT
        )
    """)
    
    # Players table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            position TEXT,
            jersey_number INTEGER,
            height TEXT,
            weight TEXT,
            college TEXT,
            country TEXT,
            draft_year INTEGER,
            salary REAL,
            salary_updated_at TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
        )
    """)
    
    # Gameweeks table (schedule structure)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gameweeks (
            gameweek_id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_year INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            UNIQUE(season_year, week_number)
        )
    """)
    
    # Games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            gameweek_id INTEGER NOT NULL,
            game_date TEXT NOT NULL,
            season_year INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            away_team_id INTEGER NOT NULL,
            home_team_score INTEGER,
            away_team_score INTEGER,
            game_status TEXT,
            FOREIGN KEY (gameweek_id) REFERENCES gameweeks(gameweek_id),
            FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
            FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
        )
    """)
    
    # Player game stats table (raw stats for fantasy point calculation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_game_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            game_id TEXT NOT NULL,
            game_date TEXT NOT NULL,
            points INTEGER,
            rebounds INTEGER,
            assists INTEGER,
            blocks INTEGER,
            steals INTEGER,
            fantasy_points INTEGER,
            minutes_played REAL,
            field_goals_made INTEGER,
            field_goals_attempted INTEGER,
            three_pointers_made INTEGER,
            three_pointers_attempted INTEGER,
            free_throws_made INTEGER,
            free_throws_attempted INTEGER,
            turnovers INTEGER,
            personal_fouls INTEGER,
            plus_minus INTEGER,
            UNIQUE(player_id, game_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
    """)
    
    # Player gameweek summary table (aggregated stats per gameweek)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_gameweek_stats (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            gameweek_id INTEGER NOT NULL,
            games_played INTEGER,
            total_points INTEGER,
            total_rebounds INTEGER,
            total_assists INTEGER,
            total_blocks INTEGER,
            total_steals INTEGER,
            total_fantasy_points INTEGER,
            avg_fantasy_points REAL,
            UNIQUE(player_id, gameweek_id),
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (gameweek_id) REFERENCES gameweeks(gameweek_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)


def close_connection(conn):
    """Close a database connection."""
    if conn:
        conn.close()
