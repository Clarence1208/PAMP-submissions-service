#!/usr/bin/env python3
"""
Inventory Management Module for Game Project
Handles item management, equipment, and resource tracking.
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

class ItemRarity(Enum):
    """Item rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class ItemType(Enum):
    """Types of items in the game."""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    QUEST = "quest"
    CRAFTING = "crafting"
    CURRENCY = "currency"

@dataclass
class ItemStats:
    """Item statistics and attributes."""
    damage: int = 0
    defense: int = 0
    durability: int = 100
    max_durability: int = 100
    weight: float = 1.0
    value: int = 1

@dataclass
class Item:
    """Represents an item in the game."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unknown Item"
    description: str = ""
    item_type: ItemType = ItemType.CONSUMABLE
    rarity: ItemRarity = ItemRarity.COMMON
    stats: ItemStats = field(default_factory=ItemStats)
    stack_size: int = 1
    is_stackable: bool = False
    requirements: Dict[str, int] = field(default_factory=dict)
    effects: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def can_stack_with(self, other: 'Item') -> bool:
        """Check if this item can stack with another."""
        return (self.is_stackable and 
                other.is_stackable and
                self.name == other.name and
                self.item_type == other.item_type and
                self.rarity == other.rarity)
    
    def repair(self, amount: int = None) -> bool:
        """Repair the item's durability."""
        if amount is None:
            amount = self.stats.max_durability
        
        old_durability = self.stats.durability
        self.stats.durability = min(self.stats.max_durability, 
                                   self.stats.durability + amount)
        return self.stats.durability > old_durability
    
    def is_broken(self) -> bool:
        """Check if the item is broken."""
        return self.stats.durability <= 0
    
    def get_effective_value(self) -> int:
        """Get the item's value considering durability."""
        if self.stats.max_durability == 0:
            return self.stats.value
        
        durability_ratio = self.stats.durability / self.stats.max_durability
        return int(self.stats.value * durability_ratio)

@dataclass
class InventorySlot:
    """Represents a slot in the inventory."""
    item: Optional[Item] = None
    quantity: int = 0
    slot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_locked: bool = False
    
    def is_empty(self) -> bool:
        """Check if the slot is empty."""
        return self.item is None or self.quantity <= 0
    
    def can_add_item(self, item: Item, quantity: int = 1) -> bool:
        """Check if an item can be added to this slot."""
        if self.is_locked:
            return False
        
        if self.is_empty():
            return True
        
        if self.item.can_stack_with(item):
            return self.quantity + quantity <= item.stack_size
        
        return False
    
    def add_item(self, item: Item, quantity: int = 1) -> int:
        """Add item to slot, returns quantity that couldn't be added."""
        if not self.can_add_item(item, quantity):
            return quantity
        
        if self.is_empty():
            self.item = item
            self.quantity = min(quantity, item.stack_size)
        else:
            max_add = item.stack_size - self.quantity
            self.quantity += min(quantity, max_add)
        
        return max(0, quantity - (item.stack_size - self.quantity))
    
    def remove_item(self, quantity: int = 1) -> Tuple[Optional[Item], int]:
        """Remove item from slot, returns (item, actual_quantity_removed)."""
        if self.is_empty():
            return None, 0
        
        actual_quantity = min(quantity, self.quantity)
        self.quantity -= actual_quantity
        
        removed_item = self.item
        if self.quantity <= 0:
            self.item = None
            self.quantity = 0
        
        return removed_item, actual_quantity

