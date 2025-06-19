#!/usr/bin/env python3
"""
Game UI Module for Game Project
Modern graphical user interface components and event handling.
"""

import pygame
import sys
from typing import List, Dict, Any, Tuple, Optional, Callable
from enum import Enum
from dataclasses import dataclass

class UIElementType(Enum):
    """Types of UI elements available."""
    BUTTON = "button"
    LABEL = "label"
    TEXTBOX = "textbox"
    SLIDER = "slider"
    PROGRESS_BAR = "progress_bar"
    PANEL = "panel"

@dataclass
class Position:
    """Position in 2D space."""
    x: float
    y: float

@dataclass
class Size:
    """Size dimensions."""
    width: float
    height: float

@dataclass
class Color:
    """RGBA color representation."""
    r: int
    g: int
    b: int
    a: int = 255

class UIElement:
    """Base class for all UI elements."""
    
    def __init__(self, element_id: str, position: Position, size: Size):
        self.id = element_id
        self.position = position
        self.size = size
        self.visible = True
        self.enabled = True
        self.z_index = 0
        self.parent = None
        self.children = []
        self.event_handlers = {}
    
    def add_child(self, child: 'UIElement'):
        """Add a child element."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'UIElement'):
        """Remove a child element."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle UI events."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type](event_data)
    
    def render(self, screen):
        """Render the UI element."""
        if not self.visible:
            return
        
        # Render children
        for child in sorted(self.children, key=lambda c: c.z_index):
            child.render(screen)

class Button(UIElement):
    """Interactive button element."""
    
    def __init__(self, element_id: str, position: Position, size: Size, 
                 text: str, font_size: int = 16):
        super().__init__(element_id, position, size)
        self.text = text
        self.font_size = font_size
        self.background_color = Color(100, 100, 100)
        self.text_color = Color(255, 255, 255)
        self.hover_color = Color(120, 120, 120)
        self.pressed_color = Color(80, 80, 80)
        self.is_hovered = False
        self.is_pressed = False
    
    def set_click_handler(self, handler: Callable):
        """Set click event handler."""
        self.event_handlers['click'] = handler
    
    def render(self, screen):
        """Render the button."""
        if not self.visible:
            return
        
        # Determine color based on state
        color = self.background_color
        if self.is_pressed:
            color = self.pressed_color
        elif self.is_hovered:
            color = self.hover_color
        
        # Draw button background
        pygame.draw.rect(screen, (color.r, color.g, color.b), 
                        (self.position.x, self.position.y, self.size.width, self.size.height))
        
        # Draw button text (simplified - would need actual font rendering)
        # This is a placeholder for actual text rendering
        pass

class ProgressBar(UIElement):
    """Visual progress indicator."""
    
    def __init__(self, element_id: str, position: Position, size: Size, 
                 min_value: float = 0, max_value: float = 100):
        super().__init__(element_id, position, size)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = min_value
        self.background_color = Color(50, 50, 50)
        self.fill_color = Color(0, 255, 0)
        self.border_color = Color(255, 255, 255)
    
    def set_value(self, value: float):
        """Set the progress value."""
        self.current_value = max(self.min_value, min(self.max_value, value))
    
    def get_percentage(self) -> float:
        """Get progress as percentage."""
        if self.max_value == self.min_value:
            return 0.0
        return (self.current_value - self.min_value) / (self.max_value - self.min_value)
    
    def render(self, screen):
        """Render the progress bar."""
        if not self.visible:
            return
        
        # Draw background
        pygame.draw.rect(screen, (self.background_color.r, self.background_color.g, self.background_color.b),
                        (self.position.x, self.position.y, self.size.width, self.size.height))
        
        # Draw progress fill
        fill_width = self.size.width * self.get_percentage()
        pygame.draw.rect(screen, (self.fill_color.r, self.fill_color.g, self.fill_color.b),
                        (self.position.x, self.position.y, fill_width, self.size.height))
        
        # Draw border
        pygame.draw.rect(screen, (self.border_color.r, self.border_color.g, self.border_color.b),
                        (self.position.x, self.position.y, self.size.width, self.size.height), 2)

