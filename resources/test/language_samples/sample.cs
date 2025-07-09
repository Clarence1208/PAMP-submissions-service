using System;
using System.Collections.Generic;
using System.Linq;

namespace SampleCSharp
{
    // Record type (C# 9+)
    public record Person(string Name, int Age);
    
    // Interface
    public interface IGreeter
    {
        void Greet(Person person);
    }
    
    // Class implementing interface
    public class ConsoleGreeter : IGreeter
    {
        public void Greet(Person person)
        {
            Console.WriteLine($"Hello, {person.Name}! You are {person.Age} years old.");
        }
    }
    
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("C# Programming Example");
            
            // Create people
            var people = new List<Person>
            {
                new("Alice", 30),
                new("Bob", 25),
                new("Charlie", 35)
            };
            
            // Use interface
            IGreeter greeter = new ConsoleGreeter();
            
            // LINQ query
            var adults = people.Where(p => p.Age >= 30).ToList();
            
            Console.WriteLine("Adults:");
            foreach (var person in adults)
            {
                greeter.Greet(person);
            }
            
            // Lambda expression
            var averageAge = people.Average(p => p.Age);
            Console.WriteLine($"Average age: {averageAge:F1}");
        }
    }
} 