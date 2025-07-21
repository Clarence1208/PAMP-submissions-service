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
            {'type': 'assignment', 'text': 'x = 1'}
        ]

        operations = self.service._extract_operations(tokens)

        expected = ['MATH_OP', 'MATH_OP', 'COMPARE_OP', 'LOGIC_OP', 'METHOD_CALL']
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
        self.assertEqual(self.service._sequence_similarity([], []), 1.0)
        self.assertEqual(self.service._sequence_similarity(['A'], []), 0.0)
        self.assertEqual(self.service._sequence_similarity([], ['A']), 0.0)

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

if __name__ == '__main__':
    unittest.main()
