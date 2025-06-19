#!/usr/bin/env python3
"""
Player Statistics Module for Game Project
Handles player data and performance metrics.
"""

from typing import List, Dict, Any, Optional, Union
import json
import math
from datetime import datetime

class PlayerDataManager:
    """Manages player data and statistics."""
    
    def __init__(self):
        self.player_cache = {}
        self.score_history = []
        self.session_data = {}
    
    def process_numeric_list(self, scores: List[Union[int, float]]) -> Dict[str, Any]:
        """Process a list of player scores and return statistical analysis."""
        if not scores:
            return {"error": "No scores provided"}
        
        # Basic statistics
        total = sum(scores)
        count = len(scores)
        mean = total / count
        
        # Sort for median calculation
        sorted_scores = sorted(scores)
        if count % 2 == 1:
            median = sorted_scores[count // 2]
        else:
            median = (sorted_scores[count // 2 - 1] + sorted_scores[count // 2]) / 2
        
        # Variance and standard deviation
        variance = sum((x - mean) ** 2 for x in scores) / count
        std_dev = math.sqrt(variance)
        
        result = {
            "count": count,
            "sum": total,
            "mean": mean,
            "median": median,
            "variance": variance,
            "std_dev": std_dev,
            "min": min(scores),
            "max": max(scores),
            "range": max(scores) - min(scores),
            "high_score": max(scores),
            "average_score": mean
        }
        
        self.score_history.append(("process_scores", len(scores)))
        return result
    
    def find_patterns(self, gameplay_data: List[Any]) -> Dict[str, Any]:
        """Find patterns in player gameplay data."""
        if not gameplay_data:
            return {"patterns": []}
        
        patterns = {
            "session_length": len(gameplay_data),
            "unique_actions": len(set(gameplay_data)),
            "most_frequent": None,
            "repeated_actions": []
        }
        
        # Find most frequent action
        frequency = {}
        for action in gameplay_data:
            frequency[action] = frequency.get(action, 0) + 1
        
        if frequency:
            most_frequent = max(frequency, key=frequency.get)
            patterns["most_frequent"] = {
                "action": most_frequent,
                "count": frequency[most_frequent]
            }
            
            # Find repeated actions
            patterns["repeated_actions"] = [action for action, count in frequency.items() if count > 1]
        
        return patterns
    
    def serialize_data(self, data: Any) -> str:
        """Serialize player data to JSON string."""
        try:
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            return f"Serialization error: {str(e)}"
    
    def validate_data_structure(self, data: Any, expected_type: str) -> bool:
        """Validate player data structure type."""
        type_mapping = {
            "list": list,
            "dict": dict,
            "string": str,
            "number": (int, float),
            "boolean": bool
        }
        
        expected = type_mapping.get(expected_type.lower())
        if expected:
            return isinstance(data, expected)
        return False

class GameConfigManager:
    """Manages game configuration and settings."""
    
    def __init__(self):
        self.settings = {
            "difficulty": "normal",
            "sound_enabled": True,
            "max_players": 4,
            "auto_save_progress": True,
            "graphics_quality": "high"
        }
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a game configuration setting."""
        if key in self.settings:
            old_value = self.settings[key]
            self.settings[key] = value
            print(f"Game setting '{key}' changed from {old_value} to {value}")
            return True
        return False
    
    def get_setting(self, key: str) -> Any:
        """Get a game configuration setting."""
        return self.settings.get(key)
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.__init__()

class AchievementTracker:
    """Tracks player achievements and milestones."""
    
    def __init__(self):
        self.achievements = {}
        self.milestones = {
            "first_win": False,
            "high_scorer": False,
            "consistent_player": False,
            "speed_demon": False
        }
    
    def check_achievement(self, player_id: str, stats: Dict[str, Any]) -> List[str]:
        """Check if player has earned new achievements."""
        new_achievements = []
        
        # High score achievement
        if stats.get("max", 0) > 1000 and not self.milestones.get("high_scorer"):
            new_achievements.append("High Scorer")
            self.milestones["high_scorer"] = True
        
        # Consistent player achievement
        if stats.get("count", 0) > 10 and stats.get("std_dev", 0) < 50:
            if not self.milestones.get("consistent_player"):
                new_achievements.append("Consistent Player")
                self.milestones["consistent_player"] = True
        
        return new_achievements
    
    def get_player_achievements(self, player_id: str) -> List[str]:
        """Get all achievements for a player."""
        return self.achievements.get(player_id, []) 