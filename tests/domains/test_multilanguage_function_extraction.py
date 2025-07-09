"""
Tests for multi-language function extraction using Tree-sitter queries.
Tests function extraction across Python, JavaScript, Java, C++, Go, Rust, and other languages.
"""
from pathlib import Path

import pytest

from app.domains.tokenization.tokenization_service import TokenizationService


class TestMultiLanguageFunctionExtraction:
    """Test function extraction across different programming languages"""
    
    @pytest.fixture
    def tokenization_service(self):
        """Create a tokenization service instance"""
        return TokenizationService()
    
    def test_python_function_extraction(self, tokenization_service):
        """Test function extraction from Python code"""
        python_code = '''
def calculate_area(radius):
    """Calculate the area of a circle"""
    return 3.14159 * radius * radius

def calculate_perimeter(radius):
    return 2 * 3.14159 * radius

class Circle:
    def __init__(self, radius):
        self.radius = radius
    
    def get_area(self):
        return calculate_area(self.radius)
    
    def get_perimeter(self):
        return calculate_perimeter(self.radius)

def main():
    circle = Circle(5)
    print(f"Area: {circle.get_area()}")
    print(f"Perimeter: {circle.get_perimeter()}")
'''
        
        file_path = Path("test.py")
        functions = tokenization_service.extract_functions_with_positions(python_code, file_path)
        
        # Should extract at least the main functions
        assert len(functions) >= 3
        
        # Check that we found the main functions
        function_names = [func_data['function_name'] for func_data in functions.values()]
        assert 'calculate_area' in function_names
        assert 'calculate_perimeter' in function_names
        assert 'main' in function_names
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'python'
    
    def test_javascript_function_extraction(self, tokenization_service):
        """Test function extraction from JavaScript code"""
        javascript_code = '''
function calculateArea(radius) {
    return Math.PI * radius * radius;
}

const calculatePerimeter = (radius) => {
    return 2 * Math.PI * radius;
}

class Circle {
    constructor(radius) {
        this.radius = radius;
    }
    
    getArea() {
        return calculateArea(this.radius);
    }
    
    getPerimeter() {
        return calculatePerimeter(this.radius);
    }
}

function main() {
    const circle = new Circle(5);
    console.log(`Area: ${circle.getArea()}`);
    console.log(`Perimeter: ${circle.getPerimeter()}`);
}
'''
        
        file_path = Path("test.js")
        functions = tokenization_service.extract_functions_with_positions(javascript_code, file_path)
        
        # Should extract functions and methods
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'javascript'
    
    def test_java_function_extraction(self, tokenization_service):
        """Test function extraction from Java code"""
        java_code = '''
public class Circle {
    private double radius;
    
    public Circle(double radius) {
        this.radius = radius;
    }
    
    public double calculateArea() {
        return Math.PI * radius * radius;
    }
    
    public double calculatePerimeter() {
        return 2 * Math.PI * radius;
    }
    
    public static void main(String[] args) {
        Circle circle = new Circle(5.0);
        System.out.println("Area: " + circle.calculateArea());
        System.out.println("Perimeter: " + circle.calculatePerimeter());
    }
}
'''
        
        file_path = Path("Circle.java")
        functions = tokenization_service.extract_functions_with_positions(java_code, file_path)
        
        # Should extract methods and constructor
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'java'
    
    def test_cpp_function_extraction(self, tokenization_service):
        """Test function extraction from C++ code"""
        cpp_code = '''
#include <iostream>
#include <cmath>

double calculateArea(double radius) {
    return M_PI * radius * radius;
}

double calculatePerimeter(double radius) {
    return 2 * M_PI * radius;
}

class Circle {
private:
    double radius;
    
public:
    Circle(double r) : radius(r) {}
    
    double getArea() {
        return calculateArea(radius);
    }
    
    double getPerimeter() {
        return calculatePerimeter(radius);
    }
};

int main() {
    Circle circle(5.0);
    std::cout << "Area: " << circle.getArea() << std::endl;
    std::cout << "Perimeter: " << circle.getPerimeter() << std::endl;
    return 0;
}
'''
        
        file_path = Path("circle.cpp")
        functions = tokenization_service.extract_functions_with_positions(cpp_code, file_path)
        
        # Should extract functions
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'cpp'
    
    def test_go_function_extraction(self, tokenization_service):
        """Test function extraction from Go code"""
        go_code = '''
package main

import (
    "fmt"
    "math"
)

func calculateArea(radius float64) float64 {
    return math.Pi * radius * radius
}

func calculatePerimeter(radius float64) float64 {
    return 2 * math.Pi * radius
}

type Circle struct {
    radius float64
}

func (c Circle) getArea() float64 {
    return calculateArea(c.radius)
}

func (c Circle) getPerimeter() float64 {
    return calculatePerimeter(c.radius)
}

func main() {
    circle := Circle{radius: 5.0}
    fmt.Printf("Area: %.2f\\n", circle.getArea())
    fmt.Printf("Perimeter: %.2f\\n", circle.getPerimeter())
}
'''
        
        file_path = Path("circle.go")
        functions = tokenization_service.extract_functions_with_positions(go_code, file_path)
        
        # Should extract functions and methods
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'go'
    
    def test_rust_function_extraction(self, tokenization_service):
        """Test function extraction from Rust code"""
        rust_code = '''
use std::f64::consts::PI;

fn calculate_area(radius: f64) -> f64 {
    PI * radius * radius
}

fn calculate_perimeter(radius: f64) -> f64 {
    2.0 * PI * radius
}

struct Circle {
    radius: f64,
}

impl Circle {
    fn new(radius: f64) -> Circle {
        Circle { radius }
    }
    
    fn get_area(&self) -> f64 {
        calculate_area(self.radius)
    }
    
    fn get_perimeter(&self) -> f64 {
        calculate_perimeter(self.radius)
    }
}

fn main() {
    let circle = Circle::new(5.0);
    println!("Area: {:.2}", circle.get_area());
    println!("Perimeter: {:.2}", circle.get_perimeter());
}
'''
        
        file_path = Path("circle.rs")
        functions = tokenization_service.extract_functions_with_positions(rust_code, file_path)
        
        # Should extract functions
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'rust'
    
    def test_php_function_extraction(self, tokenization_service):
        """Test function extraction from PHP code"""
        php_code = '''
<?php

function calculateArea($radius) {
    return pi() * $radius * $radius;
}

function calculatePerimeter($radius) {
    return 2 * pi() * $radius;
}

class Circle {
    private $radius;
    
    public function __construct($radius) {
        $this->radius = $radius;
    }
    
    public function getArea() {
        return calculateArea($this->radius);
    }
    
    public function getPerimeter() {
        return calculatePerimeter($this->radius);
    }
}

function main() {
    $circle = new Circle(5.0);
    echo "Area: " . $circle->getArea() . "\\n";
    echo "Perimeter: " . $circle->getPerimeter() . "\\n";
}

main();
?>
'''
        
        file_path = Path("circle.php")
        functions = tokenization_service.extract_functions_with_positions(php_code, file_path)
        
        # Should extract functions and methods
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'php'
    
    def test_ruby_function_extraction(self, tokenization_service):
        """Test function extraction from Ruby code"""
        ruby_code = '''
def calculate_area(radius)
  Math::PI * radius * radius
end

def calculate_perimeter(radius)
  2 * Math::PI * radius
end

class Circle
  def initialize(radius)
    @radius = radius
  end
  
  def get_area
    calculate_area(@radius)
  end
  
  def get_perimeter
    calculate_perimeter(@radius)
  end
end

def main
  circle = Circle.new(5.0)
  puts "Area: #{circle.get_area}"
  puts "Perimeter: #{circle.get_perimeter}"
end

main
'''
        
        file_path = Path("circle.rb")
        functions = tokenization_service.extract_functions_with_positions(ruby_code, file_path)
        
        # Should extract functions and methods
        assert len(functions) >= 2
        
        # Check function data structure
        for func_id, func_data in functions.items():
            assert 'function_name' in func_data
            assert 'start_line' in func_data
            assert 'end_line' in func_data
            assert 'code_block' in func_data
            assert 'language' in func_data
            assert func_data['language'] == 'ruby'
    
    def test_fallback_mechanism(self, tokenization_service):
        """Test that fallback mechanism works when queries fail"""
        # Test with a language that might not have perfect queries
        code = '''
        function testFunction() {
            console.log("test");
        }
        '''
        
        file_path = Path("test.js")
        functions = tokenization_service.extract_functions_with_positions(code, file_path)
        
        # Should still extract something using fallback
        assert isinstance(functions, dict)
    
    def test_empty_code(self, tokenization_service):
        """Test behavior with empty code"""
        empty_code = ""
        file_path = Path("empty.py")
        
        functions = tokenization_service.extract_functions_with_positions(empty_code, file_path)
        
        assert functions == {}
    
    def test_code_without_functions(self, tokenization_service):
        """Test behavior with code that has no functions"""
        code = '''
x = 5
y = 10
result = x + y
print(result)
'''
        
        file_path = Path("no_functions.py")
        functions = tokenization_service.extract_functions_with_positions(code, file_path)
        
        assert functions == {}
    
    def test_similarity_detection_with_extracted_functions(self, tokenization_service):
        """Test that extracted functions work with similarity detection"""
        python_code1 = '''
def add_numbers(a, b):
    return a + b

def multiply_numbers(a, b):
    return a * b
'''
        
        python_code2 = '''
def sum_values(x, y):
    return x + y

def product_values(x, y):
    return x * y
'''
        
        file_path1 = Path("math1.py")
        file_path2 = Path("math2.py")
        
        functions1 = tokenization_service.extract_functions_with_positions(python_code1, file_path1)
        functions2 = tokenization_service.extract_functions_with_positions(python_code2, file_path2)
        
        # Both should extract 2 functions
        assert len(functions1) == 2
        assert len(functions2) == 2
        
        # Test that we can compare function similarity
        from app.domains.detection.similarity_detection_service import SimilarityDetectionService
        similarity_service = SimilarityDetectionService()
        
        shared_blocks = similarity_service.detect_shared_code_blocks(
            source1=python_code1,
            source2=python_code2,
            file1_name="math1.py",
            file2_name="math2.py",
            file1_path=file_path1,
            file2_path=file_path2,
            tokenization_service=tokenization_service
        )
        
        # Should detect shared blocks (similar functions)
        assert 'shared_blocks' in shared_blocks
        assert 'total_shared_blocks' in shared_blocks
        assert shared_blocks['functions_file1'] == 2
        assert shared_blocks['functions_file2'] == 2 