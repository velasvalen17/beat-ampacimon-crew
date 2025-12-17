"""
Database Query Utilities
Functions to query player info, gameweek calendars, and fantasy statistics.
"""

import sqlite3
from database import get_connection
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class QueryUtils:
    """Utility functions for querying the NBA fantasy database."""
    
    @staticmethod
    def get_player_info(player_id: int) -> Optional[Dict]:
        """
        Get complete player information including team.
        
        Args:
            player_id: NBA player ID
            
        Returns:
            Dictionary with player info or None if not found
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.player_id, p.player_name, p.team_id, p.position, p.jersey_number,
                   p.height, p.weight, p.college, p.country, p.draft_year,
                   t.team_name, t.team_abbreviation
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE p.player_id = ?
        """, (player_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'player_id': result[0],
                'player_name': result[1],
                'team_id': result[2],
                'position': result[3],
                'jersey_number': result[4],
                'height': result[5],
                'weight': result[6],
                'college': result[7],
                'country': result[8],
                'draft_year': result[9],
                'team_name': result[10],
                'team_abbreviation': result[11]
            }
        return None
    
    @staticmethod
    def get_player_by_name(player_name: str) -> Optional[Dict]:
        """
        Get player info by searching for name (case-insensitive).
        
        Args:
            player_name: Name of the player to search for
            
        Returns:
            Dictionary with player info or None if not found
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.player_id, p.player_name, p.team_id, p.position, p.jersey_number,
                   p.height, p.weight, p.college, p.country, p.draft_year,
                   t.team_name, t.team_abbreviation
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE LOWER(p.player_name) LIKE LOWER(?)
            LIMIT 1
        """, (f"%{player_name}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'player_id': result[0],
                'player_name': result[1],
                'team_id': result[2],
                'position': result[3],
                'jersey_number': result[4],
                'height': result[5],
                'weight': result[6],
                'college': result[7],
                'country': result[8],
                'draft_year': result[9],
                'team_name': result[10],
                'team_abbreviation': result[11]
            }
        return None
    
    @staticmethod
    def get_team_roster(team_id: int) -> List[Dict]:
        """
        Get all players on a team.
        
        Args:
            team_id: NBA team ID
            
        Returns:
            List of player dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT player_id, player_name, position, jersey_number
            FROM players
            WHERE team_id = ?
            ORDER BY player_name
        """, (team_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'player_id': row[0],
                'player_name': row[1],
                'position': row[2],
                'jersey_number': row[3]
            }
            for row in rows
        ]
    
    @staticmethod
    def get_gameweek_calendar(season_year: int) -> List[Dict]:
        """
        Get the gameweek calendar for a season.
        
        Args:
            season_year: NBA season year
            
        Returns:
            List of gameweeks with start and end dates
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gameweek_id, week_number, start_date, end_date
            FROM gameweeks
            WHERE season_year = ?
            ORDER BY week_number
        """, (season_year,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'gameweek_id': row[0],
                'week_number': row[1],
                'start_date': row[2],
                'end_date': row[3]
            }
            for row in rows
        ]
    
    @staticmethod
    def get_gameweek_by_date(game_date: str) -> Optional[Dict]:
        """
        Get gameweek information for a specific date.
        
        Args:
            game_date: Date in format 'YYYY-MM-DD'
            
        Returns:
            Gameweek dictionary or None if date not in any gameweek
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gameweek_id, season_year, week_number, start_date, end_date
            FROM gameweeks
            WHERE start_date <= ? AND end_date >= ?
            LIMIT 1
        """, (game_date, game_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'gameweek_id': result[0],
                'season_year': result[1],
                'week_number': result[2],
                'start_date': result[3],
                'end_date': result[4]
            }
        return None
    
    @staticmethod
    def get_player_game_stats(player_id: int, limit: int = 10) -> List[Dict]:
        """
        Get recent game statistics for a player.
        
        Args:
            player_id: NBA player ID
            limit: Number of recent games to retrieve
            
        Returns:
            List of game statistics dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT player_id, game_id, game_date, points, rebounds, assists, blocks, steals,
                   fantasy_points, minutes_played
            FROM player_game_stats
            WHERE player_id = ?
            ORDER BY game_date DESC
            LIMIT ?
        """, (player_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'player_id': row[0],
                'game_id': row[1],
                'game_date': row[2],
                'points': row[3],
                'rebounds': row[4],
                'assists': row[5],
                'blocks': row[6],
                'steals': row[7],
                'fantasy_points': row[8],
                'minutes_played': row[9]
            }
            for row in rows
        ]
    
    @staticmethod
    def get_player_gameweek_stats(player_id: int, season_year: int) -> List[Dict]:
        """
        Get aggregated stats for a player by gameweek.
        
        Args:
            player_id: NBA player ID
            season_year: NBA season year
            
        Returns:
            List of gameweek statistics dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pgs.summary_id, pgs.gameweek_id, g.week_number, pgs.games_played,
                   pgs.total_points, pgs.total_rebounds, pgs.total_assists,
                   pgs.total_blocks, pgs.total_steals, pgs.total_fantasy_points, pgs.avg_fantasy_points
            FROM player_gameweek_stats pgs
            JOIN gameweeks g ON pgs.gameweek_id = g.gameweek_id
            WHERE pgs.player_id = ? AND g.season_year = ?
            ORDER BY g.week_number
        """, (player_id, season_year))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'summary_id': row[0],
                'gameweek_id': row[1],
                'week_number': row[2],
                'games_played': row[3],
                'total_points': row[4],
                'total_rebounds': row[5],
                'total_assists': row[6],
                'total_blocks': row[7],
                'total_steals': row[8],
                'total_fantasy_points': row[9],
                'avg_fantasy_points': row[10]
            }
            for row in rows
        ]
    
    @staticmethod
    def search_players(name_pattern: str, team_id: Optional[int] = None) -> List[Dict]:
        """
        Search for players by name pattern.
        
        Args:
            name_pattern: Name pattern to search (case-insensitive)
            team_id: Optional team ID to filter by
            
        Returns:
            List of matching player dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        if team_id:
            cursor.execute("""
                SELECT player_id, player_name, team_id, position, jersey_number
                FROM players
                WHERE LOWER(player_name) LIKE LOWER(?) AND team_id = ?
                ORDER BY player_name
            """, (f"%{name_pattern}%", team_id))
        else:
            cursor.execute("""
                SELECT player_id, player_name, team_id, position, jersey_number
                FROM players
                WHERE LOWER(player_name) LIKE LOWER(?)
                ORDER BY player_name
            """, (f"%{name_pattern}%",))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'player_id': row[0],
                'player_name': row[1],
                'team_id': row[2],
                'position': row[3],
                'jersey_number': row[4]
            }
            for row in rows
        ]
    
    @staticmethod
    def get_top_scorers(season_year: int, limit: int = 10) -> List[Dict]:
        """
        Get top players by total fantasy points for a season.
        
        Args:
            season_year: NBA season year
            limit: Number of top players to return
            
        Returns:
            List of player statistics dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.player_id, p.player_name, p.position, p.team_id, t.team_abbreviation,
                   SUM(pgs.total_fantasy_points) as total_fp, 
                   AVG(pgs.avg_fantasy_points) as avg_fp,
                   COUNT(pgs.summary_id) as gameweeks_played
            FROM players p
            JOIN player_gameweek_stats pgs ON p.player_id = pgs.player_id
            JOIN gameweeks g ON pgs.gameweek_id = g.gameweek_id
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE g.season_year = ?
            GROUP BY p.player_id
            ORDER BY total_fp DESC
            LIMIT ?
        """, (season_year, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'player_id': row[0],
                'player_name': row[1],
                'position': row[2],
                'team_id': row[3],
                'team_abbreviation': row[4],
                'total_fantasy_points': row[5],
                'avg_fantasy_points': row[6],
                'gameweeks_played': row[7]
            }
            for row in rows
        ]


def test_queries():
    """Test query utilities with sample queries."""
    print("Testing Query Utilities\n")
    
    # Test gameweek calendar
    print("Gameweek Calendar for 2024-25 season:")
    calendar = QueryUtils.get_gameweek_calendar(2024)
    for gw in calendar[:3]:  # Show first 3 gameweeks
        print(f"  Week {gw['week_number']}: {gw['start_date']} to {gw['end_date']}")
    
    # Test player search
    print("\nSearching for LeBron James:")
    result = QueryUtils.get_player_by_name("LeBron")
    if result:
        print(f"  Found: {result['player_name']} - Team: {result['team_abbreviation']}")
    
    print("\nQuery utilities ready to use!")


if __name__ == "__main__":
    test_queries()
