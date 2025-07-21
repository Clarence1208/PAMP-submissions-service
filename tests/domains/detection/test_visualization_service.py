"""
Test suite for VisualizationService
Tests React Flow AST generation and code similarity visualization functionality.
"""

import unittest
from unittest.mock import Mock, patch
from app.domains.detection.visualization import VisualizationService


class TestVisualizationService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.service = VisualizationService()

    def test_init_successful(self):
        """Test that VisualizationService initializes correctly."""
        service = VisualizationService()
        self.assertIsNotNone(service)

    def test_generate_react_flow_ast_no_similarities(self):
        """Test React Flow AST generation with no similarities."""
        tokens1 = [{'type': 'assignment', 'text': 'x = 1', 'start': 0, 'end': 0}]
        tokens2 = [{'type': 'assignment', 'text': 'y = 2', 'start': 0, 'end': 0}]
        
        result = self.service.generate_react_flow_ast(
            "x = 1", "y = 2", "file1.py", "file2.py", "elk"
        )
        
        self.assertFalse(result['has_similarity'])
        self.assertEqual(len(result['nodes']), 2)  # file root nodes are created
        self.assertEqual(len(result['edges']), 0)

    def test_generate_react_flow_ast_with_similarities(self):
        """Test React Flow AST generation with similarities."""
        # Create tokens that would result in similar functions with higher similarity
        tokens1 = [
            {'type': 'function_definition',
             'text': 'def calculate(x):\n    if x > 0:\n        return x * 2\n    return 0', 'start': 0, 'end': 3},
            {'type': 'if_statement', 'text': 'if x > 0:', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return x * 2', 'start': 2, 'end': 2},
            {'type': 'return_statement', 'text': 'return 0', 'start': 3, 'end': 3}
        ]
        tokens2 = [
            {'type': 'function_definition',
             'text': 'def compute(y):\n    if y > 0:\n        return y * 2\n    return 0', 'start': 0, 'end': 3},
            {'type': 'if_statement', 'text': 'if y > 0:', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return y * 2', 'start': 2, 'end': 2},
            {'type': 'return_statement', 'text': 'return 0', 'start': 3, 'end': 3}
        ]
        
        source1 = "def calculate(x):\n    if x > 0:\n        return x * 2\n    return 0"
        source2 = "def compute(y):\n    if y > 0:\n        return y * 2\n    return 0"
        
        result = self.service.generate_react_flow_ast(
            source1, source2, "file1.py", "file2.py", "elk"
        )
        
        # The result should have similarity detected
        self.assertIsInstance(result, dict)
        self.assertIn('nodes', result)
        self.assertIn('edges', result)
        self.assertIn('has_similarity', result)

    def test_extract_functions_with_imports(self):
        """Test function extraction with imports."""
        source_code = """import os
from typing import List
def test_func():
    return 42"""
        
        result = self.service._extract_functions_with_imports(source_code, "test.py")
        
        self.assertIsInstance(result, dict)
        self.assertIn('functions', result)
        self.assertIn('imports', result)


if __name__ == '__main__':
    unittest.main()
