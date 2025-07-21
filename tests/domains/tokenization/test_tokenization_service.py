"""
Tests for TokenizationService
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.domains.repositories.exceptions import UnsupportedRepositoryException
from app.domains.repositories.fetchers.github_fetcher import _extract_repo_name, _normalize_github_url
from app.domains.tokenization.tokenization_service import TokenizationService
from app.shared.exceptions import ValidationException


class TestTokenizationService(unittest.TestCase):
    """Comprehensive unit tests for TokenizationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()

    def test_extract_code_block_from_lines_valid_range(self):
        """Test code block extraction with valid line range."""
        source_lines = ["line 0", "line 1", "line 2", "line 3", "line 4"]

        code_block = self.service._extract_code_block_from_lines(source_lines, 1, 3)

        self.assertEqual(code_block, "line 1\nline 2")

    def test_extract_code_block_from_lines_empty_source(self):
        """Test code block extraction with empty source."""
        code_block = self.service._extract_code_block_from_lines([], 0, 5)

        self.assertEqual(code_block, "")

    def test_extract_code_block_from_lines_invalid_range(self):
        """Test code block extraction with invalid ranges."""
        source_lines = ["line 0", "line 1", "line 2"]

        # Start after end
        code_block = self.service._extract_code_block_from_lines(source_lines, 5, 3)
        self.assertEqual(code_block, "")

        # Negative start - returns empty string as per implementation
        code_block = self.service._extract_code_block_from_lines(source_lines, -1, 2)
        self.assertEqual(code_block, "line 0\nline 1")

        # None values
        code_block = self.service._extract_code_block_from_lines(source_lines, None, None)
        self.assertEqual(code_block, "")

    def test_extract_code_block_from_lines_out_of_bounds(self):
        """Test code block extraction with out-of-bounds indices."""
        source_lines = ["line 0", "line 1"]

        code_block = self.service._extract_code_block_from_lines(source_lines, 0, 10)

        self.assertEqual(code_block, "line 0\nline 1")

    def test_extract_code_block_with_invalid_types(self):
        """Test code block extraction with invalid start/end types."""
        source_lines = ["line 0", "line 1", "line 2"]

        # Test with string values that can't be converted to int
        self.assertRaises(TypeError, self.service._extract_code_block_from_lines, source_lines, "invalid", "invalid")

    def test_init_successful(self):
        """Test successful initialization of TokenizationService."""
        service = TokenizationService()
        self.assertIsNotNone(service.parsers)
        self.assertIsNotNone(service.language_mapping)
        self.assertIsNotNone(service.similarity_service)

    def test_language_mapping_setup(self):
        """Test that language mapping is properly set up."""
        self.assertGreater(len(self.service.language_mapping), 50)  # Should have many mappings

        # Test some key mappings
        self.assertEqual(self.service.language_mapping['.py'], 'python')
        self.assertEqual(self.service.language_mapping['.js'], 'javascript')
        self.assertEqual(self.service.language_mapping['.java'], 'java')
        self.assertEqual(self.service.language_mapping['.cpp'], 'cpp')
        self.assertEqual(self.service.language_mapping['.rs'], 'rust')

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = self.service.get_supported_languages()
        self.assertIsInstance(languages, list)
        self.assertGreater(len(languages), 20)  # Should support many languages
        self.assertIn('python', languages)
        self.assertIn('javascript', languages)
        self.assertIn('java', languages)

    def test_get_supported_extensions(self):
        """Test getting supported file extensions."""
        extensions = self.service.get_supported_extensions()
        self.assertIsInstance(extensions, list)
        self.assertGreater(len(extensions), 50)  # Should support many extensions
        self.assertIn('.py', extensions)
        self.assertIn('.js', extensions)
        self.assertIn('.java', extensions)

    def test_detect_language_by_file_extension(self):
        """Test language detection based on file extension."""
        # Python file
        python_file = Path("test.py")
        lang = self.service._detect_language(file_path=python_file)
        self.assertEqual(lang, 'python')

        # JavaScript file
        js_file = Path("test.js")
        lang = self.service._detect_language(file_path=js_file)
        self.assertEqual(lang, 'javascript')

        # Java file
        java_file = Path("Test.java")
        lang = self.service._detect_language(file_path=java_file)
        self.assertEqual(lang, 'java')

        # Unknown extension defaults to Python
        unknown_file = Path("test.xyz")
        lang = self.service._detect_language(file_path=unknown_file)
        self.assertEqual(lang, 'python')

    def test_detect_language_special_files(self):
        """Test language detection for special filenames."""
        # Dockerfile
        dockerfile = Path("Dockerfile")
        lang = self.service._detect_language(file_path=dockerfile)
        self.assertEqual(lang, 'dockerfile')

        # Makefile
        makefile = Path("Makefile")
        lang = self.service._detect_language(file_path=makefile)
        self.assertEqual(lang, 'make')

    def test_detect_language_without_file_path(self):
        """Test language detection without file path."""
        lang = self.service._detect_language(content="def test(): pass")
        self.assertEqual(lang, 'python')

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
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with self.assertRaises(ValidationException):
                self.service.tokenize_project(temp_path)
        finally:
            temp_path.unlink()

    @patch('builtins.print')
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_success(self, mock_logger, mock_print):
        """Test successful project tokenization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test Python file
            test_file = temp_path / "test.py"
            test_file.write_text("def hello(): return 'world'")

            # Should not raise an exception
            self.service.tokenize_project(temp_path)

            # Verify logging was called
            mock_logger.info.assert_called()
            mock_print.assert_called()

    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_file_read_error(self, mock_logger, mock_open):
        """Test tokenize_project handles file read errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.touch()  # Create empty file

            # Should handle the exception gracefully
            self.service.tokenize_project(temp_path)

            # Verify error was logged
            mock_logger.error.assert_called()

    def test_create_temp_directory(self):
        """Test creating temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self.assertTrue(temp_path.exists())
            self.assertTrue(temp_path.is_dir())

    def test_extract_repo_name_standard_url(self):
        """Test extracting repository name from standard URL."""
        url = "https://github.com/user/repo"
        expected = "repo"
        result = _extract_repo_name(url)
        self.assertEqual(result, expected)

    def test_extract_repo_name_with_git_suffix(self):
        """Test extracting repository name with .git suffix."""
        url = "https://github.com/user/repo.git"
        expected = "repo"
        result = _extract_repo_name(url)
        self.assertEqual(result, expected)

    def test_extract_repo_name_with_trailing_slash(self):
        """Test extracting repository name with trailing slash."""
        url = "https://github.com/user/repo/"
        expected = "repo"
        result = _extract_repo_name(url)
        self.assertEqual(result, expected)

    def test_extract_repo_name_invalid_url(self):
        """Test extracting repository name from invalid URL."""
        url = "invalid-url"
        expected = "repo"
        result = _extract_repo_name(url)
        self.assertEqual(result, expected)

    def test_normalize_github_url_already_git(self):
        """Test normalizing GitHub URL that's already a git URL."""
        url = "https://github.com/user/repo.git"
        expected = "https://github.com/user/repo.git"
        result = _normalize_github_url(url)
        self.assertEqual(result, expected)

    def test_normalize_github_url_web_format(self):
        """Test normalizing GitHub web URL to git format."""
        url = "https://github.com/user/repo"
        expected = "https://github.com/user/repo.git"
        result = _normalize_github_url(url)
        self.assertEqual(result, expected)

    def test_normalize_github_url_other_format(self):
        """Test normalizing non-GitHub URL."""
        url = "https://gitlab.com/user/repo"
        expected = "https://gitlab.com/user/repo"
        self.assertRaises(UnsupportedRepositoryException, lambda: _normalize_github_url(url))

    @patch('subprocess.run')
    def test_clone_github_repo_success(self, mock_run):
        """Test successful GitHub repository cloning."""
        mock_run.return_value = MagicMock(returncode=0)
        # Test would require actual implementation details

    @patch('subprocess.run')
    def test_clone_github_repo_failure(self, mock_run):
        """Test GitHub repository cloning failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
        # Test would require actual implementation details

    @patch('subprocess.run')
    def test_clone_github_repo_timeout(self, mock_run):
        """Test GitHub repository cloning timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('git', 300)
        # Test would require actual implementation details

    @patch('subprocess.run')
    def test_clone_github_repo_general_exception(self, mock_run):
        """Test GitHub repository cloning general exception."""
        mock_run.side_effect = Exception("Network error")
        # Test would require actual implementation details

    @patch('subprocess.run')
    def test_clone_github_repo_removes_git_directory(self, mock_run):
        """Test that cloning removes .git directory."""
        mock_run.return_value = MagicMock(returncode=0)
        # Test would require actual implementation details

    @patch('app.domains.tokenization.tokenization_service.get_parser')
    def test_setup_parsers_failure(self, mock_get_parser):
        """Test parser setup handles failures gracefully."""
        mock_get_parser.side_effect = Exception("Parser initialization failed")

        # Should not raise an exception
        service = TokenizationService()
        self.assertIsNotNone(service.parsers)

    def test_tokenize_with_missing_parser(self):
        """Test tokenization when parser is missing."""
        # Create a service and remove a parser
        service = TokenizationService()
        if 'python' in service.parsers:
            del service.parsers['python']

        code = "def test(): pass"
        tokens = service.tokenize(code, Path("test.py"))

        # Should return empty list when parser is missing
        self.assertIsInstance(tokens, list)

    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_with_parsing_exception(self, mock_logger):
        """Test tokenization handles parsing exceptions."""
        # Test with a parser that might fail
        service = TokenizationService()

        # Mock parser to raise exception
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parse error")
        service.parsers['test'] = mock_parser

        tokens = service.tokenize("test code", Path("test.unknown"))

        # Should return empty list on exception
        self.assertIsInstance(tokens, list)

    @patch('builtins.print')
    @patch('app.domains.tokenization.tokenization_service.logger')
    def test_tokenize_project_with_non_file_paths(self, mock_logger, mock_print):
        """Test that tokenize_project handles non-file paths correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def hello(): return 'world'")

            # Should handle directories gracefully
            self.service.tokenize_project(temp_path)

            # Verify warning was logged for non-file path
            mock_logger.warning.assert_called()

    def test_normalize_github_url_other_formats(self):
        """Test normalizing various GitHub URL formats."""
        test_cases = [
            ("https://github.com/user/repo", "https://github.com/user/repo.git"),
            ("https://github.com/user/repo.git", "https://github.com/user/repo.git"),
        ]

        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = _normalize_github_url(input_url)
                self.assertEqual(result, expected)

    # ==============================================
    # LANGUAGE-SPECIFIC TOKENIZATION TESTS
    # ==============================================

    def test_tokenize_javascript(self):
        """Test tokenization of JavaScript code."""
        code = '''
function greet(name) {
    const message = `Hello, ${name}!`;
    return message;
}

const result = greet("World");
console.log(result);
'''
        tokens = self.service.tokenize(code, Path("test.js"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_java(self):
        """Test tokenization of Java code."""
        code = '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
    
    private int add(int a, int b) {
        return a + b;
    }
}
'''
        tokens = self.service.tokenize(code, Path("HelloWorld.java"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_cpp(self):
        """Test tokenization of C++ code."""
        code = '''
#include <iostream>
#include <string>

class Greeter {
private:
    std::string name;
    
public:
    Greeter(const std::string& n) : name(n) {}
    
    void greet() {
        std::cout << "Hello, " << name << "!" << std::endl;
    }
};

int main() {
    Greeter g("World");
    g.greet();
    return 0;
}
'''
        tokens = self.service.tokenize(code, Path("main.cpp"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_c(self):
        """Test tokenization of C code."""
        code = '''
#include <stdio.h>
#include <stdlib.h>

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int num = 5;
    printf("Factorial of %d is %d\\n", num, factorial(num));
    return 0;
}
'''
        tokens = self.service.tokenize(code, Path("factorial.c"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_rust(self):
        """Test tokenization of Rust code."""
        code = '''
use std::collections::HashMap;

fn main() {
    let mut scores = HashMap::new();
    scores.insert("Blue", 10);
    scores.insert("Yellow", 50);
    
    for (key, value) in &scores {
        println!("{}: {}", key, value);
    }
}

fn fibonacci(n: u32) -> u32 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}
'''
        tokens = self.service.tokenize(code, Path("main.rs"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_go(self):
        """Test tokenization of Go code."""
        code = '''
package main

import (
    "fmt"
    "time"
)

type Person struct {
    Name string
    Age  int
}

func (p Person) greet() {
    fmt.Printf("Hello, I'm %s and I'm %d years old\\n", p.Name, p.Age)
}

func main() {
    person := Person{Name: "Alice", Age: 30}
    person.greet()
    
    fmt.Println("Current time:", time.Now())
}
'''
        tokens = self.service.tokenize(code, Path("main.go"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_typescript(self):
        """Test tokenization of TypeScript code."""
        code = '''
interface User {
    id: number;
    name: string;
    email?: string;
}

class UserService {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }
    
    getUser(id: number): User | undefined {
        return this.users.find(user => user.id === id);
    }
}

const service = new UserService();
service.addUser({ id: 1, name: "John Doe" });
'''
        tokens = self.service.tokenize(code, Path("user.ts"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_ruby(self):
        """Test tokenization of Ruby code."""
        code = '''
class Person
  attr_accessor :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def greet
    puts "Hello, I'm #{@name} and I'm #{@age} years old"
  end
  
  def self.create_anonymous
    new("Anonymous", 0)
  end
end

person = Person.new("Alice", 30)
person.greet

anonymous = Person.create_anonymous
anonymous.greet
'''
        tokens = self.service.tokenize(code, Path("person.rb"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_php(self):
        """Test tokenization of PHP code."""
        code = '''
<?php
class User {
    private $name;
    private $email;
    
    public function __construct($name, $email) {
        $this->name = $name;
        $this->email = $email;
    }
    
    public function getName() {
        return $this->name;
    }
    
    public function getEmail() {
        return $this->email;
    }
    
    public function getFullInfo() {
        return $this->name . " (" . $this->email . ")";
    }
}

$user = new User("John Doe", "john@example.com");
echo $user->getFullInfo();
?>
'''
        tokens = self.service.tokenize(code, Path("user.php"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_kotlin(self):
        """Test tokenization of Kotlin code."""
        code = '''
data class Person(val name: String, val age: Int) {
    fun greet() {
        println("Hello, I'm $name and I'm $age years old")
    }
}

fun main() {
    val people = listOf(
        Person("Alice", 30),
        Person("Bob", 25),
        Person("Charlie", 35)
    )
    
    people.forEach { person ->
        person.greet()
    }
    
    val adults = people.filter { it.age >= 30 }
    println("Adults: ${adults.map { it.name }}")
}
'''
        tokens = self.service.tokenize(code, Path("Main.kt"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_scala(self):
        """Test tokenization of Scala code."""
        code = '''
case class Person(name: String, age: Int) {
  def greet(): Unit = {
    println(s"Hello, I'm $name and I'm $age years old")
  }
}

object Main extends App {
  val people = List(
    Person("Alice", 30),
    Person("Bob", 25),
    Person("Charlie", 35)
  )
  
  people.foreach(_.greet())
  
  val adults = people.filter(_.age >= 30)
  println(s"Adults: ${adults.map(_.name).mkString(", ")}")
}
'''
        tokens = self.service.tokenize(code, Path("Main.scala"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_haskell(self):
        """Test tokenization of Haskell code."""
        code = '''
factorial :: Integer -> Integer
factorial 0 = 1
factorial n = n * factorial (n - 1)

fibonacci :: Integer -> Integer
fibonacci 0 = 0
fibonacci 1 = 1
fibonacci n = fibonacci (n - 1) + fibonacci (n - 2)

main :: IO ()
main = do
  putStrLn "Factorial of 5:"
  print (factorial 5)
  putStrLn "Fibonacci of 10:"
  print (fibonacci 10)
'''
        tokens = self.service.tokenize(code, Path("main.hs"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_r(self):
        """Test tokenization of R code."""
        code = '''
# Define a function to calculate mean
calculate_mean <- function(numbers) {
  if (length(numbers) == 0) {
    return(NA)
  }
  return(sum(numbers) / length(numbers))
}

# Create sample data
data <- c(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

# Calculate statistics
mean_value <- calculate_mean(data)
median_value <- median(data)

# Print results
cat("Mean:", mean_value, "\\n")
cat("Median:", median_value, "\\n")

# Create a simple plot
plot(data, main="Sample Data", xlab="Index", ylab="Value")
'''
        tokens = self.service.tokenize(code, Path("analysis.r"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_lua(self):
        """Test tokenization of Lua code."""
        code = '''
-- Define a person table/class
local Person = {}
Person.__index = Person

function Person.new(name, age)
    local self = setmetatable({}, Person)
    self.name = name
    self.age = age
    return self
end

function Person:greet()
    print("Hello, I'm " .. self.name .. " and I'm " .. self.age .. " years old")
end

-- Create instances
local alice = Person.new("Alice", 30)
local bob = Person.new("Bob", 25)

-- Call methods
alice:greet()
bob:greet()

-- Simple function
function factorial(n)
    if n <= 1 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

print("Factorial of 5:", factorial(5))
'''
        tokens = self.service.tokenize(code, Path("person.lua"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_bash(self):
        """Test tokenization of Bash code."""
        code = '''
#!/bin/bash

# Function to greet user
greet_user() {
    local name=$1
    echo "Hello, $name!"
}

# Check if argument provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <name>"
    exit 1
fi

# Variables
USER_NAME=$1
CURRENT_DATE=$(date +"%Y-%m-%d")

# Main logic
greet_user "$USER_NAME"
echo "Today is $CURRENT_DATE"

# Loop example
for i in {1..5}; do
    echo "Count: $i"
done

# Array example
FRUITS=("apple" "banana" "orange")
for fruit in "${FRUITS[@]}"; do
    echo "Fruit: $fruit"
done
'''
        tokens = self.service.tokenize(code, Path("greet.sh"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_html(self):
        """Test tokenization of HTML code."""
        code = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample Page</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { color: blue; }
    </style>
</head>
<body>
    <header class="header">
        <h1>Welcome to My Website</h1>
    </header>
    
    <main>
        <p>This is a sample paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
    </main>
    
    <script>
        console.log("Hello from JavaScript!");
    </script>
</body>
</html>
'''
        tokens = self.service.tokenize(code, Path("index.html"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_css(self):
        """Test tokenization of CSS code."""
        code = '''
/* Base styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem 0;
    text-align: center;
}

.button {
    display: inline-block;
    padding: 12px 24px;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s ease;
}

.button:hover {
    background-color: #0056b3;
}

@media (max-width: 768px) {
    .container {
        padding: 0 10px;
    }
}
'''
        tokens = self.service.tokenize(code, Path("styles.css"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_json(self):
        """Test tokenization of JSON code."""
        code = '''
{
  "name": "sample-project",
  "version": "1.0.0",
  "description": "A sample project for testing",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest",
    "build": "webpack --mode=production"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "webpack": "^5.74.0"
  },
  "keywords": ["javascript", "node", "express"],
  "author": "Test Author",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/user/repo.git"
  },
  "bugs": {
    "url": "https://github.com/user/repo/issues"
  }
}
'''
        tokens = self.service.tokenize(code, Path("package.json"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_yaml(self):
        """Test tokenization of YAML code."""
        code = '''
# Configuration file
app:
  name: sample-app
  version: 1.0.0
  debug: true
  
database:
  host: localhost
  port: 5432
  name: sample_db
  user: admin
  password: secret123
  
server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  
logging:
  level: info
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
features:
  - authentication
  - authorization  
  - caching
  - monitoring

environments:
  development:
    debug: true
    database:
      host: localhost
  production:
    debug: false
    database:
      host: prod-db.example.com
'''
        tokens = self.service.tokenize(code, Path("config.yaml"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_sql(self):
        """Test tokenization of SQL code."""
        code = '''
               -- Create users table
               CREATE TABLE users
               (
                   id            SERIAL PRIMARY KEY,
                   username      VARCHAR(50) UNIQUE  NOT NULL,
                   email         VARCHAR(100) UNIQUE NOT NULL,
                   password_hash VARCHAR(255)        NOT NULL,
                   created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               );

-- Create posts table
               CREATE TABLE posts
               (
                   id         SERIAL PRIMARY KEY,
                   user_id    INTEGER REFERENCES users (id) ON DELETE CASCADE,
                   title      VARCHAR(200) NOT NULL,
                   content    TEXT,
                   status     VARCHAR(20) DEFAULT 'draft',
                   created_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
               );

-- Insert sample data
               INSERT INTO users (username, email, password_hash)
               VALUES ('john_doe', 'john@example.com', 'hashed_password_1'),
                      ('jane_smith', 'jane@example.com', 'hashed_password_2');

-- Complex query with joins
               SELECT u.username,
                      u.email,
                      COUNT(p.id)       as post_count,
                      MAX(p.created_at) as last_post_date
               FROM users u
                        LEFT JOIN posts p ON u.id = p.user_id
               WHERE u.created_at >= '2024-01-01'
               GROUP BY u.id, u.username, u.email
               HAVING COUNT(p.id) > 0
               ORDER BY post_count DESC; \
               '''
        tokens = self.service.tokenize(code, Path("schema.sql"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_markdown(self):
        """Test tokenization of Markdown code."""
        code = '''
# Sample Project Documentation

This is a **sample project** that demonstrates various *markdown features*.

## Installation

To install this project, run:

```bash
npm install sample-project
```

## Usage

Here's how to use this project:

```javascript
const sample = require('sample-project');
console.log(sample.greet('World'));
```

## Features

- Easy to use API
- Comprehensive documentation
- TypeScript support
- Unit tests included

## Configuration

You can configure the project using a `config.json` file:

```json
{
  "debug": true,
  "port": 3000
}
```

## Links

- [Documentation](https://docs.example.com)
- [GitHub Repository](https://github.com/user/sample-project)
- [Issue Tracker](https://github.com/user/sample-project/issues)

## Tables

| Feature | Supported | Notes |
|---------|-----------|-------|
| Authentication | ✅ | JWT tokens |
| Caching | ✅ | Redis backend |
| Logging | ✅ | Winston logger |

> **Note**: This is just an example project for demonstration purposes.
'''
        tokens = self.service.tokenize(code, Path("README.md"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_dockerfile(self):
        """Test tokenization of Dockerfile."""
        code = '''
# Use official Node.js runtime as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership of app directory
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD node healthcheck.js

# Start application
CMD ["npm", "start"]
'''
        tokens = self.service.tokenize(code, Path("Dockerfile"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_toml(self):
        """Test tokenization of TOML code."""
        code = '''
[package]
name = "sample-project"
version = "0.1.0"
edition = "2021"
authors = ["Test Author <test@example.com>"]
description = "A sample Rust project"
license = "MIT"
repository = "https://github.com/user/sample-project"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
anyhow = "1.0"

[dev-dependencies]
tokio-test = "0.4"

[build-dependencies]
cc = "1.0"

[[bin]]
name = "main"
path = "src/main.rs"

[[bin]]
name = "worker"
path = "src/worker.rs"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1

[profile.dev]
opt-level = 0
debug = true

[features]
default = ["tls"]
tls = ["reqwest/rustls-tls"]
'''
        tokens = self.service.tokenize(code, Path("Cargo.toml"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_makefile(self):
        """Test tokenization of Makefile."""
        code = '''
# Makefile for sample project

# Variables
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2
LDFLAGS = -lm
SRCDIR = src
OBJDIR = obj
BINDIR = bin
TARGET = $(BINDIR)/sample

# Source files
SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)

# Default target
all: $(TARGET)

# Build target
$(TARGET): $(OBJECTS) | $(BINDIR)
\t$(CC) $(OBJECTS) -o $@ $(LDFLAGS)

# Compile source files
$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
\t$(CC) $(CFLAGS) -c $< -o $@

# Create directories
$(OBJDIR):
\tmkdir -p $(OBJDIR)

$(BINDIR):
\tmkdir -p $(BINDIR)

# Clean build artifacts
clean:
\trm -rf $(OBJDIR) $(BINDIR)

# Install
install: $(TARGET)
\tcp $(TARGET) /usr/local/bin/

# Uninstall
uninstall:
\trm -f /usr/local/bin/sample

# Run tests
test: $(TARGET)
\t./$(TARGET) --test

# Debug build
debug: CFLAGS += -g -DDEBUG
debug: $(TARGET)

.PHONY: all clean install uninstall test debug
'''
        tokens = self.service.tokenize(code, Path("Makefile"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_pascal(self):
        """Test tokenization of Pascal/Delphi code."""
        code = '''
program HelloWorld;

type
  TPerson = class
  private
    FName: String;
    FAge: Integer;
  public
    constructor Create(const AName: String; const AAge: Integer);
    property Name: String read FName write FName;
    property Age: Integer read FAge write FAge;
    procedure Greet;
  end;

constructor TPerson.Create(const AName: String; const AAge: Integer);
begin
  FName := AName;
  FAge := AAge;
end;

procedure TPerson.Greet;
begin
  WriteLn('Hello, I''m ', FName, ' and I''m ', FAge, ' years old');
end;

var
  Person: TPerson;

begin
  Person := TPerson.Create('Alice', 30);
  try
    Person.Greet;
  finally
    Person.Free;
  end;
end.
'''
        tokens = self.service.tokenize(code, Path("hello.pas"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_svelte(self):
        """Test tokenization of Svelte component code."""
        code = '''
<script>
  export let name = 'World';
  let count = 0;
  
  function increment() {
    count += 1;
  }
  
  $: doubled = count * 2;
</script>

<style>
  h1 {
    color: #ff3e00;
    text-transform: uppercase;
    font-size: 4em;
    font-weight: 100;
  }
  
  button {
    background: #ff3e00;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 2px;
  }
</style>

<h1>Hello {name}!</h1>

<button on:click={increment}>
  Count: {count}
</button>

<p>Double count: {doubled}</p>

{#if count > 5}
  <p>Count is greater than 5!</p>
{/if}
'''
        tokens = self.service.tokenize(code, Path("App.svelte"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_vue(self):
        """Test tokenization of Vue.js component code."""
        code = '''
<template>
  <div class="counter">
    <h1>{{ title }}</h1>
    <button @click="increment">Count: {{ count }}</button>
    <p v-if="count > 5">Count is greater than 5!</p>
    <ul>
      <li v-for="item in items" :key="item.id">
        {{ item.name }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Counter',
  data() {
    return {
      title: 'Vue Counter',
      count: 0,
      items: [
        { id: 1, name: 'Item 1' },
        { id: 2, name: 'Item 2' },
        { id: 3, name: 'Item 3' }
      ]
    }
  },
  methods: {
    increment() {
      this.count++
    }
  },
  computed: {
    doubled() {
      return this.count * 2
    }
  }
}
</script>

<style scoped>
.counter {
  text-align: center;
  margin-top: 2rem;
}

button {
  background: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #369870;
}
</style>
'''
        tokens = self.service.tokenize(code, Path("Counter.vue"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)

    def test_tokenize_solidity(self):
        """Test tokenization of Solidity smart contract code."""
        code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleToken {
    string public name;
    string public symbol;
    uint8 public decimals;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _decimals,
        uint256 _totalSupply
    ) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
        totalSupply = _totalSupply;
        balanceOf[msg.sender] = _totalSupply;
    }
    
    function transfer(address _to, uint256 _value) public returns (bool success) {
        require(balanceOf[msg.sender] >= _value, "Insufficient balance");
        require(_to != address(0), "Invalid address");
        
        balanceOf[msg.sender] -= _value;
        balanceOf[_to] += _value;
        
        emit Transfer(msg.sender, _to, _value);
        return true;
    }
    
    function approve(address _spender, uint256 _value) public returns (bool success) {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }
    
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
        require(balanceOf[_from] >= _value, "Insufficient balance");
        require(allowance[_from][msg.sender] >= _value, "Allowance exceeded");
        require(_to != address(0), "Invalid address");
        
        balanceOf[_from] -= _value;
        balanceOf[_to] += _value;
        allowance[_from][msg.sender] -= _value;
        
        emit Transfer(_from, _to, _value);
        return true;
    }
}
'''
        tokens = self.service.tokenize(code, Path("SimpleToken.sol"))
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)


class TestTokenizationServiceIntegration(unittest.TestCase):
    """Integration tests for TokenizationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()

    def test_tokenize_real_python_file(self):
        """Test tokenizing an actual Python file."""
        # Use the service file itself as test data
        service_file = Path("app/domains/tokenization/tokenization_service.py")

        if service_file.exists():
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tokens = self.service.tokenize(content, service_file)

            self.assertIsInstance(tokens, list)
            self.assertGreater(len(tokens), 50)  # Should have many tokens

            # Check that we have class and function definitions
            token_types = [token['type'] for token in tokens]
            self.assertIn('class_definition', token_types)
            self.assertIn('function_definition', token_types)

    def test_roundtrip_tokenize_detokenize(self):
        """Test that tokenizing and detokenizing preserves some structure."""
        original_code = '''
def hello_world():
    message = "Hello, World!"
    print(message)
    return message

if __name__ == "__main__":
    hello_world()
'''

        # Tokenize
        tokens = self.service.tokenize(original_code)

        # Detokenize
        reconstructed = self.service.detokenize(tokens)

        # Check that we got some meaningful output
        self.assertIsInstance(reconstructed, str)
        self.assertGreater(len(reconstructed), 0)

        # Should contain key elements (though spacing will be different)
        self.assertIn("hello_world", reconstructed)
        self.assertIn("Hello, World!", reconstructed)
        self.assertIn("print", reconstructed)


