<?php
// Sample PHP program

declare(strict_types=1);

// Person class with modern PHP features
class Person {
    public function __construct(
        private string $name,
        private int $age,
        private ?string $email = null
    ) {}
    
    public function greet(): string {
        return "Hello, {$this->name}! You are {$this->age} years old.";
    }
    
    public function isAdult(): bool {
        return $this->age >= 18;
    }
    
    public function getName(): string { return $this->name; }
    public function getAge(): int { return $this->age; }
    public function getEmail(): ?string { return $this->email; }
}

// Enum (PHP 8.1+)
enum Priority: int {
    case LOW = 1;
    case MEDIUM = 2;
    case HIGH = 3;
    case URGENT = 4;
    
    public function label(): string {
        return match($this) {
            Priority::LOW => 'Low',
            Priority::MEDIUM => 'Medium',
            Priority::HIGH => 'High',
            Priority::URGENT => 'Urgent',
        };
    }
}

// Functions
function filterAdults(array $people): array {
    return array_filter($people, fn($person) => $person->isAdult());
}

function mapNames(array $people): array {
    return array_map(fn($person) => $person->getName(), $people);
}

function calculateStats(array $numbers): array {
    return [
        'sum' => array_sum($numbers),
        'average' => array_sum($numbers) / count($numbers),
        'min' => min($numbers),
        'max' => max($numbers)
    ];
}

// Main execution
function main(): void {
    echo "PHP Programming Example\n\n";
    
    // Create people
    $people = [
        new Person('Alice', 30, 'alice@example.com'),
        new Person('Bob', 17, 'bob@example.com'),
        new Person('Charlie', 35, 'charlie@example.com'),
        new Person('Diana', 25, 'diana@example.com'),
    ];
    
    echo "All people:\n";
    foreach ($people as $person) {
        echo $person->greet() . "\n";
    }
    
    // Filter adults
    $adults = filterAdults($people);
    echo "\nAdults:\n";
    foreach ($adults as $adult) {
        echo "- {$adult->getName()}\n";
    }
    
    // Array operations
    $numbers = range(1, 10);
    $squares = array_map(fn($n) => $n ** 2, $numbers);
    $evenNumbers = array_filter($numbers, fn($n) => $n % 2 === 0);
    
    echo "\nNumbers: " . implode(', ', $numbers) . "\n";
    echo "Squares: " . implode(', ', $squares) . "\n";
    echo "Even numbers: " . implode(', ', $evenNumbers) . "\n";
    
    // Statistics
    $stats = calculateStats($numbers);
    echo "\nStatistics:\n";
    echo "Sum: {$stats['sum']}, Average: {$stats['average']}\n";
    echo "Min: {$stats['min']}, Max: {$stats['max']}\n";
    
    // Priority enum example
    echo "\nPriorities:\n";
    foreach (Priority::cases() as $priority) {
        echo "{$priority->name}: {$priority->label()} (value: {$priority->value})\n";
    }
    
    // Array functions
    $fruits = ['apple', 'banana', 'cherry', 'date'];
    echo "\nFruits: " . implode(', ', $fruits) . "\n";
    echo "Uppercase: " . implode(', ', array_map('strtoupper', $fruits)) . "\n";
    
    // Associative arrays
    $scores = ['Alice' => 95, 'Bob' => 87, 'Charlie' => 92];
    echo "\nScores:\n";
    foreach ($scores as $name => $score) {
        echo "$name: $score\n";
    }
}

main();
?> 