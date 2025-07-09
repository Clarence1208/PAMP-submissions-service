#!/usr/bin/env ruby

# Sample Ruby program

# Person class
class Person
  attr_reader :name, :age, :email
  
  def initialize(name, age, email = nil)
    @name = name
    @age = age
    @email = email
  end
  
  def greet
    "Hello, #{@name}! You are #{@age} years old."
  end
  
  def adult?
    @age >= 18
  end
  
  def to_h
    { name: @name, age: @age, email: @email }
  end
  
  def to_s
    "Person(#{@name}, #{@age})"
  end
end

# Module with utility methods
module Statistics
  def self.calculate(numbers)
    {
      sum: numbers.sum,
      mean: numbers.sum.to_f / numbers.length,
      min: numbers.min,
      max: numbers.max,
      median: median(numbers)
    }
  end
  
  private
  
  def self.median(numbers)
    sorted = numbers.sort
    len = sorted.length
    len.odd? ? sorted[len / 2] : (sorted[len / 2 - 1] + sorted[len / 2]) / 2.0
  end
end

# Fibonacci with memoization
class Fibonacci
  def initialize
    @memo = { 0 => 0, 1 => 1 }
  end
  
  def calculate(n)
    return @memo[n] if @memo.key?(n)
    @memo[n] = calculate(n - 1) + calculate(n - 2)
  end
end

# Main execution
def main
  puts "Ruby Programming Example"
  
  # Create people
  people = [
    Person.new("Alice", 30, "alice@example.com"),
    Person.new("Bob", 17, "bob@example.com"),
    Person.new("Charlie", 35, "charlie@example.com"),
    Person.new("Diana", 25, "diana@example.com")
  ]
  
  puts "\nAll people:"
  people.each { |person| puts person.greet }
  
  # Filter adults
  adults = people.select(&:adult?)
  puts "\nAdults:"
  adults.each { |adult| puts "- #{adult.name}" }
  
  # Map operations
  names = people.map(&:name)
  ages = people.map(&:age)
  
  puts "\nNames: #{names.join(', ')}"
  puts "Ages: #{ages.join(', ')}"
  
  # Array operations
  numbers = (1..10).to_a
  squares = numbers.map { |n| n**2 }
  evens = numbers.select(&:even?)
  
  puts "\nNumbers: #{numbers.join(', ')}"
  puts "Squares: #{squares.join(', ')}"
  puts "Even numbers: #{evens.join(', ')}"
  
  # Statistics
  stats = Statistics.calculate(ages)
  puts "\nAge statistics:"
  stats.each { |key, value| puts "  #{key}: #{value.round(2)}" }
  
  # Hash operations
  scores = { "Alice" => 95, "Bob" => 87, "Charlie" => 92, "Diana" => 89 }
  puts "\nScores:"
  scores.each { |name, score| puts "  #{name}: #{score}" }
  
  high_scorers = scores.select { |name, score| score >= 90 }
  puts "High scorers: #{high_scorers.keys.join(', ')}"
  
  # Block examples
  puts "\nBlock examples:"
  3.times { |i| puts "Iteration #{i + 1}" }
  
  # Range operations
  puts "\nRange operations:"
  (1..5).each { |n| print "#{n} " }
  puts
  
  letters = ('a'..'e').to_a
  puts "Letters: #{letters.join(', ')}"
  
  # String operations
  text = "  Hello Ruby World  "
  puts "\nString operations:"
  puts "Original: '#{text}'"
  puts "Stripped: '#{text.strip}'"
  puts "Upcase: '#{text.strip.upcase}'"
  puts "Downcase: '#{text.strip.downcase}'"
  puts "Words: #{text.strip.split.inspect}"
  
  # Fibonacci sequence
  fib = Fibonacci.new
  fib_sequence = (0..9).map { |i| fib.calculate(i) }
  puts "\nFibonacci sequence: #{fib_sequence.join(', ')}"
  
  # Regular expressions
  emails = ["alice@example.com", "invalid-email", "bob@test.org"]
  email_regex = /\A[\w+\-.]+@[a-z\d\-]+(\.[a-z\d\-]+)*\.[a-z]+\z/i
  
  puts "\nEmail validation:"
  emails.each do |email|
    valid = email.match?(email_regex)
    puts "  #{email}: #{valid ? '✓ valid' : '✗ invalid'}"
  end
  
  # Symbol usage
  person_data = {
    name: "Test Person",
    age: 25,
    active: true
  }
  
  puts "\nSymbol hash:"
  person_data.each { |key, value| puts "  #{key}: #{value}" }
  
  # Case statement
  priority = :high
  message = case priority
            when :low then "Can wait"
            when :medium then "Should do soon"
            when :high then "Important"
            when :urgent then "Drop everything!"
            else "Unknown priority"
            end
  
  puts "\nPriority message: #{message}"
  
  # Exception handling
  begin
    result = 10 / 0
  rescue ZeroDivisionError => e
    puts "\nCaught exception: #{e.message}"
  rescue => e
    puts "\nCaught general exception: #{e.message}"
  ensure
    puts "Cleanup code executed"
  end
  
  puts "\nProgram completed successfully!"
end

# Run main if this file is executed directly
main if __FILE__ == $0 