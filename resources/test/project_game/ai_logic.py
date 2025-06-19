#!/usr/bin/env python3
"""
AI Logic Module for Game Project
Artificial intelligence algorithms and decision-making systems.
"""

from typing import List, Tuple, Optional, Callable, Dict, Any
import math
import random

class PathfindingAlgorithms:
    """Collection of pathfinding algorithms for game AI."""
    
    @staticmethod
    def simple_sort_positions(positions: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Sort positions by distance from origin (similar structure to bubble sort)."""
        n = len(positions)
        result = positions.copy()
        
        for i in range(n):
            for j in range(0, n - i - 1):
                dist1 = math.sqrt(result[j][0]**2 + result[j][1]**2)
                dist2 = math.sqrt(result[j + 1][0]**2 + result[j + 1][1]**2)
                if dist1 > dist2:
                    result[j], result[j + 1] = result[j + 1], result[j]
        
        return result
    
    @staticmethod
    def quick_select_targets(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Quick selection of targets based on priority (similar to quick sort)."""
        if len(targets) <= 1:
            return targets
        
        pivot = targets[len(targets) // 2]
        pivot_priority = pivot.get('priority', 0)
        
        high = [t for t in targets if t.get('priority', 0) > pivot_priority]
        equal = [t for t in targets if t.get('priority', 0) == pivot_priority]
        low = [t for t in targets if t.get('priority', 0) < pivot_priority]
        
        return PathfindingAlgorithms.quick_select_targets(high) + equal + PathfindingAlgorithms.quick_select_targets(low)
    
    @staticmethod
    def merge_threat_lists(list1: List[Dict], list2: List[Dict]) -> List[Dict]:
        """Merge two threat lists (similar to merge sort)."""
        if len(list1) <= 1 and len(list2) <= 1:
            return list1 + list2
        
        # Split and merge recursively
        mid1 = len(list1) // 2 if list1 else 0
        mid2 = len(list2) // 2 if list2 else 0
        
        if list1:
            left1 = PathfindingAlgorithms.merge_threat_lists(list1[:mid1], [])
            right1 = PathfindingAlgorithms.merge_threat_lists(list1[mid1:], [])
        else:
            left1 = right1 = []
        
        if list2:
            left2 = PathfindingAlgorithms.merge_threat_lists(list2[:mid2], [])
            right2 = PathfindingAlgorithms.merge_threat_lists(list2[mid2:], [])
        else:
            left2 = right2 = []
        
        return PathfindingAlgorithms._merge_threats(left1 + left2, right1 + right2)
    
    @staticmethod
    def _merge_threats(left: List[Dict], right: List[Dict]) -> List[Dict]:
        """Helper function for merging threat lists."""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i].get('threat_level', 0) >= right[j].get('threat_level', 0):
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result

class AISearchStrategies:
    """AI search and decision-making strategies."""
    
    @staticmethod
    def binary_search_skill_level(skill_ratings: List[float], target_skill: float) -> int:
        """Binary search for appropriate skill level matching."""
        left, right = 0, len(skill_ratings) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if skill_ratings[mid] == target_skill:
                return mid
            elif skill_ratings[mid] < target_skill:
                left = mid + 1
            else:
                right = mid - 1
        
        return -1
    
    @staticmethod
    def linear_search_resources(resources: List[Dict], resource_type: str) -> int:
        """Linear search for specific resource types."""
        for i, resource in enumerate(resources):
            if resource.get('type') == resource_type:
                return i
        return -1
    
    @staticmethod
    def find_optimal_strategy(strategies: List[Dict]) -> Tuple[Dict, Dict, int, int]:
        """Find best and worst strategies with their indices."""
        if not strategies:
            raise ValueError("Strategy list cannot be empty")
        
        best = worst = strategies[0]
        best_idx = worst_idx = 0
        
        for i, strategy in enumerate(strategies[1:], 1):
            effectiveness = strategy.get('effectiveness', 0)
            if effectiveness > best.get('effectiveness', 0):
                best = strategy
                best_idx = i
            elif effectiveness < worst.get('effectiveness', 0):
                worst = strategy
                worst_idx = i
        
        return best, worst, best_idx, worst_idx

class DecisionMaking:
    """AI decision-making and optimization."""
    
    @staticmethod
    def adaptive_learning(performance_func: Callable[[float], float], 
                         feedback_func: Callable[[float], float],
                         initial_param: float,
                         learning_rate: float = 0.05,
                         max_iterations: int = 200,
                         tolerance: float = 1e-4) -> Tuple[float, float]:
        """Adaptive learning algorithm (similar to gradient descent)."""
        param = initial_param
        
        for iteration in range(max_iterations):
            feedback = feedback_func(param)
            new_param = param + learning_rate * feedback
            
            if abs(new_param - param) < tolerance:
                break
            
            param = new_param
        
        return param, performance_func(param)
    
    @staticmethod
    def behavior_optimization(behavior_func: Callable[[float], float],
                             behavior_derivative: Callable[[float], float],
                             initial_behavior: float,
                             max_iterations: int = 50,
                             tolerance: float = 1e-8) -> Optional[float]:
        """Behavior optimization using iterative improvement."""
        behavior = initial_behavior
        
        for iteration in range(max_iterations):
            current_value = behavior_func(behavior)
            if abs(current_value) < tolerance:
                return behavior
            
            derivative = behavior_derivative(behavior)
            if abs(derivative) < tolerance:
                return None  # Cannot improve further
            
            behavior = behavior - current_value / derivative
        
        return behavior if abs(behavior_func(behavior)) < tolerance else None

class GameAI:
    """Main AI controller for game logic."""
    
    @staticmethod
    def calculate_move_value(game_state: Dict, move: Dict, 
                           complexity_factor: float = 1e-6) -> float:
        """Calculate the value of a move (similar to numerical derivative)."""
        base_value = game_state.get('current_score', 0)
        move_impact = move.get('impact', 0)
        
        return (base_value + move_impact - base_value) / complexity_factor
    
    @staticmethod
    def evaluate_game_state(state_func: Callable[[Dict], float],
                           current_state: Dict,
                           future_states: List[Dict],
                           time_steps: int = 100) -> float:
        """Evaluate game state progression (similar to numerical integration)."""
        if not future_states:
            return state_func(current_state)
        
        step_size = 1.0 / time_steps
        total_value = (state_func(current_state) + state_func(future_states[-1])) / 2
        
        for i in range(1, min(time_steps, len(future_states))):
            total_value += state_func(future_states[i])
        
        return total_value * step_size
    
    @staticmethod
    def strategic_planning(objectives: List[float], weights: List[float]) -> float:
        """Strategic planning using weighted objectives (similar to polynomial evaluation)."""
        if not objectives or len(objectives) != len(weights):
            return 0.0
        
        result = objectives[0] * weights[0]
        combined_weight = weights[0]
        
        for i in range(1, len(objectives)):
            result = result * combined_weight + objectives[i] * weights[i]
            combined_weight *= weights[i]
        
        return result

class BehaviorTree:
    """Simple behavior tree implementation for AI decision making."""
    
    def __init__(self, name: str):
        self.name = name
        self.children = []
        self.parent = None
    
    def add_child(self, child):
        """Add a child node to the behavior tree."""
        child.parent = self
        self.children.append(child)
    
    def evaluate(self, context: Dict) -> bool:
        """Evaluate the behavior tree."""
        # Simple evaluation - all children must succeed
        for child in self.children:
            if not child.evaluate(context):
                return False
        return True
    
    def get_best_action(self, available_actions: List[str]) -> Optional[str]:
        """Get the best action from available options."""
        if not available_actions:
            return None
        
        # Simple selection based on name similarity
        for action in available_actions:
            if action.lower() in self.name.lower():
                return action
        
        # Return first available action as fallback
        return available_actions[0] 