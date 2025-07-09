#!/usr/bin/env python3

"""Sample Python program demonstrating various Python features."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Dict, Any
import statistics
import json

@dataclass
class Person:
    """Person data class with type hints."""
    name: str
    age: int
    email: Optional[str] = None
    
    def greet(self) -> str:
        return f"Hello, {self.name}! You are {self.age} years old."
    
    def is_adult(self) -> bool:
        return self.age >= 18
    
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "age": self.age, "email": self.email}

class Priority(Enum):
    """Priority enumeration."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    URGENT = auto()
    
    def __str__(self) -> str:
        return self.name.title()

def filter_adults(people: List[Person]) -> List[Person]:
    """Filter adults from a list of people."""
    return [person for person in people if person.is_adult()]

def map_names(people: List[Person]) -> List[str]:
    """Extract names from a list of people."""
    return [person.name for person in people]

def calculate_stats(numbers: List[float]) -> Dict[str, float]:
    """Calculate statistics for a list of numbers."""
    return {
        'sum': sum(numbers),
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'stdev': statistics.stdev(numbers) if len(numbers) > 1 else 0.0,
        'min': min(numbers),
        'max': max(numbers)
    }

def fibonacci(n: int) -> int:
    """Calculate Fibonacci number using memoization."""
    cache = {}
    
    def fib(num: int) -> int:
        if num in cache:
            return cache[num]
        if num <= 1:
            result = num
        else:
            result = fib(num - 1) + fib(num - 2)
        cache[num] = result
        return result
    
    return fib(n)

def process_data(data: Dict[str, Any]) -> None:
    """Process complex data structure."""
    print("Processing data:")
    for key, value in data.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"  {key}: {len(value)} keys")
        else:
            print(f"  {key}: {value}")

def main() -> None:
    """Main function demonstrating Python features."""
    print("Python Programming Example")
    
    # Create people using dataclass
    people = [
        Person("Alice", 30, "alice@example.com"),
        Person("Bob", 17, "bob@example.com"),
        Person("Charlie", 35, "charlie@example.com"),
        Person("Diana", 25, "diana@example.com"),
    ]
    
    print("\nAll people:")
    for person in people:
        print(person.greet())
    
    # Filter and map operations
    adults = filter_adults(people)
    print(f"\nAdults: {', '.join(map_names(adults))}")
    
    # List comprehensions
    ages = [person.age for person in people]
    even_ages = [age for age in ages if age % 2 == 0]
    
    print(f"Ages: {ages}")
    print(f"Even ages: {even_ages}")
    
    # Statistics
    stats = calculate_stats(ages)
    print(f"\nAge statistics:")
    for stat, value in stats.items():
        print(f"  {stat}: {value:.2f}")
    
    # Generator expression
    squares = (x**2 for x in range(1, 11))
    print(f"\nSquares: {list(squares)}")
    
    # Dictionary comprehension
    age_dict = {person.name: person.age for person in people}
    print(f"Age dictionary: {age_dict}")
    
    # Set operations
    names_set = {person.name for person in people}
    print(f"Unique names: {names_set}")
    
    # Enum usage
    print("\nPriorities:")
    for priority in Priority:
        print(f"  {priority}: {priority.value}")
    
    # Lambda and map/filter
    numbers = list(range(1, 11))
    doubled = list(map(lambda x: x * 2, numbers))
    evens = list(filter(lambda x: x % 2 == 0, numbers))
    
    print(f"\nNumbers: {numbers}")
    print(f"Doubled: {doubled}")
    print(f"Evens: {evens}")
    
    # Fibonacci sequence
    fib_sequence = [fibonacci(i) for i in range(10)]
    print(f"Fibonacci: {fib_sequence}")
    
    # JSON serialization
    people_data = [person.to_dict() for person in people]
    json_str = json.dumps(people_data, indent=2)
    print(f"\nJSON representation:\n{json_str}")
    
    # Complex data processing
    complex_data = {
        "users": people_data,
        "settings": {"theme": "dark", "language": "en"},
        "metrics": stats
    }
    process_data(complex_data)
    
    # Context manager example
    print("\nFile operations:")
    with open('/tmp/python_sample.txt', 'w') as f:
        f.write("Hello from Python!\n")
        f.write(f"Created by Python script\n")
    
    with open('/tmp/python_sample.txt', 'r') as f:
        content = f.read()
        print(f"File content: {content.strip()}")
    
    print("Program completed successfully!")

if __name__ == "__main__":
    main() 