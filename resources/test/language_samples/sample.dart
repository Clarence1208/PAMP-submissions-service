// Sample Dart program

import 'dart:async';
import 'dart:math';

// Abstract class
abstract class Animal {
  String get name;
  void makeSound();
}

// Mixin
mixin Flyable {
  void fly() {
    print('Flying high!');
  }
}

// Class with inheritance and mixin
class Bird extends Animal with Flyable {
  @override
  final String name;
  
  Bird(this.name);
  
  @override
  void makeSound() {
    print('$name says: Tweet tweet!');
  }
}

// Generic class
class Repository<T> {
  final List<T> _items = [];
  
  void add(T item) {
    _items.add(item);
  }
  
  List<T> getAll() => List.unmodifiable(_items);
  
  T? findById(bool Function(T) predicate) {
    try {
      return _items.firstWhere(predicate);
    } catch (e) {
      return null;
    }
  }
}

// Record (Dart 3+)
typedef Person = ({String name, int age});

// Extension
extension PersonExtension on Person {
  String get greeting => 'Hello, $name! You are $age years old.';
  bool get isAdult => age >= 18;
}

void main() async {
  print('Dart Programming Example');
  
  // Create a bird
  final bird = Bird('Robin');
  bird.makeSound();
  bird.fly();
  
  // Use repository
  final personRepo = Repository<Person>();
  personRepo.add((name: 'Alice', age: 30));
  personRepo.add((name: 'Bob', age: 25));
  
  // Find person
  final alice = personRepo.findById((p) => p.name == 'Alice');
  if (alice != null) {
    print(alice.greeting);
    print('Is adult: ${alice.isAdult}');
  }
  
  // Async example
  await performAsyncTask();
  
  // Collection operations
  final numbers = [1, 2, 3, 4, 5];
  final doubled = numbers.map((n) => n * 2).toList();
  final evenNumbers = numbers.where((n) => n % 2 == 0).toList();
  
  print('Original: $numbers');
  print('Doubled: $doubled');
  print('Even: $evenNumbers');
  
  // Pattern matching (Dart 3+)
  final random = Random().nextInt(3);
  final result = switch (random) {
    0 => 'Zero',
    1 => 'One',
    _ => 'Other'
  };
  print('Random result: $result');
}

Future<void> performAsyncTask() async {
  print('Starting async task...');
  await Future.delayed(Duration(milliseconds: 100));
  print('Async task completed!');
} 