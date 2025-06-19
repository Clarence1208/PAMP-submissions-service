"""
Calculator Utilities
Helper functions for mathematical operations and data processing.
"""

import math
from typing import List, Tuple, Optional

class MathUtils:
    @staticmethod
    def calculate_statistics(numbers: List[float]) -> dict:
        """Calculate basic statistics for a list of numbers."""
        if not numbers:
            return {}
        
        n = len(numbers)
        mean = sum(numbers) / n
        variance = sum((x - mean) ** 2 for x in numbers) / n
        std_dev = math.sqrt(variance)
        
        sorted_nums = sorted(numbers)
        median = sorted_nums[n // 2] if n % 2 == 1 else (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
        
        return {
            'count': n,
            'sum': sum(numbers),
            'mean': mean,
            'median': median,
            'variance': variance,
            'std_dev': std_dev,
            'min': min(numbers),
            'max': max(numbers)
        }
    
    @staticmethod
    def solve_quadratic(a: float, b: float, c: float) -> Tuple[Optional[float], Optional[float]]:
        """Solve quadratic equation ax² + bx + c = 0."""
        if a == 0:
            if b == 0:
                return None, None
            return -c / b, None
        
        discriminant = b ** 2 - 4 * a * c
        
        if discriminant < 0:
            return None, None  # No real solutions
        elif discriminant == 0:
            x = -b / (2 * a)
            return x, x
        else:
            sqrt_d = math.sqrt(discriminant)
            x1 = (-b + sqrt_d) / (2 * a)
            x2 = (-b - sqrt_d) / (2 * a)
            return x1, x2 