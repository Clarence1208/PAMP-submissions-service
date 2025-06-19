#!/usr/bin/env python3
"""
Algorithms Module for Calculator Project
Mathematical algorithms and computational methods.
"""

from typing import List, Tuple, Optional, Callable
import math

class SortingAlgorithms:
    """Collection of sorting algorithms for numerical analysis."""
    
    @staticmethod
    def bubble_sort(arr: List[float]) -> List[float]:
        """Bubble sort implementation."""
        n = len(arr)
        result = arr.copy()
        
        for i in range(n):
            for j in range(0, n - i - 1):
                if result[j] > result[j + 1]:
                    result[j], result[j + 1] = result[j + 1], result[j]
        
        return result
    
    @staticmethod
    def quick_sort(arr: List[float]) -> List[float]:
        """Quick sort implementation."""
        if len(arr) <= 1:
            return arr
        
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        
        return SortingAlgorithms.quick_sort(left) + middle + SortingAlgorithms.quick_sort(right)
    
    @staticmethod
    def merge_sort(arr: List[float]) -> List[float]:
        """Merge sort implementation."""
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        left = SortingAlgorithms.merge_sort(arr[:mid])
        right = SortingAlgorithms.merge_sort(arr[mid:])
        
        return SortingAlgorithms._merge(left, right)
    
    @staticmethod
    def _merge(left: List[float], right: List[float]) -> List[float]:
        """Helper function for merge sort."""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result

class SearchAlgorithms:
    """Collection of search algorithms."""
    
    @staticmethod
    def binary_search(arr: List[float], target: float) -> int:
        """Binary search implementation."""
        left, right = 0, len(arr) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1
    
    @staticmethod
    def linear_search(arr: List[float], target: float) -> int:
        """Linear search implementation."""
        for i, value in enumerate(arr):
            if value == target:
                return i
        return -1
    
    @staticmethod
    def find_extrema(arr: List[float]) -> Tuple[float, float, int, int]:
        """Find minimum and maximum values with their indices."""
        if not arr:
            raise ValueError("Array cannot be empty")
        
        min_val = max_val = arr[0]
        min_idx = max_idx = 0
        
        for i, value in enumerate(arr[1:], 1):
            if value < min_val:
                min_val = value
                min_idx = i
            elif value > max_val:
                max_val = value
                max_idx = i
        
        return min_val, max_val, min_idx, max_idx

class OptimizationAlgorithms:
    """Mathematical optimization algorithms."""
    
    @staticmethod
    def gradient_descent(func: Callable[[float], float], 
                        derivative: Callable[[float], float],
                        initial_x: float,
                        learning_rate: float = 0.01,
                        max_iterations: int = 1000,
                        tolerance: float = 1e-6) -> Tuple[float, float]:
        """Simple gradient descent implementation."""
        x = initial_x
        
        for iteration in range(max_iterations):
            grad = derivative(x)
            new_x = x - learning_rate * grad
            
            if abs(new_x - x) < tolerance:
                break
            
            x = new_x
        
        return x, func(x)
    
    @staticmethod
    def newton_raphson(func: Callable[[float], float],
                      derivative: Callable[[float], float],
                      initial_x: float,
                      max_iterations: int = 100,
                      tolerance: float = 1e-10) -> Optional[float]:
        """Newton-Raphson method for finding roots."""
        x = initial_x
        
        for iteration in range(max_iterations):
            fx = func(x)
            if abs(fx) < tolerance:
                return x
            
            dfx = derivative(x)
            if abs(dfx) < tolerance:
                return None  # Derivative too small
            
            x = x - fx / dfx
        
        return x if abs(func(x)) < tolerance else None

class NumericalMethods:
    """Numerical computation methods."""
    
    @staticmethod
    def numerical_derivative(func: Callable[[float], float], 
                           x: float, 
                           h: float = 1e-8) -> float:
        """Compute numerical derivative using central difference."""
        return (func(x + h) - func(x - h)) / (2 * h)
    
    @staticmethod
    def numerical_integration(func: Callable[[float], float],
                            a: float, b: float,
                            n: int = 1000) -> float:
        """Numerical integration using trapezoidal rule."""
        h = (b - a) / n
        result = (func(a) + func(b)) / 2
        
        for i in range(1, n):
            x = a + i * h
            result += func(x)
        
        return result * h
    
    @staticmethod
    def polynomial_evaluation(coefficients: List[float], x: float) -> float:
        """Evaluate polynomial using Horner's method."""
        if not coefficients:
            return 0.0
        
        result = coefficients[0]
        for coeff in coefficients[1:]:
            result = result * x + coeff
        
        return result 