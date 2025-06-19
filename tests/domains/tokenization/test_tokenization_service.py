"""
Tests for TokenizationService
"""

import unittest
from pathlib import Path
from typing import List, Dict, Any

from app.domains.tokenization.tokenization_service import TokenizationService


class TestTokenizationService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()
    
    def test_basic_tokenization(self):
        """Test basic tokenization functionality."""
        text = "Hello, world! This is a test."
        tokens = self.service.tokenize(text)
        
        # Should return some tokens
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        
        # Each token should have required fields
        for token in tokens:
            self.assertIn('type', token)
            self.assertIn('text', token)
            self.assertIn('start', token)
            self.assertIn('end', token)
    
    def test_detokenization(self):
        """Test detokenization functionality."""
        text = "def hello(): return 'world'"
        tokens = self.service.tokenize(text)
        detokenized = self.service.detokenize(tokens)
        
        # Should return a string
        self.assertIsInstance(detokenized, str)
        self.assertGreater(len(detokenized), 0)
    
    def test_empty_input(self):
        """Test handling of empty input."""
        tokens = self.service.tokenize("")
        self.assertIsInstance(tokens, list)
        
        detokenized = self.service.detokenize([])
        self.assertEqual(detokenized, "")
    
    def test_python_code_tokenization(self):
        """Test tokenization of Python code."""
        python_code = '''
def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b

result = calculate_sum(5, 3)
print(f"Result: {result}")
'''
        tokens = self.service.tokenize(python_code)
        
        # Should tokenize Python code properly
        self.assertGreater(len(tokens), 0)
        
        # Should contain function definition
        function_tokens = [t for t in tokens if t['type'] == 'function_definition']
        self.assertGreater(len(function_tokens), 0)
    
    def test_file_path_detection(self):
        """Test language detection from file path."""
        # Test with Python file
        tokens = self.service.tokenize("def test(): pass", Path("test.py"))
        self.assertIsInstance(tokens, list)
        
        # Test without file path
        tokens = self.service.tokenize("def test(): pass")
        self.assertIsInstance(tokens, list)


class TestTokenizationWithTestFiles(unittest.TestCase):
    """Tests that use actual test files."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()
    
    def test_tokenization_with_calculator_file(self):
        """Test tokenization with calculator test file."""
        test_file_path = Path("resources/test/test_file.py")
        
        if not test_file_path.exists():
            self.skipTest(f"Test file {test_file_path} not found")
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tokens = self.service.tokenize(content, test_file_path)
        
        # Basic validation
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 100)  # Should have many tokens for a substantial file
        
        # Should have function definitions
        function_tokens = [t for t in tokens if t['type'] == 'function_definition']
        self.assertGreater(len(function_tokens), 0)
        
        print(f"✅ Tokenized {test_file_path.name}: {len(tokens)} tokens, {len(function_tokens)} functions")
    
    def test_tokenization_comparison_between_files(self):
        """Test tokenization and basic comparison between different files."""
        file1_path = Path("resources/test/test_file.py")
        file2_path = Path("resources/test/test_file2.py")
        
        if not file1_path.exists() or not file2_path.exists():
            self.skipTest("Test files not found")
        
        # Tokenize both files
        with open(file1_path, 'r', encoding='utf-8') as f:
            content1 = f.read()
        with open(file2_path, 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        tokens1 = self.service.tokenize(content1, file1_path)
        tokens2 = self.service.tokenize(content2, file2_path)
        
        # Both should have tokens
        self.assertGreater(len(tokens1), 0)
        self.assertGreater(len(tokens2), 0)
        
        # Test similarity using the similarity service
        similarity_result = self.service.similarity_service.compare_similarity(tokens1, tokens2)
        
        # Should return similarity metrics
        self.assertIn('jaccard_similarity', similarity_result)
        self.assertIn('type_similarity', similarity_result)
        self.assertIsInstance(similarity_result['jaccard_similarity'], float)
        self.assertIsInstance(similarity_result['type_similarity'], float)
        
        print(f"✅ File comparison - Jaccard: {similarity_result['jaccard_similarity']:.3f}, "
              f"Type: {similarity_result['type_similarity']:.3f}")


if __name__ == "__main__":
    unittest.main() 