class Inventory:
    """Main inventory system."""
    
    def __init__(self, max_slots: int = 30, max_weight: float = 100.0):
        self.max_slots = max_slots
        self.max_weight = max_weight
        self.slots: List[InventorySlot] = [InventorySlot() for _ in range(max_slots)]
        self.currency: Dict[str, int] = {"gold": 0, "silver": 0, "copper": 0}
        self.auto_sort_enabled = True
        self.filter_settings = {"show_broken": True, "show_quest": True}
    
    def get_total_weight(self) -> float:
        """Calculate total weight of all items."""
        total_weight = 0.0
        for slot in self.slots:
            if not slot.is_empty():
                total_weight += slot.item.stats.weight * slot.quantity
        return total_weight
    
    def get_available_weight(self) -> float:
        """Get remaining weight capacity."""
        return max(0.0, self.max_weight - self.get_total_weight())
    
    def find_empty_slot(self) -> Optional[int]:
        """Find the first empty slot."""
        for i, slot in enumerate(self.slots):
            if slot.is_empty():
                return i
        return None
    
    def find_stackable_slot(self, item: Item) -> Optional[int]:
        """Find a slot where the item can be stacked."""
        for i, slot in enumerate(self.slots):
            if not slot.is_empty() and slot.can_add_item(item):
                return i
        return None
    
    def add_item(self, item: Item, quantity: int = 1) -> bool:
        """Add item to inventory, returns True if successful."""
        if quantity <= 0:
            return False
        
        # Check weight limit
        total_weight = item.stats.weight * quantity
        if self.get_available_weight() < total_weight:
            return False
        
        remaining_quantity = quantity
        
        # Try to stack with existing items first
        if item.is_stackable:
            for slot in self.slots:
                if remaining_quantity <= 0:
                    break
                if not slot.is_empty() and slot.can_add_item(item, remaining_quantity):
                    remaining_quantity = slot.add_item(item, remaining_quantity)
        
        # Use empty slots for remaining quantity
        while remaining_quantity > 0:
            empty_slot_index = self.find_empty_slot()
            if empty_slot_index is None:
                return False  # No space
            
            slot = self.slots[empty_slot_index]
            remaining_quantity = slot.add_item(item, remaining_quantity)
        
        if self.auto_sort_enabled:
            self._auto_sort()
        
        return True
    
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from inventory by name."""
        remaining_to_remove = quantity
        
        for slot in self.slots:
            if remaining_to_remove <= 0:
                break
            
            if not slot.is_empty() and slot.item.name == item_name:
                _, removed = slot.remove_item(remaining_to_remove)
                remaining_to_remove -= removed
        
        return remaining_to_remove == 0
    
    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if inventory contains specific item and quantity."""
        total_found = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item.name == item_name:
                total_found += slot.quantity
                if total_found >= quantity:
                    return True
        return False
    
    def get_items_by_type(self, item_type: ItemType) -> List[Tuple[Item, int]]:
        """Get all items of a specific type."""
        items = []
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_type == item_type:
                items.append((slot.item, slot.quantity))
        return items
    
    def get_items_by_rarity(self, rarity: ItemRarity) -> List[Tuple[Item, int]]:
        """Get all items of a specific rarity."""
        items = []
        for slot in self.slots:
            if not slot.is_empty() and slot.item.rarity == rarity:
                items.append((slot.item, slot.quantity))
        return items
    
    def _auto_sort(self):
        """Automatically sort inventory by type and rarity."""
        if not self.auto_sort_enabled:
            return
        
        # Collect all items
        all_items = []
        for slot in self.slots:
            if not slot.is_empty():
                all_items.append((slot.item, slot.quantity))
            slot.item = None
            slot.quantity = 0
        
        # Sort by type, then rarity, then name
        all_items.sort(key=lambda x: (
            x[0].item_type.value,
            list(ItemRarity).index(x[0].rarity),
            x[0].name
        ))
        
        # Re-add items to inventory
        for item, quantity in all_items:
            self.add_item(item, quantity)
    
    def get_inventory_value(self) -> int:
        """Calculate total value of all items in inventory."""
        total_value = 0
        for slot in self.slots:
            if not slot.is_empty():
                total_value += slot.item.get_effective_value() * slot.quantity
        return total_value
    
    def search_items(self, search_term: str) -> List[Tuple[Item, int, int]]:
        """Search for items by name or description."""
        results = []
        search_term = search_term.lower()
        
        for i, slot in enumerate(self.slots):
            if not slot.is_empty():
                item = slot.item
                if (search_term in item.name.lower() or 
                    search_term in item.description.lower()):
                    results.append((item, slot.quantity, i))
        
        return results
    
    def cleanup_broken_items(self) -> int:
        """Remove all broken items from inventory."""
        removed_count = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item.is_broken():
                slot.item = None
                slot.quantity = 0
                removed_count += 1
        return removed_count

class Equipment:
    """Player equipment system."""
    
    def __init__(self):
        self.equipped_items: Dict[str, Optional[Item]] = {
            "helmet": None,
            "chest": None,
            "legs": None,
            "boots": None,
            "weapon": None,
            "shield": None,
            "ring1": None,
            "ring2": None,
            "necklace": None
        }
        self.set_bonuses: Dict[str, Dict[str, Any]] = {}
    
    def equip_item(self, item: Item, slot: str) -> Optional[Item]:
        """Equip an item, returns previously equipped item if any."""
        if slot not in self.equipped_items:
            return None
        
        # Check if item can be equipped in this slot
        if not self._can_equip_in_slot(item, slot):
            return None
        
        previous_item = self.equipped_items[slot]
        self.equipped_items[slot] = item
        
        self._update_set_bonuses()
        return previous_item
    
    def unequip_item(self, slot: str) -> Optional[Item]:
        """Unequip item from slot."""
        if slot not in self.equipped_items:
            return None
        
        item = self.equipped_items[slot]
        self.equipped_items[slot] = None
        
        self._update_set_bonuses()
        return item
    
    def _can_equip_in_slot(self, item: Item, slot: str) -> bool:
        """Check if item can be equipped in the specified slot."""
        slot_type_mapping = {
            "helmet": ItemType.ARMOR,
            "chest": ItemType.ARMOR,
            "legs": ItemType.ARMOR,
            "boots": ItemType.ARMOR,
            "weapon": ItemType.WEAPON,
            "shield": ItemType.ARMOR,
            "ring1": ItemType.ARMOR,
            "ring2": ItemType.ARMOR,
            "necklace": ItemType.ARMOR
        }
        
        return slot_type_mapping.get(slot) == item.item_type
    
    def _update_set_bonuses(self):
        """Update set bonuses based on equipped items."""
        # Implementation would check for matching item sets
        # and apply appropriate bonuses
        pass
    
    def get_total_stats(self) -> ItemStats:
        """Calculate total stats from all equipped items."""
        total_stats = ItemStats()
        
        for item in self.equipped_items.values():
            if item is not None:
                total_stats.damage += item.stats.damage
                total_stats.defense += item.stats.defense
                total_stats.weight += item.stats.weight
        
        return total_stats
    
    def get_equipped_items(self) -> List[Tuple[str, Item]]:
        """Get all equipped items with their slot names."""
        equipped = []
        for slot, item in self.equipped_items.items():
            if item is not None:
                equipped.append((slot, item))
        return equipped 