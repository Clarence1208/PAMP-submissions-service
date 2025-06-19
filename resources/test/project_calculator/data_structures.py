#!/usr/bin/env python3
"""
Data Structures Module for Calculator Project
Handles various data operations and structures.
"""

from typing import List, Dict, Any, Optional, Union
import json
import math

class DataManager:
    """Handles data operations and statistics."""
    
    def __init__(self):
        self.data_cache = {}
        self.operation_history = []
    
    def process_numeric_list(self, numbers: List[Union[int, float]]) -> Dict[str, Any]:
        """Process a list of numbers and return statistical analysis."""
        if not numbers:
            return {"error": "Empty list provided"}
        
        # Basic statistics
        total = sum(numbers)
        count = len(numbers)
        mean = total / count
        
        # Sort for median calculation
        sorted_nums = sorted(numbers)
        if count % 2 == 1:
            median = sorted_nums[count // 2]
        else:
            median = (sorted_nums[count // 2 - 1] + sorted_nums[count // 2]) / 2
        
        # Variance and standard deviation
        variance = sum((x - mean) ** 2 for x in numbers) / count
        std_dev = math.sqrt(variance)
        
        result = {
            "count": count,
            "sum": total,
            "mean": mean,
            "median": median,
            "variance": variance,
            "std_dev": std_dev,
            "min": min(numbers),
            "max": max(numbers),
            "range": max(numbers) - min(numbers)
        }
        
        self.operation_history.append(("process_numeric_list", len(numbers)))
        return result
    
    def find_patterns(self, data: List[Any]) -> Dict[str, Any]:
        """Find patterns in data sequences."""
        if not data:
            return {"patterns": []}
        
        patterns = {
            "sequence_length": len(data),
            "unique_elements": len(set(data)),
            "most_common": None,
            "duplicates": []
        }
        
        # Find most common element
        frequency = {}
        for item in data:
            frequency[item] = frequency.get(item, 0) + 1
        
        if frequency:
            most_common = max(frequency, key=frequency.get)
            patterns["most_common"] = {
                "value": most_common,
                "count": frequency[most_common]
            }
            
            # Find duplicates
            patterns["duplicates"] = [item for item, count in frequency.items() if count > 1]
        
        return patterns
    
    def serialize_data(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            return f"Serialization error: {str(e)}"
    
    def validate_data_structure(self, data: Any, expected_type: str) -> bool:
        """Validate data structure type."""
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

class ConfigManager:
    """Manages configuration settings."""
    
    def __init__(self):
        self.settings = {
            "precision": 4,
            "use_scientific_notation": False,
            "max_history_size": 100,
            "auto_save": True
        }
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a configuration setting."""
        if key in self.settings:
            old_value = self.settings[key]
            self.settings[key] = value
            print(f"Setting '{key}' changed from {old_value} to {value}")
            return True
        return False
    
    def get_setting(self, key: str) -> Any:
        """Get a configuration setting."""
        return self.settings.get(key)
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.__init__() 