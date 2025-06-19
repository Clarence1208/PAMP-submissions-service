#!/usr/bin/env python3
"""
Fantasy Adventure Game Engine
A text-based RPG with combat, inventory, and scoring systems.
"""

import random
import math
from typing import Dict, List, Union, Optional
from dataclasses import dataclass
from enum import Enum

class WeaponType(Enum):
    SWORD = "sword"
    BOW = "bow"
    STAFF = "staff"
    DAGGER = "dagger"

@dataclass
class Player:
    name: str
    health: float
    mana: float
    level: int
    experience: float
    gold: float
    inventory: List[str]

class GameEngine:
    def __init__(self):
        self.player = None
        self.current_location = "village"
        self.game_state = {}
        self.combat_log = []
        
    # SHARED UTILITY FUNCTION 1 - Input validation (identical to calculator project)
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
    
    # SHARED UTILITY FUNCTION 2 - Number formatting (identical to calculator project)
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
    
    def create_player(self, name: str) -> Player:
        """Create a new player character."""
        return Player(
            name=name,
            health=100.0,
            mana=50.0,
            level=1,
            experience=0.0,
            gold=100.0,
            inventory=["health_potion", "rusty_sword"]
        )
    
    def calculate_damage(self, attacker_level: int, weapon_type: WeaponType, 
                        critical_chance: float = 0.1) -> float:
        """Calculate combat damage with random elements."""
        base_damage = attacker_level * 10
        weapon_multiplier = {
            WeaponType.SWORD: 1.2,
            WeaponType.BOW: 1.0,
            WeaponType.STAFF: 0.8,
            WeaponType.DAGGER: 1.5
        }
        
        damage = base_damage * weapon_multiplier[weapon_type]
        
        # Add randomness
        damage *= random.uniform(0.8, 1.2)
        
        # Critical hit
        if random.random() < critical_chance:
            damage *= 2.0
            return damage, True
        
        return damage, False
    
    def calculate_experience_gain(self, enemy_level: int, player_level: int) -> float:
        """Calculate experience points gained from defeating an enemy."""
        base_exp = enemy_level * 25
        level_difference_multiplier = max(0.5, 1.0 - (player_level - enemy_level) * 0.1)
        return base_exp * level_difference_multiplier
    
    def process_combat_round(self, player: Player, enemy_level: int) -> Dict:
        """Process a single round of combat."""
        # Player attacks
        player_damage, player_crit = self.calculate_damage(
            player.level, WeaponType.SWORD, 0.15
        )
        
        # Enemy attacks
        enemy_damage, enemy_crit = self.calculate_damage(
            enemy_level, WeaponType.DAGGER, 0.05
        )
        
        # Apply damage
        enemy_health = enemy_level * 50  # Simplified enemy health
        player.health -= enemy_damage
        
        # Format combat results
        formatted_player_damage = self.format_number_display(player_damage, 1)
        formatted_enemy_damage = self.format_number_display(enemy_damage, 1)
        
        combat_result = {
            'player_damage': player_damage,
            'enemy_damage': enemy_damage,
            'player_critical': player_crit,
            'enemy_critical': enemy_crit,
            'formatted_player_damage': formatted_player_damage,
            'formatted_enemy_damage': formatted_enemy_damage,
            'player_health_remaining': player.health
        }
        
        self.combat_log.append(f"Player deals {formatted_player_damage} damage" + 
                              (" (CRITICAL!)" if player_crit else ""))
        self.combat_log.append(f"Enemy deals {formatted_enemy_damage} damage" + 
                              (" (CRITICAL!)" if enemy_crit else ""))
        
        return combat_result
    
    def level_up_player(self, player: Player):
        """Handle player level up mechanics."""
        required_exp = player.level * 100
        if player.experience >= required_exp:
            player.level += 1
            player.experience -= required_exp
            
            # Increase stats
            health_gain = 20 + (player.level * 5)
            mana_gain = 10 + (player.level * 3)
            
            player.health += health_gain
            player.mana += mana_gain
            
            formatted_health = self.format_number_display(player.health, 0)
            formatted_mana = self.format_number_display(player.mana, 0)
            
            print(f"\n🎉 LEVEL UP! {player.name} reached level {player.level}!")
            print(f"Health: {formatted_health}, Mana: {formatted_mana}")
    
    def calculate_shop_prices(self, base_price: float, player_level: int, 
                            item_rarity: str = "common") -> Dict[str, float]:
        """Calculate shop item prices based on player level and item rarity."""
        rarity_multipliers = {
            "common": 1.0,
            "uncommon": 2.0,
            "rare": 5.0,
            "epic": 10.0,
            "legendary": 25.0
        }
        
        level_multiplier = 1.0 + (player_level - 1) * 0.1
        final_price = base_price * rarity_multipliers[item_rarity] * level_multiplier
        
        return {
            'buy_price': final_price,
            'sell_price': final_price * 0.6,
            'formatted_buy': self.format_number_display(final_price, 0),
            'formatted_sell': self.format_number_display(final_price * 0.6, 0)
        }

def simulate_game_session():
    """Simulate a game session with combat and progression."""
    game = GameEngine()
    
    print("Fantasy Adventure Game")
    print("=" * 50)
    
    # Create player
    player = game.create_player("Hero")
    print(f"Welcome, {player.name}!")
    
    # Simulate some combat encounters
    enemies = [
        ("Goblin", 1),
        ("Orc", 2),
        ("Troll", 3),
        ("Dragon", 5)
    ]
    
    for enemy_name, enemy_level in enemies:
        print(f"\n⚔️  Encountering {enemy_name} (Level {enemy_level})")
        
        # Multiple combat rounds
        for round_num in range(1, 4):
            combat_result = game.process_combat_round(player, enemy_level)
            
            print(f"Round {round_num}: Player deals {combat_result['formatted_player_damage']} damage" +
                  (" (CRITICAL!)" if combat_result['player_critical'] else ""))
            
            if player.health <= 0:
                print("💀 Player defeated!")
                return
        
        # Award experience
        exp_gained = game.calculate_experience_gain(enemy_level, player.level)
        player.experience += exp_gained
        formatted_exp = game.format_number_display(exp_gained, 0)
        print(f"Gained {formatted_exp} experience points!")
        
        # Check for level up
        game.level_up_player(player)
        
        # Award gold
        gold_gained = enemy_level * 50 * random.uniform(0.8, 1.2)
        player.gold += gold_gained
        formatted_gold = game.format_number_display(player.gold, 0)
        print(f"Gold: {formatted_gold}")
    
    print(f"\n🏆 Final Stats for {player.name}:")
    print(f"Level: {player.level}")
    print(f"Health: {game.format_number_display(player.health, 0)}")
    print(f"Experience: {game.format_number_display(player.experience, 0)}")
    print(f"Gold: {game.format_number_display(player.gold, 0)}")

if __name__ == "__main__":
    simulate_game_session() 