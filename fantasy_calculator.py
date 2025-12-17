"""
NBA Fantasy Points Calculator
Calculates fantasy points based on official NBA Fantasy scoring rules.

Scoring Rules:
- Points scored: 1 point each
- Rebounds: 1 point each
- Assists: 2 points each
- Blocks: 3 points each
- Steals: 3 points each
"""

from typing import Dict, Optional


class FantasyCalculator:
    """Calculate fantasy points based on player statistics."""
    
    # Scoring multipliers
    POINTS_MULTIPLIER = 1
    REBOUNDS_MULTIPLIER = 1
    ASSISTS_MULTIPLIER = 2
    BLOCKS_MULTIPLIER = 3
    STEALS_MULTIPLIER = 3
    
    @staticmethod
    def calculate_fantasy_points(
        points: int = 0,
        rebounds: int = 0,
        assists: int = 0,
        blocks: int = 0,
        steals: int = 0,
    ) -> int:
        """
        Calculate total fantasy points from individual statistics.
        
        Args:
            points: Points scored in the game
            rebounds: Total rebounds
            assists: Total assists
            blocks: Total blocks
            steals: Total steals
            
        Returns:
            Total fantasy points
        """
        fantasy_points = (
            points * FantasyCalculator.POINTS_MULTIPLIER +
            rebounds * FantasyCalculator.REBOUNDS_MULTIPLIER +
            assists * FantasyCalculator.ASSISTS_MULTIPLIER +
            blocks * FantasyCalculator.BLOCKS_MULTIPLIER +
            steals * FantasyCalculator.STEALS_MULTIPLIER
        )
        return fantasy_points
    
    @staticmethod
    def calculate_from_dict(stats: Dict[str, int]) -> int:
        """
        Calculate fantasy points from a dictionary of statistics.
        
        Args:
            stats: Dictionary with keys: points, rebounds, assists, blocks, steals
            
        Returns:
            Total fantasy points
        """
        return FantasyCalculator.calculate_fantasy_points(
            points=stats.get("points", 0),
            rebounds=stats.get("rebounds", 0),
            assists=stats.get("assists", 0),
            blocks=stats.get("blocks", 0),
            steals=stats.get("steals", 0),
        )
    
    @staticmethod
    def breakdown_fantasy_points(
        points: int = 0,
        rebounds: int = 0,
        assists: int = 0,
        blocks: int = 0,
        steals: int = 0,
    ) -> Dict[str, int]:
        """
        Get a breakdown of fantasy points by category.
        
        Args:
            points: Points scored in the game
            rebounds: Total rebounds
            assists: Total assists
            blocks: Total blocks
            steals: Total steals
            
        Returns:
            Dictionary with points contribution from each stat category
        """
        breakdown = {
            "points": points * FantasyCalculator.POINTS_MULTIPLIER,
            "rebounds": rebounds * FantasyCalculator.REBOUNDS_MULTIPLIER,
            "assists": assists * FantasyCalculator.ASSISTS_MULTIPLIER,
            "blocks": blocks * FantasyCalculator.BLOCKS_MULTIPLIER,
            "steals": steals * FantasyCalculator.STEALS_MULTIPLIER,
            "total": 0
        }
        breakdown["total"] = sum(v for k, v in breakdown.items() if k != "total")
        return breakdown


def example_calculation():
    """Example: Calculate fantasy points for a sample game."""
    # Example: A player with 25 pts, 8 reb, 5 ast, 1 blk, 2 stl
    fantasy_pts = FantasyCalculator.calculate_fantasy_points(
        points=25,
        rebounds=8,
        assists=5,
        blocks=1,
        steals=2
    )
    print(f"Total Fantasy Points: {fantasy_pts}")
    
    # Get breakdown
    breakdown = FantasyCalculator.breakdown_fantasy_points(
        points=25,
        rebounds=8,
        assists=5,
        blocks=1,
        steals=2
    )
    print("Breakdown:")
    for key, value in breakdown.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    example_calculation()
