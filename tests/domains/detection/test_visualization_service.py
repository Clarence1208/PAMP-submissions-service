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
            tokens1, tokens2, "x = 1", "y = 2", "file1.py", "file2.py", "elk"
        )
        
        self.assertFalse(result['has_similarity'])
        self.assertEqual(len(result['nodes']), 0)
        self.assertEqual(len(result['edges']), 0)
        self.assertEqual(result['message'], "No similarities detected between files")

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
            tokens1, tokens2, source1, source2, "file1.py", "file2.py", "elk"
        )
        
        # The result should have similarity detected
        self.assertIsInstance(result, dict)
        self.assertIn('nodes', result)
        self.assertIn('edges', result)
        self.assertIn('has_similarity', result)

    def test_generate_optimized_file_nodes(self):
        """Test optimized file node generation."""
        tokens = [
            {'type': 'function_definition', 'text': 'def test():\n    return 42', 'start': 1, 'end': 2}
        ]
        source_code = "def test():\n    return 42"
        shared_blocks = []
        
        nodes, edges, counter = self.service._generate_optimized_file_nodes(
            tokens, source_code, "test.py", "file1", 0, shared_blocks
        )
        
        self.assertIsInstance(nodes, list)
        self.assertIsInstance(edges, list)
        self.assertIsInstance(counter, int)
        self.assertGreater(len(nodes), 0)
        
        # Check for file root node
        file_root = next((node for node in nodes if node['id'] == 'file1_root'), None)
        self.assertIsNotNone(file_root)
        self.assertEqual(file_root['type'], 'group')
        self.assertEqual(file_root['data']['filename'], 'test.py')

    def test_generate_optimized_file_nodes_with_imports(self):
        """Test file node generation with import statements."""
        tokens = [
            {'type': 'import_statement', 'text': 'import os', 'start': 1, 'end': 1},
            {'type': 'function_definition', 'text': 'def test():\n    return 42', 'start': 2, 'end': 3}
        ]
        source_code = "import os\ndef test():\n    return 42"
        shared_blocks = []
        
        nodes, edges, counter = self.service._generate_optimized_file_nodes(
            tokens, source_code, "test.py", "file1", 0, shared_blocks
        )
        
        # Should have file root, import group, and function nodes
        self.assertGreaterEqual(len(nodes), 3)
        
        # Check for import group node
        import_node = next((node for node in nodes if 'imports_group' in node['id']), None)
        self.assertIsNotNone(import_node)
        self.assertEqual(import_node['data']['type'], 'import_group')

    def test_analyze_function_calls(self):
        """Test function call analysis."""
        tokens = [
            {'type': 'function_definition', 'text': 'def caller():\n    return callee()', 'start': 1, 'end': 2},
            {'type': 'function_definition', 'text': 'def callee():\n    return 42', 'start': 4, 'end': 5}
        ]
        source_code = "def caller():\n    return callee()\n\ndef callee():\n    return 42"
        functions = {
            'caller': {'function_name': 'caller'},
            'callee': {'function_name': 'callee'}
        }
        
        edges = self.service._analyze_function_calls(tokens, source_code, functions, "file1")
        
        self.assertIsInstance(edges, list)

    def test_extract_functions_with_positions_simple_function(self):
        """Test function extraction with positions."""
        tokens = [
            {'type': 'function_definition', 'text': 'def test_func():\n    return 42', 'start': 1, 'end': 2}
        ]
        source_code = "def test_func():\n    return 42"
        
        functions = self.service._extract_functions_with_positions(tokens, source_code)
        
        self.assertIsInstance(functions, dict)
        self.assertGreater(len(functions), 0)
        
        # Check first function
        func_key = list(functions.keys())[0]
        func_data = functions[func_key]
        self.assertIn('function_name', func_data)
        self.assertIn('start_line', func_data)
        self.assertIn('end_line', func_data)
        self.assertIn('code_block', func_data)

    def test_extract_function_name_from_text(self):
        """Test function name extraction from token text."""
        func_token = {'text': 'def my_function(x, y):', 'type': 'function_definition'}
        
        name = self.service._extract_function_name(func_token, [])
        
        self.assertEqual(name, 'my_function')

    def test_extract_function_name_malformed(self):
        """Test function name extraction from malformed token."""
        func_token = {'text': 'not a function', 'type': 'function_definition'}
        
        name = self.service._extract_function_name(func_token, [])
        
        self.assertEqual(name, 'unknown_function')

    def test_extract_code_block_valid_range(self):
        """Test code block extraction with valid line range."""
        source_lines = ["line 0", "line 1", "line 2", "line 3"]
        
        code_block = self.service._extract_code_block(source_lines, 2, 4)
        
        self.assertEqual(code_block, "line 2\nline 3")

    def test_extract_code_block_empty_source(self):
        """Test code block extraction with empty source."""
        code_block = self.service._extract_code_block([], 1, 2)
        
        self.assertEqual(code_block, "")

    def test_extract_code_block_invalid_range(self):
        """Test code block extraction with invalid range."""
        source_lines = ["line 0", "line 1", "line 2"]
        
        # Start line > end line
        code_block = self.service._extract_code_block(source_lines, 3, 1)
        self.assertEqual(code_block, "")
        
        # Negative line numbers
        code_block = self.service._extract_code_block(source_lines, -1, 2)
        self.assertEqual(code_block, "")

    def test_extract_imports(self):
        """Test import extraction from source code."""
        source_code = """import os
from typing import List, Dict
import sys
from pathlib import Path
"""
        
        imports = self.service._extract_imports([], source_code)
        
        self.assertIsInstance(imports, list)
        self.assertGreater(len(imports), 0)
        
        # Check for expected imports
        import_modules = [imp['module'] for imp in imports]
        self.assertIn('os', import_modules)
        self.assertIn('typing', import_modules)
        self.assertIn('sys', import_modules)
        self.assertIn('pathlib', import_modules)

    def test_find_similarity_for_function(self):
        """Test finding similarity block for a specific function."""
        shared_blocks = [
            {'file1_function': 'func_0_test1', 'file2_function': 'func_0_test2', 'similarity_score': 0.9},
            {'file1_function': 'func_1_calc', 'file2_function': 'func_1_compute', 'similarity_score': 0.85}
        ]
        
        # Test finding file1 function
        result = self.service._find_similarity_for_function('func_0_test1', shared_blocks, 'file1')
        self.assertIsNotNone(result)
        self.assertEqual(result['similarity_score'], 0.9)
        
        # Test finding file2 function
        result = self.service._find_similarity_for_function('func_0_test2', shared_blocks, 'file2')
        self.assertIsNotNone(result)
        self.assertEqual(result['similarity_score'], 0.9)
        
        # Test non-existent function
        result = self.service._find_similarity_for_function('nonexistent', shared_blocks, 'file1')
        self.assertIsNone(result)

    def test_generate_similarity_edges(self):
        """Test similarity edge generation."""
        shared_blocks = [
            {'file1_function': 'func_0_test1', 'file2_function': 'func_0_test2', 'similarity_score': 0.9}
        ]
        
        all_nodes = [
            {'id': 'file1_func_0_test1', 'type': 'default'},
            {'id': 'file2_func_0_test2', 'type': 'default'}
        ]
        
        edges = self.service._generate_similarity_edges(shared_blocks, all_nodes)
        
        self.assertIsInstance(edges, list)
        self.assertEqual(len(edges), 1)
        
        edge = edges[0]
        self.assertEqual(edge['source'], 'file1_func_0_test1')
        self.assertEqual(edge['target'], 'file2_func_0_test2')
        self.assertTrue(edge['animated'])
        self.assertEqual(edge['data']['type'], 'similarity')

    def test_find_containing_function(self):
        """Test finding which function contains a given line."""
        source_lines = [
            "def function1():",
            "    x = 1",
            "    return x",
            "",
            "def function2():",
            "    y = 2",
            "    return y"
        ]
        function_names = ['function1', 'function2']
        
        # Line 2 should be in function1
        result = self.service._find_containing_function(2, source_lines, function_names)
        self.assertEqual(result, 'function1')
        
        # Line 6 should be in function2
        result = self.service._find_containing_function(6, source_lines, function_names)
        self.assertEqual(result, 'function2')
        
        # Line 0 (before any function) should return None
        result = self.service._find_containing_function(0, source_lines, function_names)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main() 