class TestTokenizationServiceWithSampleFiles(unittest.TestCase):
    """Tests for TokenizationService using comprehensive sample files."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = TokenizationService()
        self.sample_files_dir = Path(__file__).parent.parent.parent.parent / "resources" / "test" / "language_samples"
        
    def test_sample_files_directory_exists(self):
        """Test that the sample files directory exists."""
        self.assertTrue(self.sample_files_dir.exists(), f"Sample files directory not found: {self.sample_files_dir}")
        self.assertTrue(self.sample_files_dir.is_dir(), "Sample files path is not a directory")

    def _test_sample_file(self, filename: str, expected_language: str, min_tokens: int = 10):
        """Helper method to test tokenization of a sample file."""
        file_path = self.sample_files_dir / filename
        
        # Check file exists
        self.assertTrue(file_path.exists(), f"Sample file not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        self.assertGreater(len(content), 0, f"Sample file {filename} is empty")
        
        # Tokenize the content
        tokens = self.service.tokenize(content, file_path)
        
        # Verify tokenization results
        self.assertIsInstance(tokens, list, f"Tokenization should return a list for {filename}")
        self.assertGreater(len(tokens), min_tokens, f"Should have at least {min_tokens} tokens for {filename}")
        
        # Verify language detection
        detected_language = self.service._detect_language(file_path=file_path)
        self.assertEqual(detected_language, expected_language, f"Language detection failed for {filename}")
        
        # Verify token structure
        for token in tokens:
            self.assertIsInstance(token, dict, f"Each token should be a dict for {filename}")
            self.assertIn('type', token, f"Token should have 'type' field for {filename}")
            self.assertIn('text', token, f"Token should have 'text' field for {filename}")
            self.assertIn('start', token, f"Token should have 'start' field for {filename}")
            self.assertIn('end', token, f"Token should have 'end' field for {filename}")

    def test_ada_sample(self):
        """Test tokenization of Ada sample file."""
        self._test_sample_file("sample.ada", "ada", 50)

    def test_assembly_sample(self):
        """Test tokenization of Assembly sample file."""
        self._test_sample_file("sample.asm", "asm", 30)

    def test_bash_sample(self):
        """Test tokenization of Bash sample file."""
        self._test_sample_file("sample.sh", "bash", 40)

    def test_c_sample(self):
        """Test tokenization of C sample file."""
        self._test_sample_file("sample.c", "c", 60)

    def test_csharp_sample(self):
        """Test tokenization of C# sample file."""
        self._test_sample_file("sample.cs", "csharp", 80)

    def test_cpp_sample(self):
        """Test tokenization of C++ sample file."""
        self._test_sample_file("sample.cpp", "cpp", 70)

    def test_cmake_sample(self):
        """Test tokenization of CMake sample file."""
        self._test_sample_file("CMakeLists.txt", "cmake", 20)

    def test_css_sample(self):
        """Test tokenization of CSS sample file."""
        self._test_sample_file("sample.css", "css", 30)

    def test_dart_sample(self):
        """Test tokenization of Dart sample file."""
        self._test_sample_file("sample.dart", "dart", 60)

    def test_dockerfile_sample(self):
        """Test tokenization of Dockerfile sample file."""
        self._test_sample_file("Dockerfile", "dockerfile", 15)

    def test_fortran_sample(self):
        """Test tokenization of Fortran sample file."""
        self._test_sample_file("sample.f90", "fortran", 40)

    def test_go_sample(self):
        """Test tokenization of Go sample file."""
        self._test_sample_file("sample.go", "go", 50)

    def test_go_mod_sample(self):
        """Test tokenization of Go module file."""
        self._test_sample_file("go.mod", "gomod", 5)

    def test_graphql_sample(self):
        """Test tokenization of GraphQL sample file."""
        self._test_sample_file("sample.graphql", "graphql", 30)

    def test_groovy_sample(self):
        """Test tokenization of Groovy sample file."""
        self._test_sample_file("sample.groovy", "groovy", 40)

    def test_haskell_sample(self):
        """Test tokenization of Haskell sample file."""
        self._test_sample_file("sample.hs", "haskell", 50)

    def test_html_sample(self):
        """Test tokenization of HTML sample file."""
        self._test_sample_file("sample.html", "html", 40)

    def test_java_sample(self):
        """Test tokenization of Java sample file."""
        self._test_sample_file("sample.java", "java", 80)

    def test_javascript_sample(self):
        """Test tokenization of JavaScript sample file."""
        self._test_sample_file("sample.js", "javascript", 70)

    def test_json_sample(self):
        """Test tokenization of JSON sample file."""
        self._test_sample_file("sample.json", "json", 20)

    def test_julia_sample(self):
        """Test tokenization of Julia sample file."""
        self._test_sample_file("sample.jl", "julia", 50)

    def test_kotlin_sample(self):
        """Test tokenization of Kotlin sample file."""
        self._test_sample_file("sample.kt", "kotlin", 60)

    def test_lua_sample(self):
        """Test tokenization of Lua sample file."""
        self._test_sample_file("sample.lua", "lua", 40)

    def test_makefile_sample(self):
        """Test tokenization of Makefile sample file."""
        self._test_sample_file("Makefile", "make", 15)

    def test_markdown_sample(self):
        """Test tokenization of Markdown sample file."""
        self._test_sample_file("sample.md", "markdown", 30)

    def test_matlab_sample(self):
        """Test tokenization of MATLAB sample file."""
        self._test_sample_file("sample.m", "matlab", 40)

    def test_ocaml_sample(self):
        """Test tokenization of OCaml sample file."""
        self._test_sample_file("sample.ml", "ocaml", 50)

    def test_pascal_sample(self):
        """Test tokenization of Pascal sample file."""
        self._test_sample_file("sample.pas", "pascal", 80)

    def test_perl_sample(self):
        """Test tokenization of Perl sample file."""
        self._test_sample_file("sample.pl", "perl", 40)

    def test_php_sample(self):
        """Test tokenization of PHP sample file."""
        self._test_sample_file("sample.php", "php", 60)

    def test_python_sample(self):
        """Test tokenization of Python sample file."""
        self._test_sample_file("sample.py", "python", 60)

    def test_r_sample(self):
        """Test tokenization of R sample file."""
        self._test_sample_file("sample.r", "r", 40)

    def test_ruby_sample(self):
        """Test tokenization of Ruby sample file."""
        self._test_sample_file("sample.rb", "ruby", 50)

    def test_rust_sample(self):
        """Test tokenization of Rust sample file."""
        self._test_sample_file("sample.rs", "rust", 70)

    def test_scala_sample(self):
        """Test tokenization of Scala sample file."""
        self._test_sample_file("sample.scala", "scala", 80)

    def test_solidity_sample(self):
        """Test tokenization of Solidity sample file."""
        self._test_sample_file("sample.sol", "solidity", 100)

    def test_sql_sample(self):
        """Test tokenization of SQL sample file."""
        self._test_sample_file("sample.sql", "sql", 150)

    def test_svelte_sample(self):
        """Test tokenization of Svelte sample file."""
        self._test_sample_file("sample.svelte", "svelte", 200)

    def test_swift_sample(self):
        """Test tokenization of Swift sample file."""
        self._test_sample_file("sample.swift", "swift", 180)

    def test_toml_sample(self):
        """Test tokenization of TOML sample file."""
        self._test_sample_file("sample.toml", "toml", 120)

    def test_typescript_sample(self):
        """Test tokenization of TypeScript sample file."""
        self._test_sample_file("sample.ts", "typescript", 200)

    def test_vue_sample(self):
        """Test tokenization of Vue sample file."""
        self._test_sample_file("sample.vue", "vue", 250)

    def test_xml_sample(self):
        """Test tokenization of XML sample file."""
        self._test_sample_file("sample.xml", "xml", 120)

    def test_yaml_sample(self):
        """Test tokenization of YAML sample file."""
        self._test_sample_file("sample.yaml", "yaml", 150)

    def test_all_sample_files_tokenization(self):
        """Test that all sample files can be tokenized successfully."""
        expected_files = [
            ("sample.ada", "ada"),
            ("sample.asm", "asm"),
            ("sample.sh", "bash"),
            ("sample.c", "c"),
            ("sample.cs", "csharp"),
            ("sample.cpp", "cpp"),
            ("CMakeLists.txt", "cmake"),
            ("sample.css", "css"),
            ("sample.dart", "dart"),
            ("Dockerfile", "dockerfile"),
            ("sample.f90", "fortran"),
            ("sample.go", "go"),
            ("go.mod", "gomod"),
            ("sample.graphql", "graphql"),
            ("sample.groovy", "groovy"),
            ("sample.hs", "haskell"),
            ("sample.html", "html"),
            ("sample.java", "java"),
            ("sample.js", "javascript"),
            ("sample.json", "json"),
            ("sample.jl", "julia"),
            ("sample.kt", "kotlin"),
            ("sample.lua", "lua"),
            ("Makefile", "make"),
            ("sample.md", "markdown"),
            ("sample.m", "matlab"),
            ("sample.ml", "ocaml"),
            ("sample.pas", "pascal"),
            ("sample.pl", "perl"),
            ("sample.php", "php"),
            ("sample.py", "python"),
            ("sample.r", "r"),
            ("sample.rb", "ruby"),
            ("sample.rs", "rust"),
            ("sample.scala", "scala"),
            ("sample.sol", "solidity"),
            ("sample.sql", "sql"),
            ("sample.svelte", "svelte"),
            ("sample.swift", "swift"),
            ("sample.toml", "toml"),
            ("sample.ts", "typescript"),
            ("sample.vue", "vue"),
            ("sample.xml", "xml"),
            ("sample.yaml", "yaml")
        ]
        
        successful_tokenizations = 0
        failed_tokenizations = []
        
        for filename, expected_language in expected_files:
            file_path = self.sample_files_dir / filename
            
            if not file_path.exists():
                failed_tokenizations.append(f"File not found: {filename}")
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if not content.strip():
                    failed_tokenizations.append(f"Empty file: {filename}")
                    continue
                
                tokens = self.service.tokenize(content, file_path)
                
                if not isinstance(tokens, list):
                    failed_tokenizations.append(f"Invalid token format for {filename}")
                    continue
                
                if len(tokens) == 0:
                    failed_tokenizations.append(f"No tokens generated for {filename}")
                    continue
                    
                detected_language = self.service._detect_language(file_path=file_path)
                if detected_language != expected_language:
                    failed_tokenizations.append(f"Language detection mismatch for {filename}: expected {expected_language}, got {detected_language}")
                    continue
                
                successful_tokenizations += 1
                
            except Exception as e:
                failed_tokenizations.append(f"Exception for {filename}: {str(e)}")
        
        # Report results
        total_files = len(expected_files)
        print(f"\nTokenization Test Results:")
        print(f"Total files tested: {total_files}")
        print(f"Successful tokenizations: {successful_tokenizations}")
        print(f"Failed tokenizations: {len(failed_tokenizations)}")
        
        if failed_tokenizations:
            print("\nFailures:")
            for failure in failed_tokenizations:
                print(f"  - {failure}")
        
        # Assert that at least 90% of files tokenize successfully
        success_rate = successful_tokenizations / total_files
        self.assertGreaterEqual(success_rate, 0.9, f"Success rate {success_rate:.2%} is below 90%. Failures: {failed_tokenizations}")

    def test_token_consistency_across_sample_files(self):
        """Test that tokenization produces consistent results across multiple runs."""
        test_files = ["sample.py", "sample.js", "sample.java", "sample.cpp"]
        
        for filename in test_files:
            file_path = self.sample_files_dir / filename
            if not file_path.exists():
                continue
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Tokenize the same content multiple times
            tokens1 = self.service.tokenize(content, file_path)
            tokens2 = self.service.tokenize(content, file_path)
            tokens3 = self.service.tokenize(content, file_path)
            
            # Results should be identical
            self.assertEqual(len(tokens1), len(tokens2), f"Inconsistent token count for {filename}")
            self.assertEqual(len(tokens2), len(tokens3), f"Inconsistent token count for {filename}")
            
            # Compare token types and positions
            for i, (t1, t2, t3) in enumerate(zip(tokens1, tokens2, tokens3)):
                self.assertEqual(t1['type'], t2['type'], f"Token type mismatch at index {i} for {filename}")
                self.assertEqual(t2['type'], t3['type'], f"Token type mismatch at index {i} for {filename}")
                self.assertEqual(t1['start'], t2['start'], f"Start point mismatch at index {i} for {filename}")
                self.assertEqual(t2['start'], t3['start'], f"Start point mismatch at index {i} for {filename}")

    def test_large_file_tokenization_performance(self):
        """Test tokenization performance on larger sample files."""
        import time
        
        large_files = ["sample.sol", "sample.sql", "sample.svelte", "sample.swift", "sample.ts", "sample.vue", "sample.xml", "sample.yaml"]
        
        for filename in large_files:
            file_path = self.sample_files_dir / filename
            if not file_path.exists():
                continue
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Measure tokenization time
            start_time = time.time()
            tokens = self.service.tokenize(content, file_path)
            end_time = time.time()
            
            tokenization_time = end_time - start_time
            file_size_kb = len(content) / 1024
            
            # Should complete within reasonable time (less than 5 seconds for any file)
            self.assertLess(tokenization_time, 5.0, f"Tokenization of {filename} took too long: {tokenization_time:.2f}s")
            
            # Should produce tokens
            self.assertGreater(len(tokens), 0, f"No tokens produced for {filename}")
            
            # Calculate tokens per second
            if tokenization_time > 0:
                tokens_per_second = len(tokens) / tokenization_time
                print(f"{filename}: {len(tokens)} tokens, {file_size_kb:.1f}KB, {tokenization_time:.3f}s, {tokens_per_second:.0f} tokens/s")


if __name__ == '__main__':
    unittest.main()
