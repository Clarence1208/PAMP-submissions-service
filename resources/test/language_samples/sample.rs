// Sample Rust program

use std::collections::HashMap;

// Struct definition
#[derive(Debug, Clone)]
struct Person {
    name: String,
    age: u32,
    email: Option<String>,
}

impl Person {
    fn new(name: String, age: u32, email: Option<String>) -> Self {
        Person { name, age, email }
    }
    
    fn greet(&self) -> String {
        format!("Hello, {}! You are {} years old.", self.name, self.age)
    }
    
    fn is_adult(&self) -> bool {
        self.age >= 18
    }
}

// Enum definition
#[derive(Debug, PartialEq)]
enum Priority {
    Low,
    Medium,
    High,
    Urgent,
}

impl Priority {
    fn level(&self) -> u8 {
        match self {
            Priority::Low => 1,
            Priority::Medium => 2,
            Priority::High => 3,
            Priority::Urgent => 4,
        }
    }
}

// Result type for error handling
#[derive(Debug)]
enum MathError {
    DivisionByZero,
}

fn safe_divide(a: f64, b: f64) -> Result<f64, MathError> {
    if b == 0.0 {
        Err(MathError::DivisionByZero)
    } else {
        Ok(a / b)
    }
}

// Generic function
fn find_max<T: PartialOrd + Clone>(items: &[T]) -> Option<T> {
    if items.is_empty() {
        None
    } else {
        Some(items.iter().max().unwrap().clone())
    }
}

// Trait definition
trait Summarizable {
    fn summarize(&self) -> String;
}

impl Summarizable for Person {
    fn summarize(&self) -> String {
        match &self.email {
            Some(email) => format!("{} ({}, {})", self.name, self.age, email),
            None => format!("{} ({})", self.name, self.age),
        }
    }
}

// Function with lifetimes
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Fibonacci with memoization
fn fibonacci(n: u32, memo: &mut HashMap<u32, u64>) -> u64 {
    if let Some(&value) = memo.get(&n) {
        return value;
    }
    
    let result = match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1, memo) + fibonacci(n - 2, memo),
    };
    
    memo.insert(n, result);
    result
}

fn main() {
    println!("Rust Programming Example");
    
    // Create people
    let people = vec![
        Person::new("Alice".to_string(), 30, Some("alice@example.com".to_string())),
        Person::new("Bob".to_string(), 17, Some("bob@example.com".to_string())),
        Person::new("Charlie".to_string(), 35, Some("charlie@example.com".to_string())),
        Person::new("Diana".to_string(), 25, None),
    ];
    
    println!("\nAll people:");
    for person in &people {
        println!("{}", person.greet());
    }
    
    // Filter adults using iterator
    let adults: Vec<&Person> = people.iter()
        .filter(|person| person.is_adult())
        .collect();
    
    println!("\nAdults:");
    for adult in &adults {
        println!("- {}", adult.name);
    }
    
    // Map operations
    let names: Vec<&String> = people.iter().map(|p| &p.name).collect();
    let ages: Vec<u32> = people.iter().map(|p| p.age).collect();
    
    println!("\nNames: {}", names.join(", "));
    println!("Ages: {:?}", ages);
    
    // Vector operations
    let numbers: Vec<i32> = (1..=10).collect();
    let squares: Vec<i32> = numbers.iter().map(|&n| n * n).collect();
    let evens: Vec<&i32> = numbers.iter().filter(|&&n| n % 2 == 0).collect();
    
    println!("\nNumbers: {:?}", numbers);
    println!("Squares: {:?}", squares);
    println!("Evens: {:?}", evens);
    
    // Statistics
    let sum: i32 = numbers.iter().sum();
    let max = find_max(&numbers);
    println!("\nSum: {}, Max: {:?}", sum, max);
    
    // HashMap operations
    let mut scores = HashMap::new();
    scores.insert("Alice", 95);
    scores.insert("Bob", 87);
    scores.insert("Charlie", 92);
    
    println!("\nScores:");
    for (name, score) in &scores {
        println!("  {}: {}", name, score);
    }
    
    // Error handling with Result
    println!("\nSafe division:");
    match safe_divide(10.0, 2.0) {
        Ok(result) => println!("10 / 2 = {}", result),
        Err(e) => println!("Error: {:?}", e),
    }
    
    match safe_divide(10.0, 0.0) {
        Ok(result) => println!("10 / 0 = {}", result),
        Err(e) => println!("Error: {:?}", e),
    }
    
    // Option handling
    println!("\nEmail handling:");
    for person in &people {
        match &person.email {
            Some(email) => println!("{} has email: {}", person.name, email),
            None => println!("{} has no email", person.name),
        }
    }
    
    // Pattern matching with enum
    let priorities = vec![Priority::Low, Priority::High, Priority::Medium, Priority::Urgent];
    println!("\nPriorities:");
    for priority in &priorities {
        let message = match priority {
            Priority::Low => "Can wait",
            Priority::Medium => "Should do soon",
            Priority::High => "Important",
            Priority::Urgent => "Drop everything!",
        };
        println!("  {:?} (level {}): {}", priority, priority.level(), message);
    }
    
    // Trait usage
    println!("\nSummaries:");
    for person in &people {
        println!("  {}", person.summarize());
    }
    
    // Lifetime example
    let str1 = "hello";
    let str2 = "world!";
    let longer = longest(str1, str2);
    println!("\nLongest string: {}", longer);
    
    // Fibonacci with memoization
    let mut memo = HashMap::new();
    let fib_numbers: Vec<u64> = (0..10).map(|i| fibonacci(i, &mut memo)).collect();
    println!("\nFibonacci sequence: {:?}", fib_numbers);
    
    // String operations
    let text = "  Hello Rust World  ";
    println!("\nString operations:");
    println!("Original: '{}'", text);
    println!("Trimmed: '{}'", text.trim());
    println!("Uppercase: '{}'", text.trim().to_uppercase());
    println!("Words: {:?}", text.trim().split_whitespace().collect::<Vec<&str>>());
    
    // Ownership and borrowing
    let mut numbers_mut = vec![1, 2, 3, 4, 5];
    println!("\nMutable operations:");
    println!("Before: {:?}", numbers_mut);
    numbers_mut.push(6);
    numbers_mut[0] = 10;
    println!("After: {:?}", numbers_mut);
    
    println!("\nProgram completed successfully!");
} 