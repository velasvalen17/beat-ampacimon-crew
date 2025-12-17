"""
NBA Data Fetcher
Fetches current season data from NBA API including teams, players, schedule, and stats.
"""

from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import (
    playergamelog,
    teamgamelog,
    commonteamroster,
    scoreboardv2,
)
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import requests
import random


class NBADataFetcher:
    """Fetch NBA data from the official NBA API."""
    
    # Current 2025-26 season
    CURRENT_SEASON = 2025
    SEASON_START = "2025-10-21"  # 2025-26 season start
    SEASON_END = "2026-04-12"    # Approximate end date
    
    # Retry configuration
    MAX_RETRIES = 5
    RETRY_DELAY = 2  # base seconds for exponential backoff
    TIMEOUT = 90  # seconds
    
    @staticmethod
    def get_all_teams() -> List[Dict]:
        """
        Get all NBA teams for the current season.
        
        Returns:
            List of team dictionaries with team_id, team_name, team_abbreviation, etc.
        """
        teams_list = teams.get_teams()
        return teams_list
    
    @staticmethod
    def get_team_roster(team_id: int) -> List[Dict]:
        """
        Get full roster for a specific team.
        
        Args:
            team_id: NBA team ID
            
        Returns:
            List of players on the team
        """
        for attempt in range(NBADataFetcher.MAX_RETRIES):
            try:
                roster = commonteamroster.CommonTeamRoster(
                    team_id=team_id,
                    timeout=NBADataFetcher.TIMEOUT
                )
                roster_data = roster.get_data_frames()[0]
                return roster_data.to_dict('records')
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < NBADataFetcher.MAX_RETRIES - 1:
                    wait_time = NBADataFetcher.RETRY_DELAY * (2 ** attempt)
                    print(f"  Timeout for roster {team_id} (attempt {attempt+1}/{NBADataFetcher.MAX_RETRIES}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed to fetch roster for team {team_id} after {NBADataFetcher.MAX_RETRIES} attempts")
                    return []
            except Exception as e:
                print(f"  Error fetching roster for team {team_id}: {e}")
                return []
    
    @staticmethod
    def get_player_game_log(player_id: int, season: int = CURRENT_SEASON) -> List[Dict]:
        """
        Get game log for a specific player in a season.
        
        Args:
            player_id: NBA player ID
            season: NBA season year
            
        Returns:
            List of game statistics for the player
        """
        for attempt in range(1, NBADataFetcher.MAX_RETRIES + 1):
            try:
                game_log = playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season,
                    timeout=NBADataFetcher.TIMEOUT
                )
                games_data = game_log.get_data_frames()[0]
                # brief pause to be polite to the API
                time.sleep(0.25)
                return games_data.to_dict('records')
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < NBADataFetcher.MAX_RETRIES:
                    backoff = NBADataFetcher.RETRY_DELAY * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.5 * backoff)
                    wait_time = backoff + jitter
                    print(f"  Timeout for player {player_id} (attempt {attempt}/{NBADataFetcher.MAX_RETRIES}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed to fetch game log for player {player_id} after {NBADataFetcher.MAX_RETRIES} attempts")
                    return []
            except Exception as e:
                print(f"  Error fetching game log for player {player_id}: {e}")
                return []
    
    @staticmethod
    def get_team_game_log(team_id: int, season: int = CURRENT_SEASON) -> List[Dict]:
        """
        Get game log for a specific team in a season.
        
        Args:
            team_id: NBA team ID
            season: NBA season year
            
        Returns:
            List of games for the team
        """
        for attempt in range(NBADataFetcher.MAX_RETRIES):
            try:
                game_log = teamgamelog.TeamGameLog(
                    team_id=team_id,
                    season=season,
                    timeout=NBADataFetcher.TIMEOUT
                )
                games_data = game_log.get_data_frames()[0]
                return games_data.to_dict('records')
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < NBADataFetcher.MAX_RETRIES - 1:
                    wait_time = NBADataFetcher.RETRY_DELAY * (2 ** attempt)
                    print(f"  Timeout for team {team_id} (attempt {attempt+1}/{NBADataFetcher.MAX_RETRIES}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed to fetch team game log for team {team_id} after {NBADataFetcher.MAX_RETRIES} attempts")
                    return []
            except Exception as e:
                print(f"  Error fetching team game log for team {team_id}: {e}")
                return []
    
    @staticmethod
    def get_scoreboard(game_date: str) -> List[Dict]:
        """
        Get scoreboard for a specific date.
        
        Args:
            game_date: Date in format 'YYYY-MM-DD'
            
        Returns:
            List of games on that date
        """
        # Convert date format to MMDDYYYY for NBA API
        date_parts = game_date.split('-')
        formatted_date = date_parts[1] + date_parts[2] + date_parts[0]

        for attempt in range(1, NBADataFetcher.MAX_RETRIES + 1):
            try:
                board = scoreboardv2.ScoreboardV2(game_date=formatted_date, timeout=NBADataFetcher.TIMEOUT)
                games_data = board.get_data_frames()[0]
                # small polite pause
                time.sleep(0.2)
                return games_data.to_dict('records')
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < NBADataFetcher.MAX_RETRIES:
                    backoff = NBADataFetcher.RETRY_DELAY * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.5 * backoff)
                    wait = backoff + jitter
                    print(f"  Timeout fetching scoreboard for {game_date} (attempt {attempt}/{NBADataFetcher.MAX_RETRIES}), retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  Failed to fetch scoreboard for {game_date} after {NBADataFetcher.MAX_RETRIES} attempts: {e}")
                    return []
            except Exception as e:
                # Log error detail; sometimes nba_api returns invalid/non-JSON responses
                try:
                    err_text = str(e)
                except Exception:
                    err_text = repr(e)
                print(f"Error fetching scoreboard for {game_date}: {err_text}")
                # Don't spam rapid retries for non-network errors; break after logging
                return []
    
    @staticmethod
    def get_player_info(player_name: str) -> Optional[Dict]:
        """
        Get player information by name.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Player information dictionary or None if not found
        """
        try:
            all_players = players.get_players()
            for player in all_players:
                if player['full_name'].lower() == player_name.lower():
                    return player
            return None
        except Exception as e:
            print(f"Error fetching player info for {player_name}: {e}")
            return None
    
    @staticmethod
    def get_all_players() -> List[Dict]:
        """
        Get all active NBA players.
        
        Returns:
            List of all player dictionaries
        """
        try:
            all_players = players.get_players()
            return all_players
        except Exception as e:
            print(f"Error fetching all players: {e}")
            return []


def test_data_fetcher():
    """Test the data fetcher with a simple query."""
    print("Fetching all NBA teams...")
    teams_list = NBADataFetcher.get_all_teams()
    print(f"Found {len(teams_list)} teams")
    if teams_list:
        print(f"Sample team: {teams_list[0]}")
    
    print("\nFetching all players...")
    all_players = NBADataFetcher.get_all_players()
    print(f"Found {len(all_players)} players")
    if all_players:
        print(f"Sample player: {all_players[0]}")


if __name__ == "__main__":
    test_data_fetcher()
