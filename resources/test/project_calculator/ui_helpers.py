#!/usr/bin/env python3
"""
UI Helpers Module for Calculator Project
Command-line interface utilities and formatting functions.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Union

class ConsoleFormatter:
    """Console formatting and display utilities."""
    
    # ANSI color codes
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'reset': '\033[0m'
    }
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Add color to text for terminal display."""
        color_code = cls.COLORS.get(color.lower(), '')
        reset_code = cls.COLORS['reset']
        return f"{color_code}{text}{reset_code}"
    
    @classmethod
    def create_header(cls, title: str, width: int = 50) -> str:
        """Create a formatted header with borders."""
        border = "=" * width
        padding = (width - len(title) - 2) // 2
        if padding < 0:
            padding = 0
        padded_title = f"{' ' * padding} {title} {' ' * padding}"
        if len(padded_title) < width:
            padded_title += " " * (width - len(padded_title))
        
        return f"\n{border}\n{padded_title}\n{border}\n"
    
    @classmethod
    def create_table(cls, headers: List[str], rows: List[List[str]]) -> str:
        """Create a formatted table from headers and rows."""
        if not headers or not rows:
            return ""
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Create separator
        separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
        
        # Create header row
        header_row = "|" + "|".join(f" {header.ljust(col_widths[i])} " 
                                   for i, header in enumerate(headers)) + "|"
        
        # Create data rows
        data_rows = []
        for row in rows:
            row_str = "|" + "|".join(f" {str(row[i] if i < len(row) else '').ljust(col_widths[i])} " 
                                    for i in range(len(col_widths))) + "|"
            data_rows.append(row_str)
        
        # Combine all parts
        table_parts = [separator, header_row, separator] + data_rows + [separator]
        return "\n".join(table_parts)

class InputValidator:
    """Input validation utilities for calculator interface."""
    
    @staticmethod
    def get_numeric_input(prompt: str, 
                         allow_float: bool = True, 
                         min_value: Optional[float] = None,
                         max_value: Optional[float] = None) -> Union[int, float]:
        """Get validated numeric input from user."""
        while True:
            try:
                user_input = input(prompt).strip()
                
                if not user_input:
                    print("Please enter a value.")
                    continue
                
                # Try to convert to number
                if allow_float and '.' in user_input:
                    value = float(user_input)
                else:
                    value = int(user_input)
                
                # Check bounds
                if min_value is not None and value < min_value:
                    print(f"Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"Value must be at most {max_value}")
                    continue
                
                return value
                
            except ValueError:
                print("Please enter a valid number.")
                continue
    
    @staticmethod
    def get_choice_input(prompt: str, choices: List[str], case_sensitive: bool = False) -> str:
        """Get validated choice input from user."""
        if not case_sensitive:
            choices_lower = [choice.lower() for choice in choices]
        
        while True:
            user_input = input(prompt).strip()
            
            if not user_input:
                print("Please make a choice.")
                continue
            
            check_input = user_input if case_sensitive else user_input.lower()
            check_choices = choices if case_sensitive else choices_lower
            
            if check_input in check_choices:
                # Return original case choice
                if case_sensitive:
                    return user_input
                else:
                    return choices[choices_lower.index(check_input)]
            
            print(f"Please choose from: {', '.join(choices)}")
    
    @staticmethod
    def confirm_action(prompt: str, default: bool = False) -> bool:
        """Get yes/no confirmation from user."""
        default_text = "(Y/n)" if default else "(y/N)"
        full_prompt = f"{prompt} {default_text}: "
        
        while True:
            user_input = input(full_prompt).strip().lower()
            
            if not user_input:
                return default
            
            if user_input in ['y', 'yes', 'true', '1']:
                return True
            elif user_input in ['n', 'no', 'false', '0']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")

class MenuSystem:
    """Simple menu system for console applications."""
    
    def __init__(self, title: str):
        self.title = title
        self.options = []
        self.callbacks = {}
    
    def add_option(self, key: str, description: str, callback=None):
        """Add a menu option."""
        self.options.append((key, description))
        if callback:
            self.callbacks[key] = callback
    
    def display_menu(self):
        """Display the menu options."""
        print(ConsoleFormatter.create_header(self.title))
        
        for key, description in self.options:
            print(f"  {key}. {description}")
        
        print()
    
    def run(self):
        """Run the menu system."""
        while True:
            self.display_menu()
            
            valid_keys = [key for key, _ in self.options]
            choice = InputValidator.get_choice_input(
                "Select an option: ", 
                valid_keys + ['quit', 'q', 'exit']
            )
            
            if choice.lower() in ['quit', 'q', 'exit']:
                break
            
            if choice in self.callbacks:
                try:
                    self.callbacks[choice]()
                except Exception as e:
                    print(f"Error executing option: {e}")
                    input("Press Enter to continue...")
            else:
                print(f"Option '{choice}' not implemented yet.")
                input("Press Enter to continue...")
            
            print()  # Add spacing between menu iterations

class ProgressBar:
    """Simple progress bar for long-running operations."""
    
    def __init__(self, total: int, width: int = 50, fill_char: str = '█'):
        self.total = total
        self.width = width
        self.fill_char = fill_char
        self.current = 0
    
    def update(self, progress: int):
        """Update progress bar."""
        self.current = min(progress, self.total)
        filled = int(self.width * self.current / self.total)
        bar = self.fill_char * filled + '-' * (self.width - filled)
        percent = 100 * self.current / self.total
        
        print(f'\rProgress: |{bar}| {percent:.1f}% ({self.current}/{self.total})', end='')
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def increment(self):
        """Increment progress by 1."""
        self.update(self.current + 1) 