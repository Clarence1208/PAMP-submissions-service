package com.example.sample;

import java.util.*;
import java.util.stream.Collectors;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

// Record class (Java 14+)
public record Person(String name, int age, String email) {
    // Compact constructor with validation
    public Person {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Name cannot be null or empty");
        }
        if (age < 0) {
            throw new IllegalArgumentException("Age cannot be negative");
        }
    }
    
    // Additional method
    public boolean isAdult() {
        return age >= 18;
    }
    
    public String greet() {
        return String.format("Hello, %s! You are %d years old.", name, age);
    }
}

// Interface with default methods
interface Greetable {
    String greet();
    
    default String formalGreet() {
        return "Good day! " + greet();
    }
}

// Enum with methods
enum Priority {
    LOW(1), MEDIUM(2), HIGH(3), URGENT(4);
    
    private final int level;
    
    Priority(int level) {
        this.level = level;
    }
    
    public int getLevel() {
        return level;
    }
    
    public boolean isHigherThan(Priority other) {
        return this.level > other.level;
    }
}

// Task class
class Task {
    private final String title;
    private final Priority priority;
    private final LocalDateTime createdAt;
    private boolean completed;
    
    public Task(String title, Priority priority) {
        this.title = title;
        this.priority = priority;
        this.createdAt = LocalDateTime.now();
        this.completed = false;
    }
    
    // Getters
    public String getTitle() { return title; }
    public Priority getPriority() { return priority; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public boolean isCompleted() { return completed; }
    
    public void complete() {
        this.completed = true;
    }
    
    @Override
    public String toString() {
        return String.format("Task{title='%s', priority=%s, completed=%s}", 
                           title, priority, completed);
    }
}

public class SampleJava {
    public static void main(String[] args) {
        System.out.println("Java Programming Example");
        
        // Create people using records
        var people = List.of(
            new Person("Alice", 30, "alice@example.com"),
            new Person("Bob", 17, "bob@example.com"),
            new Person("Charlie", 35, "charlie@example.com"),
            new Person("Diana", 25, "diana@example.com")
        );
        
        System.out.println("\nAll people:");
        people.forEach(person -> System.out.println(person.greet()));
        
        // Stream API examples
        System.out.println("\nAdults only:");
        var adults = people.stream()
                          .filter(Person::isAdult)
                          .collect(Collectors.toList());
        adults.forEach(person -> System.out.println(person.greet()));
        
        // Average age calculation
        var averageAge = people.stream()
                              .mapToInt(Person::age)
                              .average()
                              .orElse(0.0);
        System.out.printf("Average age: %.1f%n", averageAge);
        
        // Working with tasks
        var tasks = new ArrayList<Task>();
        tasks.add(new Task("Review code", Priority.HIGH));
        tasks.add(new Task("Write documentation", Priority.MEDIUM));
        tasks.add(new Task("Fix minor bug", Priority.LOW));
        tasks.add(new Task("Security patch", Priority.URGENT));
        
        System.out.println("\nAll tasks:");
        tasks.forEach(System.out::println);
        
        // Complete some tasks
        tasks.get(0).complete();
        tasks.get(2).complete();
        
        // Filter and sort tasks
        var incompleteTasks = tasks.stream()
                                 .filter(task -> !task.isCompleted())
                                 .sorted(Comparator.comparing(Task::getPriority, 
                                        Comparator.comparing(Priority::getLevel).reversed()))
                                 .collect(Collectors.toList());
        
        System.out.println("\nIncomplete tasks (by priority):");
        incompleteTasks.forEach(System.out::println);
        
        // Text blocks (Java 15+)
        var jsonTemplate = """
                {
                    "name": "%s",
                    "age": %d,
                    "email": "%s",
                    "timestamp": "%s"
                }
                """;
        
        var person = people.get(0);
        var json = String.format(jsonTemplate, 
                                person.name(), 
                                person.age(), 
                                person.email(),
                                LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        
        System.out.println("\nJSON representation:");
        System.out.println(json);
        
        // Switch expression (Java 14+)
        for (Priority priority : Priority.values()) {
            var description = switch (priority) {
                case LOW -> "Can be done later";
                case MEDIUM -> "Should be done soon";
                case HIGH -> "Important task";
                case URGENT -> "Drop everything and do this!";
            };
            System.out.printf("%s: %s%n", priority, description);
        }
    }
} 