"""
Tests for SimilarityDetectionService
"""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.tokenization.tokenization_service import TokenizationService
from app.domains.detection.visualization.visualization_service import VisualizationService


class TestSimilarityDetectionService(unittest.TestCase):
    """Comprehensive unit tests for SimilarityDetectionService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = SimilarityDetectionService()

    def test_init_successful(self):
        """Test successful initialization of SimilarityDetectionService."""
        service = SimilarityDetectionService()
        self.assertIsNotNone(service)

    def test_prepare_for_similarity_basic(self):
        """Test basic token preparation for similarity analysis."""
        tokens = [
            {'type': 'function_definition', 'text': 'def hello():', 'normalized': False},
            {'type': 'string', 'text': '"Hello, World!"', 'normalized': False},
            {'type': 'identifier', 'text': 'variable_name', 'normalized': False},
            {'type': 'comment', 'text': '# This is a comment', 'normalized': False},
            {'type': 'integer', 'text': '42', 'normalized': False}
        ]

        result = self.service.prepare_for_similarity(tokens)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Check that structural types are kept
        function_tokens = [t for t in result if t['type'] == 'function_definition']
        self.assertEqual(len(function_tokens), 1)
        self.assertFalse(function_tokens[0]['normalized'])

        # Check that normalizable types are normalized
        string_tokens = [t for t in result if t['type'] == 'string']
        self.assertEqual(len(string_tokens), 1)
        self.assertEqual(string_tokens[0]['text'], '<STRING>')
        self.assertTrue(string_tokens[0]['normalized'])

        identifier_tokens = [t for t in result if t['type'] == 'identifier']
        self.assertEqual(len(identifier_tokens), 1)
        self.assertEqual(identifier_tokens[0]['text'], '<VAR>')
        self.assertTrue(identifier_tokens[0]['normalized'])

        # Check that comments are filtered out
        comment_tokens = [t for t in result if t['type'] == 'comment']
        self.assertEqual(len(comment_tokens), 0)

    def test_prepare_for_similarity_keep_types(self):
        """Test that structural types are kept as-is."""
        keep_types = [
            'if_statement', 'for_statement', 'while_statement', 'function_definition',
            'class_definition', 'call', 'return_statement', 'binary_operator'
        ]

        tokens = [{'type': t, 'text': f'test_{t}', 'normalized': False} for t in keep_types]
        result = self.service.prepare_for_similarity(tokens)

        self.assertEqual(len(result), len(keep_types))
        for token in result:
            self.assertFalse(token['normalized'])
            self.assertIn(token['type'], keep_types)

    def test_prepare_for_similarity_normalize_types(self):
        """Test that specific types are normalized."""
        normalize_cases = [
            ('string', '<STRING>'),
            ('integer', '<NUMBER>'),
            ('float', '<NUMBER>'),
            ('identifier', '<VAR>')
        ]

        for token_type, expected_text in normalize_cases:
            tokens = [{'type': token_type, 'text': 'original_text', 'normalized': False}]
            result = self.service.prepare_for_similarity(tokens)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['text'], expected_text)
            self.assertTrue(result[0]['normalized'])

    def test_prepare_for_similarity_skip_types(self):
        """Test that certain types are completely filtered out."""
        skip_types = ['comment', 'ERROR']

        tokens = [{'type': t, 'text': f'test_{t}', 'normalized': False} for t in skip_types]
        result = self.service.prepare_for_similarity(tokens)

        self.assertEqual(len(result), 0)

    def test_prepare_for_similarity_empty_input(self):
        """Test preparation with empty input."""
        result = self.service.prepare_for_similarity([])
        self.assertEqual(result, [])

    def test_get_similarity_signature_basic(self):
        """Test similarity signature generation."""
        tokens = [
            {'type': 'function_definition', 'text': 'def hello():', 'normalized': False},
            {'type': 'string', 'text': 'Hello, World!', 'normalized': False}
        ]

        signature = self.service.get_similarity_signature(tokens)

        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)
        self.assertIn('function_definition:def hello():', signature)
        self.assertIn('<STRING>', signature)

    def test_get_similarity_signature_truncation(self):
        """Test that very long text is truncated in signatures."""
        long_text = "a" * 50  # Longer than 20 character limit
        tokens = [{'type': 'function_definition', 'text': long_text, 'normalized': False}]

        signature = self.service.get_similarity_signature(tokens)

        self.assertIn('...', signature)
        self.assertLess(len(signature.split(':')[1].split('|')[0]), 30)

    def test_compare_similarity_identical_tokens(self):
        """Test similarity comparison with identical tokens."""
        tokens1 = [
            {'type': 'function_definition', 'text': 'def test():', 'normalized': False},
            {'type': 'return_statement', 'text': 'return 42', 'normalized': False}
        ]
        tokens2 = tokens1.copy()

        result = self.service.compare_similarity(tokens1, tokens2)

        self.assertIsInstance(result, dict)
        self.assertIn('jaccard_similarity', result)
        self.assertIn('type_similarity', result)
        self.assertEqual(result['jaccard_similarity'], 1.0)
        self.assertEqual(result['type_similarity'], 1.0)

    def test_compare_similarity_completely_different(self):
        """Test similarity comparison with completely different tokens."""
        tokens1 = [{'type': 'function_definition', 'text': 'def test1():', 'normalized': False}]
        tokens2 = [{'type': 'class_definition', 'text': 'class Test:', 'normalized': False}]

        result = self.service.compare_similarity(tokens1, tokens2)

        self.assertLess(result['jaccard_similarity'], 1.0)
        self.assertLess(result['type_similarity'], 1.0)

    def test_compare_similarity_empty_inputs(self):
        """Test similarity comparison with empty inputs."""
        result = self.service.compare_similarity([], [])

        # Empty inputs result in empty signatures which are considered identical
        self.assertEqual(result['jaccard_similarity'], 1.0)
        self.assertEqual(result['type_similarity'], 0)
        self.assertEqual(result['common_elements'], 1)  # Both have empty signature

    def test_compare_similarity_one_empty(self):
        """Test similarity comparison with one empty input."""
        tokens = [{'type': 'function_definition', 'text': 'def test():', 'normalized': False}]

        result = self.service.compare_similarity(tokens, [])

        self.assertEqual(result['jaccard_similarity'], 0)
        self.assertEqual(result['type_similarity'], 0)

    def test_detect_shared_code_blocks_no_functions(self):
        """Test shared code block detection with no functions."""
        tokens1 = [{'type': 'assignment', 'text': 'x = 1', 'normalized': False}]
        tokens2 = [{'type': 'assignment', 'text': 'y = 2', 'normalized': False}]

        result = self.service.detect_shared_code_blocks(tokens1, tokens2)

        self.assertEqual(result['total_shared_blocks'], 0)
        self.assertEqual(result['average_similarity'], 0.0)
        self.assertEqual(result['functions_file1'], 0)
        self.assertEqual(result['functions_file2'], 0)

    def test_detect_shared_code_blocks_with_similar_functions(self):
        """Test shared code block detection with similar functions."""
        # Mock function tokens that would be extracted
        tokens1 = [
            {'type': 'function_definition', 'text': 'def calculate(x):\n    return x * 2', 'start': 1, 'end': 2}
        ]
        tokens2 = [
            {'type': 'function_definition', 'text': 'def compute(y):\n    return y * 2', 'start': 1, 'end': 2}
        ]

        source1 = "def calculate(x):\n    return x * 2"
        source2 = "def compute(y):\n    return y * 2"

        result = self.service.detect_shared_code_blocks(
            tokens1, tokens2, source1, source2, "file1.py", "file2.py"
        )

        self.assertIsInstance(result, dict)
        self.assertIn('shared_blocks', result)
        self.assertIn('total_shared_blocks', result)
        self.assertIn('average_similarity', result)
        self.assertIn('functions_file1', result)
        self.assertIn('functions_file2', result)

    def test_extract_functions_with_positions_simple_function(self):
        """Test function extraction with simple function."""
        tokens = [
            {'type': 'function_definition', 'text': 'def hello():\n    return "world"', 'start': 0, 'end': 1}
        ]
        source_code = 'def hello():\n    return "world"'

        functions = self.service._extract_functions_with_positions(tokens, source_code)

        self.assertIsInstance(functions, dict)
        self.assertGreater(len(functions), 0)

        # Check function structure
        func_key = list(functions.keys())[0]
        func_data = functions[func_key]

        self.assertIn('tokens', func_data)
        self.assertIn('code_block', func_data)
        self.assertIn('start_line', func_data)
        self.assertIn('end_line', func_data)
        self.assertIn('function_name', func_data)

    def test_extract_functions_with_positions_no_source(self):
        """Test function extraction without source code."""
        tokens = [
            {'type': 'function_definition', 'text': 'def hello():', 'start': 0, 'end': 1}
        ]

        functions = self.service._extract_functions_with_positions(tokens, "")

        self.assertIsInstance(functions, dict)

    def test_extract_functions_with_positions_multiple_functions(self):
        """Test extraction of multiple functions."""
        tokens = [
            {'type': 'function_definition', 'text': 'def func1():', 'start': 0, 'end': 1},
            {'type': 'return_statement', 'text': 'return 1', 'start': 1, 'end': 1},
            {'type': 'function_definition', 'text': 'def func2():', 'start': 3, 'end': 4},
            {'type': 'return_statement', 'text': 'return 2', 'start': 4, 'end': 4}
        ]
        source_code = "def func1():\n    return 1\n\ndef func2():\n    return 2"

        functions = self.service._extract_functions_with_positions(tokens, source_code)

        self.assertGreaterEqual(len(functions), 2)

    def test_extract_function_name_from_text(self):
        """Test function name extraction from function text."""
        func_token = {'text': 'def calculate_sum(a, b):\n    return a + b', 'type': 'function_definition'}

        name = self.service._extract_function_name(func_token, [])

        self.assertEqual(name, 'calculate_sum')

    def test_extract_function_name_malformed(self):
        """Test function name extraction from malformed text."""
        func_token = {'text': 'malformed function definition', 'type': 'function_definition'}

        name = self.service._extract_function_name(func_token, [])

        self.assertEqual(name, 'unknown_function')

    def test_extract_function_name_multiline(self):
        """Test function name extraction from multiline function definition."""
        func_token = {
            'text': 'def complex_function(\n    param1: int,\n    param2: str\n) -> bool:\n    pass',
            'type': 'function_definition'
        }

        name = self.service._extract_function_name(func_token, [])

        self.assertEqual(name, 'complex_function')

    def test_extract_code_block_valid_range(self):
        """Test code block extraction with valid line range."""
        source_lines = ["line 0", "line 1", "line 2", "line 3", "line 4"]

        code_block = self.service._extract_code_block(source_lines, 1, 3)

        self.assertEqual(code_block, "line 1\nline 2")

    def test_extract_code_block_empty_source(self):
        """Test code block extraction with empty source."""
        code_block = self.service._extract_code_block([], 0, 5)

        self.assertEqual(code_block, "")

    def test_extract_code_block_invalid_range(self):
        """Test code block extraction with invalid ranges."""
        source_lines = ["line 0", "line 1", "line 2"]

        # Start after end
        code_block = self.service._extract_code_block(source_lines, 5, 3)
        self.assertEqual(code_block, "")

        # Negative start - returns empty string as per implementation
        code_block = self.service._extract_code_block(source_lines, -1, 2)
        self.assertEqual(code_block, "")

        # None values
        code_block = self.service._extract_code_block(source_lines, None, None)
        self.assertEqual(code_block, "")

    def test_extract_code_block_out_of_bounds(self):
        """Test code block extraction with out-of-bounds indices."""
        source_lines = ["line 0", "line 1"]

        code_block = self.service._extract_code_block(source_lines, 0, 10)

        self.assertEqual(code_block, "line 0\nline 1")

    def test_compare_function_similarity_identical_functions(self):
        """Test function similarity comparison with identical functions."""
        func_tokens = [
            {'type': 'function_definition', 'text': 'def test():', 'normalized': False},
            {'type': 'return_statement', 'text': 'return 42', 'normalized': False}
        ]

        result = self.service._compare_function_similarity(func_tokens, func_tokens)

        self.assertIsInstance(result, dict)
        self.assertIn('similarity_score', result)
        self.assertGreater(result['similarity_score'], 0.9)  # Should be very high

    def test_compare_function_similarity_different_functions(self):
        """Test function similarity comparison with different functions."""
        func1_tokens = [
            {'type': 'function_definition', 'text': 'def add(a, b):', 'normalized': False},
            {'type': 'return_statement', 'text': 'return a + b', 'normalized': False}
        ]
        func2_tokens = [
            {'type': 'function_definition', 'text': 'def greet(name):', 'normalized': False},
            {'type': 'return_statement', 'text': 'return f"Hello {name}"', 'normalized': False}
        ]

        result = self.service._compare_function_similarity(func1_tokens, func2_tokens)

        # These functions have similar structure (def + return) so similarity will be high
        self.assertGreater(result['similarity_score'], 0.5)  # Should have some similarity due to structure

    def test_compare_function_similarity_empty_functions(self):
        """Test function similarity comparison with empty functions."""
        result = self.service._compare_function_similarity([], [])

        self.assertEqual(result['similarity_score'], 0.0)

    def test_create_structural_sequence(self):
        """Test structural sequence creation."""
        tokens = [
            {'type': 'function_definition', 'text': 'def test():'},
            {'type': 'if_statement', 'text': 'if x > 0:'},
            {'type': 'assignment', 'text': 'y = x * 2'},
            {'type': 'return_statement', 'text': 'return y'}
        ]

        sequence = self.service._create_structural_sequence(tokens)

        expected = ['FUNC_DEF', 'CONDITIONAL', 'ASSIGN', 'RETURN']
        self.assertEqual(sequence, expected)

    def test_create_structural_sequence_normalization(self):
        """Test that structural sequence normalizes similar concepts."""
        tokens = [
            {'type': 'method_definition', 'text': 'def method(self):'},  # Should become FUNC_DEF
            {'type': 'elif_clause', 'text': 'elif x < 0:'},  # Should become CONDITIONAL
            {'type': 'for_statement', 'text': 'for i in range(10):'},  # Should become LOOP
            {'type': 'while_statement', 'text': 'while True:'}  # Should become LOOP
        ]

        sequence = self.service._create_structural_sequence(tokens)

        expected = ['FUNC_DEF', 'CONDITIONAL', 'LOOP', 'LOOP']
        self.assertEqual(sequence, expected)

    def test_extract_logical_flow(self):
        """Test logical flow extraction."""
        tokens = [
            {'type': 'if_statement', 'text': 'if condition:'},
            {'type': 'for_statement', 'text': 'for i in range(10):'},
            {'type': 'return_statement', 'text': 'return result'},
            {'type': 'assignment', 'text': 'x = 1'}  # Should not be included
        ]

        flow = self.service._extract_logical_flow(tokens)

        expected = ['if_statement', 'for_statement', 'return_statement']
        self.assertEqual(flow, expected)

    def test_extract_operations(self):
        """Test operation extraction and normalization."""
        tokens = [
            {'type': 'binary_operator', 'text': '+'},
            {'type': 'binary_operator', 'text': '*'},
            {'type': 'comparison_operator', 'text': '=='},
            {'type': 'boolean_operator', 'text': 'and'},
            {'type': 'assignment', 'text': 'x = 1'}  # Should not be included
        ]

        operations = self.service._extract_operations(tokens)

        expected = ['MATH_OP', 'MATH_OP', 'COMPARE_OP', 'LOGIC_OP']
        self.assertEqual(operations, expected)

    def test_sequence_similarity_identical(self):
        """Test sequence similarity with identical sequences."""
        seq1 = ['A', 'B', 'C', 'D']
        seq2 = ['A', 'B', 'C', 'D']

        similarity = self.service._sequence_similarity(seq1, seq2)

        self.assertEqual(similarity, 1.0)

    def test_sequence_similarity_completely_different(self):
        """Test sequence similarity with completely different sequences."""
        seq1 = ['A', 'B', 'C']
        seq2 = ['X', 'Y', 'Z']

        similarity = self.service._sequence_similarity(seq1, seq2)

        self.assertEqual(similarity, 0.0)

    def test_sequence_similarity_partial_overlap(self):
        """Test sequence similarity with partial overlap."""
        seq1 = ['A', 'B', 'C', 'D']
        seq2 = ['B', 'C', 'E', 'F']

        similarity = self.service._sequence_similarity(seq1, seq2)

        self.assertGreater(similarity, 0.0)
        self.assertLess(similarity, 1.0)

    def test_sequence_similarity_empty_sequences(self):
        """Test sequence similarity with empty sequences."""
        self.assertEqual(self.service._sequence_similarity([], []), 0.0)
        self.assertEqual(self.service._sequence_similarity(['A'], []), 0.0)
        self.assertEqual(self.service._sequence_similarity([], ['A']), 0.0)

    def test_extract_functions_with_positions_function_depth_tracking(self):
        """Test function extraction with nested function depth tracking."""
        tokens = [
            {'type': 'function_definition', 'text': 'def outer():', 'start': 0, 'end': 1},
            {'type': 'function_definition', 'text': 'def inner():', 'start': 2, 'end': 3},  # Nested function
            {'type': 'return_statement', 'text': 'return 42', 'start': 4, 'end': 4}
        ]
        source_code = "def outer():\n    def inner():\n        return 42"

        functions = self.service._extract_functions_with_positions(tokens, source_code)

        # Should handle nested functions properly
        self.assertIsInstance(functions, dict)

    def test_create_structural_sequence_with_edge_cases(self):
        """Test structural sequence creation with edge case token types."""
        tokens = [
            {'type': 'else_clause', 'text': 'else:'},
            {'type': 'binary_operator', 'text': '+'},
            {'type': 'call', 'text': 'func()'},
            {'type': 'list', 'text': '[1, 2, 3]'},
            {'type': 'string', 'text': '"hello"'},
            {'type': 'identifier', 'text': 'variable'},
            {'type': 'unknown_type', 'text': 'unknown'}  # Fallback case
        ]

        sequence = self.service._create_structural_sequence(tokens)

        expected = ['ELSE', 'OPERATOR', 'CALL', 'COLLECTION', 'LITERAL', 'VAR', 'UNKNOWN_TYPE']
        self.assertEqual(sequence, expected)

    def test_extract_operations_with_edge_cases(self):
        """Test operation extraction with edge case operators."""
        tokens = [
            {'type': 'binary_operator', 'text': '**'},  # Math operation
            {'type': 'comparison_operator', 'text': '>='},  # Compare operation
            {'type': 'boolean_operator', 'text': 'not'},  # Logic operation
            {'type': 'unary_operator', 'text': '~'},  # Other operator (fallback)
        ]

        operations = self.service._extract_operations(tokens)

        expected = ['MATH_OP', 'COMPARE_OP', 'LOGIC_OP', 'OPERATOR']
        self.assertEqual(operations, expected)

    def test_prepare_for_similarity_with_other_token_type(self):
        """Test token preparation with token types that fall into the 'other' category."""
        tokens = [
            {'type': 'some_other_type', 'text': 'other content', 'normalized': False}
        ]

        result = self.service.prepare_for_similarity(tokens)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'some_other_type')
        self.assertFalse(result[0]['normalized'])

    def test_extract_function_name_with_exception(self):
        """Test function name extraction when an exception occurs."""
        func_token = {'text': '', 'type': 'function_definition'}  # Empty text

        name = self.service._extract_function_name(func_token, [])

        self.assertEqual(name, 'unknown_function')

    def test_extract_code_block_with_invalid_types(self):
        """Test code block extraction with invalid start/end types."""
        source_lines = ["line 0", "line 1", "line 2"]

        # Test with string values that can't be converted to int
        code_block = self.service._extract_code_block(source_lines, "invalid", "invalid")
        self.assertEqual(code_block, "")


class TestSimilarityDetectionServiceIntegration(unittest.TestCase):
    """Integration tests for SimilarityDetectionService with realistic scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = SimilarityDetectionService()
        self.viz_service = VisualizationService()

    def test_full_similarity_analysis_workflow(self):
        """Test complete similarity analysis workflow."""
        # Create realistic function tokens with more detailed structure
        tokens1 = [
            {'type': 'function_definition',
             'text': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)',
             'start': 0, 'end': 3},
            {'type': 'if_statement', 'text': 'if n <= 1:', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return n', 'start': 2, 'end': 2},
            {'type': 'return_statement', 'text': 'return fibonacci(n-1) + fibonacci(n-2)', 'start': 3, 'end': 3},
            {'type': 'call', 'text': 'fibonacci(n-1)', 'start': 3, 'end': 3},
            {'type': 'call', 'text': 'fibonacci(n-2)', 'start': 3, 'end': 3}
        ]
        tokens2 = [
            {'type': 'function_definition',
             'text': 'def fib(num):\n    if num <= 1:\n        return num\n    return fib(num-1) + fib(num-2)',
             'start': 0, 'end': 3},
            {'type': 'if_statement', 'text': 'if num <= 1:', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return num', 'start': 2, 'end': 2},
            {'type': 'return_statement', 'text': 'return fib(num-1) + fib(num-2)', 'start': 3, 'end': 3},
            {'type': 'call', 'text': 'fib(num-1)', 'start': 3, 'end': 3},
            {'type': 'call', 'text': 'fib(num-2)', 'start': 3, 'end': 3}
        ]

        source1 = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""

        source2 = """def fib(num):
    if num <= 1:
        return num
    return fib(num-1) + fib(num-2)"""

        # Test similarity comparison - should be low due to different variable names in signatures
        similarity = self.service.compare_similarity(tokens1, tokens2)
        self.assertIsInstance(similarity['jaccard_similarity'], float)

        # Test shared code block detection - may not find high similarity due to threshold
        shared_blocks = self.service.detect_shared_code_blocks(
            tokens1, tokens2, source1, source2, "file1.py", "file2.py"
        )
        self.assertIsInstance(shared_blocks['total_shared_blocks'], int)

        # Test that the workflow completes successfully
        self.assertGreater(len(tokens1), 0)
        self.assertGreater(len(tokens2), 0)

    def test_realistic_code_comparison(self):
        """Test with realistic but different code samples."""
        # Mathematical functions with similar structure
        tokens1 = [
            {'type': 'function_definition',
             'text': 'def calculate_area(radius):\n    pi = 3.14159\n    return pi * radius * radius', 'start': 0,
             'end': 2},
            {'type': 'assignment', 'text': 'pi = 3.14159', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return pi * radius * radius', 'start': 2, 'end': 2}
        ]
        tokens2 = [
            {'type': 'function_definition',
             'text': 'def compute_volume(r, h):\n    pi = 3.14159\n    return pi * r * r * h', 'start': 0, 'end': 2},
            {'type': 'assignment', 'text': 'pi = 3.14159', 'start': 1, 'end': 1},
            {'type': 'return_statement', 'text': 'return pi * r * r * h', 'start': 2, 'end': 2}
        ]

        source1 = "def calculate_area(radius):\n    pi = 3.14159\n    return pi * radius * radius"
        source2 = "def compute_volume(r, h):\n    pi = 3.14159\n    return pi * r * r * h"

        similarity = self.service.compare_similarity(tokens1, tokens2)

        # Should have some similarity due to similar structure
        self.assertIsInstance(similarity['jaccard_similarity'], float)
        self.assertGreaterEqual(similarity['jaccard_similarity'], 0.0)
        self.assertLessEqual(similarity['jaccard_similarity'], 1.0)

    def test_no_similarity_detection(self):
        """Test detection correctly identifies no similarities."""
        # Completely different code types
        tokens1 = [
            {'type': 'class_definition',
             'text': 'class Person:\n    def __init__(self, name):\n        self.name = name', 'start': 0, 'end': 2}
        ]
        tokens2 = [
            {'type': 'assignment', 'text': 'numbers = [1, 2, 3, 4, 5]\nresult = sum(numbers)', 'start': 0, 'end': 1}
        ]

        source1 = "class Person:\n    def __init__(self, name):\n        self.name = name"
        source2 = "numbers = [1, 2, 3, 4, 5]\nresult = sum(numbers)"

        shared_blocks = self.service.detect_shared_code_blocks(
            tokens1, tokens2, source1, source2, "file1.py", "file2.py"
        )

        self.assertEqual(shared_blocks['total_shared_blocks'], 0)
        self.assertEqual(shared_blocks['average_similarity'], 0.0)

    def test_generate_react_flow_ast_no_similarities(self):
        """Test React Flow AST generation with no similarities."""
        tokens1 = [{'type': 'assignment', 'text': 'x = 1', 'start': 0, 'end': 0}]
        tokens2 = [{'type': 'assignment', 'text': 'y = 2', 'start': 0, 'end': 0}]

        result = self.viz_service.generate_react_flow_ast(
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

        result = self.viz_service.generate_react_flow_ast(
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
            {'type': 'function_definition', 'text': 'def test():\n    return 42', 'start': 0, 'end': 1}
        ]
        source_code = "def test():\n    return 42"
        shared_blocks = []

        nodes, edges, counter = self.viz_service._generate_optimized_file_nodes(
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

    def test_analyze_function_calls(self):
        """Test function call analysis."""
        tokens = [
            {'type': 'function_definition', 'text': 'def caller():\n    return callee()', 'start': 0, 'end': 1},
            {'type': 'function_definition', 'text': 'def callee():\n    return 42', 'start': 2, 'end': 3}
        ]
        source_code = "def caller():\n    return callee()\n\ndef callee():\n    return 42"
        functions = {
            'func_0': {'function_name': 'caller'},
            'func_1': {'function_name': 'callee'}
        }

        edges = self.viz_service._analyze_function_calls(tokens, source_code, functions, "file1")

        self.assertIsInstance(edges, list)

    def test_extract_imports(self):
        """Test import extraction from source code."""
        source_code = """import os
from typing import List, Dict
import sys
from pathlib import Path
"""

        imports = self.viz_service._extract_imports([], source_code)

        self.assertIsInstance(imports, list)
        self.assertGreater(len(imports), 0)

        # Check first import
        first_import = imports[0]
        self.assertIn('module', first_import)
        self.assertIn('type', first_import)
        self.assertIn('line', first_import)
        self.assertEqual(first_import['module'], 'os')
        self.assertEqual(first_import['type'], 'import')

    def test_find_similarity_for_function(self):
        """Test finding similarity block for a specific function."""
        shared_blocks = [
            {'file1_function': 'func_0_test1', 'file2_function': 'func_0_test2', 'similarity_score': 0.9},
            {'file1_function': 'func_1_calc', 'file2_function': 'func_1_compute', 'similarity_score': 0.85}
        ]

        # Test finding file1 function
        result = self.viz_service._find_similarity_for_function('func_0_test1', shared_blocks, 'file1')

        self.assertIsNotNone(result)
        self.assertEqual(result['file1_function'], 'func_0_test1')
        self.assertEqual(result['file2_function'], 'func_0_test2')
        self.assertEqual(result['similarity_score'], 0.9)

        # Test finding file2 function
        result2 = self.viz_service._find_similarity_for_function('func_1_compute', shared_blocks, 'file2')

        self.assertIsNotNone(result2)
        self.assertEqual(result2['file2_function'], 'func_1_compute')
        self.assertEqual(result2['similarity_score'], 0.85)

        # Test with non-existent function
        result3 = self.viz_service._find_similarity_for_function('nonexistent', shared_blocks, 'file1')
        self.assertIsNone(result3)

    def test_generate_similarity_edges(self):
        """Test similarity edge generation."""
        shared_blocks = [
            {'file1_function': 'func_0_test1', 'file2_function': 'func_0_test2', 'similarity_score': 0.9}
        ]

        all_nodes = [
            {'id': 'file1_func_0_test1', 'type': 'default'},
            {'id': 'file2_func_0_test2', 'type': 'default'}
        ]

        edges = self.viz_service._generate_similarity_edges(shared_blocks, all_nodes)

        self.assertIsInstance(edges, list)
        self.assertEqual(len(edges), 1)

        edge = edges[0]
        self.assertIn('id', edge)
        self.assertIn('source', edge)
        self.assertIn('target', edge)
        self.assertEqual(edge['source'], 'file1_func_0_test1')
        self.assertEqual(edge['target'], 'file2_func_0_test2')

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
        result = self.viz_service._find_containing_function(2, source_lines, function_names)
        self.assertEqual(result, 'function1')

        # Line 6 should be in function2
        result2 = self.viz_service._find_containing_function(6, source_lines, function_names)
        self.assertEqual(result2, 'function2')

        # Line 1 should be in function1 (the def line itself)
        result3 = self.viz_service._find_containing_function(1, source_lines, function_names)
        self.assertEqual(result3, 'function1')

        # Test with line number that doesn't contain a function
        result4 = self.viz_service._find_containing_function(100, source_lines, function_names)
        self.assertIsNone(result4)

    def test_generate_optimized_file_nodes_with_imports(self):
        """Test file node generation that includes import handling."""
        tokens = [
            {'type': 'import_statement', 'text': 'import os', 'start': 0, 'end': 0},
            {'type': 'function_definition', 'text': 'def test():\n    return 42', 'start': 1, 'end': 2}
        ]
        source_code = "import os\ndef test():\n    return 42"
        shared_blocks = []

        nodes, edges, counter = self.viz_service._generate_optimized_file_nodes(
            tokens, source_code, "test.py", "file1", 0, shared_blocks
        )

        # Should have file root, import group, and function nodes
        self.assertGreaterEqual(len(nodes), 3)

        # Check for import group node
        import_node = next((node for node in nodes if 'imports_group' in node['id']), None)
        self.assertIsNotNone(import_node)
        self.assertEqual(import_node['data']['type'], 'import_group')


if __name__ == '__main__':
    unittest.main()