class Panel(UIElement):
    """Container panel for organizing UI elements."""
    
    def __init__(self, element_id: str, position: Position, size: Size):
        super().__init__(element_id, position, size)
        self.background_color = Color(30, 30, 30, 200)  # Semi-transparent
        self.border_color = Color(100, 100, 100)
        self.padding = 10
    
    def auto_layout(self):
        """Automatically layout child elements."""
        if not self.children:
            return
        
        # Simple vertical layout
        current_y = self.position.y + self.padding
        for child in self.children:
            child.position.x = self.position.x + self.padding
            child.position.y = current_y
            current_y += child.size.height + 5  # 5px spacing
    
    def render(self, screen):
        """Render the panel and its children."""
        if not self.visible:
            return
        
        # Draw background
        surface = pygame.Surface((self.size.width, self.size.height))
        surface.set_alpha(self.background_color.a)
        surface.fill((self.background_color.r, self.background_color.g, self.background_color.b))
        screen.blit(surface, (self.position.x, self.position.y))
        
        # Draw border
        pygame.draw.rect(screen, (self.border_color.r, self.border_color.g, self.border_color.b),
                        (self.position.x, self.position.y, self.size.width, self.size.height), 1)
        
        # Render children
        super().render(screen)

class GameUIManager:
    """Main UI manager for the game."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_elements = {}
        self.modal_stack = []
        self.event_queue = []
        self.animation_manager = AnimationManager()
    
    def add_element(self, element: UIElement):
        """Add a UI element to the manager."""
        self.ui_elements[element.id] = element
    
    def remove_element(self, element_id: str):
        """Remove a UI element by ID."""
        if element_id in self.ui_elements:
            del self.ui_elements[element_id]
    
    def get_element(self, element_id: str) -> Optional[UIElement]:
        """Get a UI element by ID."""
        return self.ui_elements.get(element_id)
    
    def show_modal(self, modal_element: UIElement):
        """Show a modal dialog."""
        self.modal_stack.append(modal_element)
    
    def hide_modal(self):
        """Hide the current modal dialog."""
        if self.modal_stack:
            self.modal_stack.pop()
    
    def handle_mouse_event(self, event_type: str, position: Tuple[int, int]):
        """Handle mouse events."""
        # Check modals first
        if self.modal_stack:
            # Only handle events for the top modal
            return
        
        # Check all elements for collision
        for element in self.ui_elements.values():
            if self._point_in_element(position, element):
                element.handle_event(event_type, {'position': position})
    
    def _point_in_element(self, point: Tuple[int, int], element: UIElement) -> bool:
        """Check if a point is inside a UI element."""
        return (element.position.x <= point[0] <= element.position.x + element.size.width and
                element.position.y <= point[1] <= element.position.y + element.size.height)
    
    def update(self, delta_time: float):
        """Update UI elements and animations."""
        self.animation_manager.update(delta_time)
        
        # Process event queue
        while self.event_queue:
            event = self.event_queue.pop(0)
            self._process_event(event)
    
    def _process_event(self, event: Dict[str, Any]):
        """Process a UI event."""
        pass  # Implementation would depend on specific event types
    
    def render(self, screen):
        """Render all UI elements."""
        # Render main UI elements
        for element in sorted(self.ui_elements.values(), key=lambda e: e.z_index):
            element.render(screen)
        
        # Render modals on top
        for modal in self.modal_stack:
            modal.render(screen)

class AnimationManager:
    """Manages UI animations and transitions."""
    
    def __init__(self):
        self.active_animations = []
    
    def add_animation(self, target: UIElement, property_name: str, 
                     end_value: Any, duration: float, ease_function: str = "linear"):
        """Add an animation to the queue."""
        animation = {
            'target': target,
            'property': property_name,
            'start_value': getattr(target, property_name),
            'end_value': end_value,
            'duration': duration,
            'elapsed': 0.0,
            'ease_function': ease_function
        }
        self.active_animations.append(animation)
    
    def update(self, delta_time: float):
        """Update all active animations."""
        finished_animations = []
        
        for animation in self.active_animations:
            animation['elapsed'] += delta_time
            progress = min(animation['elapsed'] / animation['duration'], 1.0)
            
            # Apply easing function
            eased_progress = self._apply_easing(progress, animation['ease_function'])
            
            # Interpolate value
            start_val = animation['start_value']
            end_val = animation['end_value']
            current_val = start_val + (end_val - start_val) * eased_progress
            
            # Set the property
            setattr(animation['target'], animation['property'], current_val)
            
            if progress >= 1.0:
                finished_animations.append(animation)
        
        # Remove finished animations
        for animation in finished_animations:
            self.active_animations.remove(animation)
    
    def _apply_easing(self, progress: float, ease_function: str) -> float:
        """Apply easing function to animation progress."""
        if ease_function == "ease_in":
            return progress * progress
        elif ease_function == "ease_out":
            return 1 - (1 - progress) * (1 - progress)
        elif ease_function == "ease_in_out":
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - 2 * (1 - progress) * (1 - progress)
        else:  # linear
            return progress 