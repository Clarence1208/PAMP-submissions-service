"""
Tests for TokenizationService
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock, call
import subprocess

from app.domains.tokenization.tokenization_service import TokenizationService
from app.domains.repositories.fetchers.github_fetcher import _extract_repo_name, _normalize_github_url
from app.shared.exceptions import ValidationException


class TestTokenizationService(unittest.TestCase):
    """Comprehensive unit tests for TokenizationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()

    def test_init_successful(self):
        """Test successful initialization of TokenizationService."""
        service = TokenizationService()
        self.assertIsNotNone(service.parsers)
        self.assertIn('.py', service.parsers)
        self.assertIn('python', service.parsers)
        self.assertIsNotNone(service.similarity_service)

    def test_detect_language_by_file_extension(self):
        """Test language detection based on file extension."""
        # Python file
        python_file = Path("test.py")
        lang = self.service._detect_language(file_path=python_file)
        self.assertEqual(lang, '.py')

        # Unknown extension defaults to Python
        unknown_file = Path("test.xyz")
        lang = self.service._detect_language(file_path=unknown_file)
        self.assertEqual(lang, '.py')

    def test_detect_language_without_file_path(self):
        """Test language detection without file path."""
        lang = self.service._detect_language(content="def test(): pass")
        self.assertEqual(lang, '.py')

    def test_tokenize_simple_python_code(self):
        """Test tokenization of simple Python code."""
        code = "def hello():\n    return 'world'"
        tokens = self.service.tokenize(code)
        
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        
        # Check for expected token types
        token_types = [token['type'] for token in tokens]
        self.assertIn('function_definition', token_types)
        self.assertIn('return_statement', token_types)

    def test_tokenize_empty_string(self):
        """Test tokenization of empty string."""
        tokens = self.service.tokenize("")
        self.assertIsInstance(tokens, list)
        # Empty string should still produce some tokens (like module)

    def test_tokenize_with_file_path(self):
        """Test tokenization with file path parameter."""
        code = "x = 42"
        file_path = Path("test.py")
        tokens = self.service.tokenize(code, file_path)
        
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_complex_python_code(self):
        """Test tokenization of complex Python code."""
        code = '''
import os
from typing import List

class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x: int) -> int:
        """Add x to current value."""
        if x > 0:
            self.value += x
        return self.value
    
    def multiply(self, factor: float) -> float:
        for i in range(int(factor)):
            self.value *= 2
        return self.value

def main():
    calc = Calculator()
    result = calc.add(10)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
'''
        tokens = self.service.tokenize(code)
        
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 20)  # Should have many tokens
        
        # Check for various expected token types
        token_types = [token['type'] for token in tokens]
        expected_types = [
            'import_statement', 'import_from_statement', 'class_definition',
            'function_definition', 'if_statement', 'for_statement',
            'assignment', 'call', 'return_statement'
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, token_types, f"Missing token type: {expected_type}")

    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_with_parsing_error(self, mock_logger):
        """Test tokenization handles parsing errors gracefully."""
        # Invalid Python syntax
        invalid_code = "def invalid( syntax error"
        tokens = self.service.tokenize(invalid_code)
        
        # Should return empty list on error
        self.assertIsInstance(tokens, list)

    def test_extract_tokens_recursively(self):
        """Test that _extract_tokens processes nested structures."""
        code = '''
def outer():
    def inner():
        return 42
    return inner()
'''
        tokens = self.service.tokenize(code)
        
        # Should find both function definitions
        function_tokens = [t for t in tokens if t['type'] == 'function_definition']
        self.assertGreaterEqual(len(function_tokens), 2)

    def test_token_structure(self):
        """Test that tokens have correct structure."""
        code = "def test(): pass"
        tokens = self.service.tokenize(code)
        
        for token in tokens:
            self.assertIsInstance(token, dict)
            self.assertIn('type', token)
            self.assertIn('text', token)
            self.assertIn('start', token)
            self.assertIn('end', token)
            
            # Check data types
            self.assertIsInstance(token['type'], str)
            self.assertIsInstance(token['text'], str)
            self.assertIsInstance(token['start'], int)
            self.assertIsInstance(token['end'], int)

    def test_detokenize_simple(self):
        """Test detokenization of simple token list."""
        tokens = [
            {'text': 'def', 'type': 'keyword'},
            {'text': 'hello', 'type': 'identifier'},
            {'text': '()', 'type': 'parameters'},
            {'text': ':', 'type': 'colon'}
        ]
        
        result = self.service.detokenize(tokens)
        self.assertEqual(result, "def hello () :")

    def test_detokenize_empty_list(self):
        """Test detokenization of empty token list."""
        result = self.service.detokenize([])
        self.assertEqual(result, "")

    def test_detokenize_tokens_without_text(self):
        """Test detokenization handles tokens without text."""
        tokens = [
            {'text': 'def', 'type': 'keyword'},
            {'type': 'unknown'},  # No text field
            {'text': 'hello', 'type': 'identifier'}
        ]
        
        result = self.service.detokenize(tokens)
        self.assertEqual(result, "def hello")

    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_detokenize_with_error(self, mock_logger):
        """Test detokenization handles errors gracefully."""
        # Malformed token structure that will cause an exception
        invalid_tokens = [None, {'text': 'test'}]
        
        result = self.service.detokenize(invalid_tokens)
        # Should return empty string on error
        self.assertEqual(result, "")

    def test_tokenize_project_invalid_path(self):
        """Test tokenize_project with invalid path."""
        invalid_path = Path("/nonexistent/path")
        
        with self.assertRaises(ValidationException):
            self.service.tokenize_project(invalid_path)

    def test_tokenize_project_file_instead_of_directory(self):
        """Test tokenize_project with file path instead of directory."""
        with tempfile.NamedTemporaryFile(suffix='.py') as temp_file:
            file_path = Path(temp_file.name)
            
            with self.assertRaises(ValidationException):
                self.service.tokenize_project(file_path)

    @patch('builtins.print')
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_success(self, mock_logger, mock_print):
        """Test successful project tokenization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create test Python files
            (project_path / "test1.py").write_text("def func1(): pass")
            (project_path / "test2.py").write_text("def func2(): return 42")
            (project_path / "readme.txt").write_text("Not a Python file")
            
            # Should not raise exception
            self.service.tokenize_project(project_path)
            
            # Check that print was called for Python files
            print_calls = mock_print.call_args_list
            self.assertGreater(len(print_calls), 0)

    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_file_read_error(self, mock_logger, mock_open):
        """Test tokenize_project handles file read errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "test.py").write_text("def test(): pass")
            
            # Should handle the error gracefully
            self.service.tokenize_project(project_path)
            
            # Check that error was logged
            mock_logger.error.assert_called()

    def test_create_temp_directory(self):
        """Test temporary directory creation."""
        # This method was removed from TokenizationService, so we'll skip this test
        # or test the actual functionality through the submission fetcher
        self.skipTest("_create_temp_directory method was moved to SubmissionFetcher")

    def test_extract_repo_name_standard_url(self):
        """Test repository name extraction from standard GitHub URL."""
        url = "https://github.com/user/repo-name"
        name = _extract_repo_name(url)
        self.assertEqual(name, "repo-name")

    def test_extract_repo_name_with_git_suffix(self):
        """Test repository name extraction with .git suffix."""
        url = "https://github.com/user/repo-name.git"
        name = _extract_repo_name(url)
        self.assertEqual(name, "repo-name")

    def test_extract_repo_name_with_trailing_slash(self):
        """Test repository name extraction with trailing slash."""
        url = "https://github.com/user/repo-name/"
        name = _extract_repo_name(url)
        self.assertEqual(name, "repo-name")

    def test_extract_repo_name_invalid_url(self):
        """Test repository name extraction from invalid URL."""
        url = "invalid-url"
        name = _extract_repo_name(url)
        self.assertEqual(name, "repo")

    def test_normalize_github_url_already_git(self):
        """Test URL normalization for already .git URL."""
        url = "https://github.com/user/repo.git"
        normalized = _normalize_github_url(url)
        self.assertEqual(normalized, "https://github.com/user/repo.git")

    def test_normalize_github_url_web_format(self):
        """Test URL normalization for web format."""
        url = "https://github.com/user/repo"
        normalized = _normalize_github_url(url)
        self.assertEqual(normalized, "https://github.com/user/repo.git")

    def test_normalize_github_url_other_format(self):
        """Test URL normalization for other formats."""
        url = "git@github.com:user/repo.git"
        normalized = _normalize_github_url(url)
        self.assertEqual(normalized, "https://github.com/user/repo.git")

    def test_clone_github_repo_success(self):
        """Test successful GitHub repository cloning."""
        # This method was moved to GithubFetcher, so we'll skip this test
        self.skipTest("GitHub cloning methods moved to GithubFetcher")

    def test_clone_github_repo_failure(self):
        """Test GitHub repository cloning failure."""
        # This method was moved to GithubFetcher, so we'll skip this test
        self.skipTest("GitHub cloning methods moved to GithubFetcher")

    def test_clone_github_repo_timeout(self):
        """Test GitHub repository cloning timeout."""
        # This method was moved to GithubFetcher, so we'll skip this test
        self.skipTest("GitHub cloning methods moved to GithubFetcher")

    def test_clone_github_repo_general_exception(self):
        """Test GitHub repository cloning general exception."""
        # This method was moved to GithubFetcher, so we'll skip this test
        self.skipTest("GitHub cloning methods moved to GithubFetcher")

    def test_clone_github_repo_removes_git_directory(self):
        """Test that .git directory is removed after cloning."""
        # This method was moved to GithubFetcher, so we'll skip this test
        self.skipTest("GitHub cloning methods moved to GithubFetcher")

    @patch('app.domains.tokenization.tokenization_service.Language')
    def test_setup_parsers_failure(self, mock_language):
        """Test parser setup failure handling."""
        mock_language.side_effect = Exception("Parser initialization failed")
        
        with self.assertRaises(Exception):
            TokenizationService()

    def test_tokenize_with_missing_parser(self):
        """Test tokenization when no parser is available for the language."""
        # Create a service but remove all parsers
        service = TokenizationService()
        service.parsers = {}  # Clear all parsers
        
        result = service.tokenize("def test(): pass")
        self.assertEqual(result, [])

    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_with_parsing_exception(self, mock_logger):
        """Test tokenization when parser throws an exception."""
        service = TokenizationService()
        
        # Mock the parser to raise an exception
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parsing error")
        service.parsers['.py'] = mock_parser
        
        result = service.tokenize("def test(): pass")
        self.assertEqual(result, [])
        mock_logger.error.assert_called()

    @patch('builtins.print')
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_with_non_file_paths(self, mock_logger, mock_print):
        """Test tokenize_project handling of non-file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create a subdirectory (non-file)
            subdir = project_path / "subdir"
            subdir.mkdir()
            
            # Create a Python file
            (project_path / "test.py").write_text("def test(): pass")
            
            self.service.tokenize_project(project_path)
            
            # Should log warning about skipping non-file path
            mock_logger.warning.assert_called()

    def test_normalize_github_url_other_formats(self):
        """Test URL normalization for other formats (fallback case)."""
        # Test a URL that doesn't match the specific patterns
        url = "git@github.com:user/repo.git"
        normalized = _normalize_github_url(url)
        self.assertEqual(normalized, "https://github.com/user/repo.git")


class TestTokenizationServiceIntegration(unittest.TestCase):
    """Integration tests for TokenizationService with real file operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()

    def test_tokenize_real_python_file(self):
        """Test tokenization of a real Python file."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write('''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class MathUtils:
    @staticmethod
    def factorial(n):
        if n == 0:
            return 1
        return n * MathUtils.factorial(n-1)

if __name__ == "__main__":
    print(fibonacci(10))
    print(MathUtils.factorial(5))
''')
            temp_file_path = Path(temp_file.name)

        try:
            # Read and tokenize the file
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            tokens = self.service.tokenize(content, temp_file_path)
            
            # Verify comprehensive tokenization
            self.assertGreater(len(tokens), 30)
            
            token_types = [token['type'] for token in tokens]
            expected_types = [
                'function_definition', 'class_definition', 'if_statement',
                'return_statement', 'call', 'binary_operator', 'string'
            ]
            
            for expected_type in expected_types:
                self.assertIn(expected_type, token_types)
            
            # Check that tokens have proper line information
            for token in tokens:
                self.assertIsInstance(token['start'], int)
                self.assertIsInstance(token['end'], int)
                self.assertGreaterEqual(token['start'], 0)
                self.assertGreaterEqual(token['end'], token['start'])

        finally:
            # Clean up
            temp_file_path.unlink()

    def test_roundtrip_tokenize_detokenize(self):
        """Test that tokenize->detokenize preserves essential information."""
        original_code = "def greet(name): return f'Hello, {name}!'"
        
        tokens = self.service.tokenize(original_code)
        detokenized = self.service.detokenize(tokens)
        
        # Should contain the essential elements
        self.assertIn('def', detokenized)
        self.assertIn('greet', detokenized)
        self.assertIn('return', detokenized)


if __name__ == '__main__':
    unittest.main() 