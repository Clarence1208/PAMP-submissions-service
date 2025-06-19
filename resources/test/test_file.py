#!/usr/bin/env python3
"""
Advanced Calculator Application
Supports basic arithmetic, scientific calculations, and number formatting.
"""

import math
from typing import Union, List
from decimal import Decimal, getcontext

# Set precision for decimal calculations
getcontext().prec = 10

class Calculator:
    def __init__(self):
        self.history = []
        self.memory = 0.0
    
    # SHARED UTILITY FUNCTION 1 - Input validation (will be identical in game project)
    def validate_numeric_input(self, value: Union[str, int, float]) -> bool:
        """Validate if input can be converted to a number."""
        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return False
                # Handle special cases
                if value in ['inf', '-inf', 'nan']:
                    return False
                float(value)
            elif isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    return False
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    # SHARED UTILITY FUNCTION 2 - Number formatting (will be identical in game project)
    def format_number_display(self, number: float, precision: int = 2) -> str:
        """Format number for display with proper precision and thousand separators."""
        try:
            if not self.validate_numeric_input(number):
                return "ERROR"
            
            # Handle very large or very small numbers
            if abs(number) >= 1e12 or (abs(number) < 1e-6 and number != 0):
                return f"{number:.{precision}e}"
            
            # Regular formatting with thousand separators
            formatted = f"{number:,.{precision}f}"
            
            # Remove trailing zeros after decimal point
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            
            return formatted
        except Exception:
            return "ERROR"
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} × {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
        self.history.append(f"{a} ÷ {b} = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to exponent."""
        result = base ** exponent
        self.history.append(f"{base}^{exponent} = {result}")
        return result
    
    def square_root(self, number: float) -> float:
        """Calculate square root."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()

def main():
    calc = Calculator()
    
    print("Advanced Calculator")
    print("=" * 40)
    
    # Test basic operations
    test_cases = [
        (15.5, 4.2, "add"),
        (100, 25, "subtract"),
        (7.5, 8, "multiply"),
        (144, 12, "divide"),
        (2, 8, "power"),
        (25, None, "sqrt")
    ]
    
    for case in test_cases:
        a, b, operation = case
        
        if not calc.validate_numeric_input(a):
            print(f"Invalid input: {a}")
            continue
            
        try:
            if operation == "add" and b is not None:
                result = calc.add(a, b)
            elif operation == "subtract" and b is not None:
                result = calc.subtract(a, b)
            elif operation == "multiply" and b is not None:
                result = calc.multiply(a, b)
            elif operation == "divide" and b is not None:
                result = calc.divide(a, b)
            elif operation == "power" and b is not None:
                result = calc.power(a, b)
            elif operation == "sqrt":
                result = calc.square_root(a)
            else:
                continue
                
            formatted_result = calc.format_number_display(result, 3)
            print(f"Result: {formatted_result}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")

if __name__ == "__main__":
    main() 