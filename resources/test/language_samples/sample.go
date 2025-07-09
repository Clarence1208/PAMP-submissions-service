package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"
)

// Struct with JSON tags
type Person struct {
	Name string `json:"name"`
	Age  int    `json:"age"`
}

// Interface
type Greeter interface {
	Greet() string
}

// Method on struct
func (p Person) Greet() string {
	return fmt.Sprintf("Hello, %s! You are %d years old.", p.Name, p.Age)
}

// Generic function (Go 1.18+)
func Map[T, U any](slice []T, fn func(T) U) []U {
	result := make([]U, len(slice))
	for i, v := range slice {
		result[i] = fn(v)
	}
	return result
}

// Worker function for goroutines
func worker(ctx context.Context, id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case job, ok := <-jobs:
			if !ok {
				return
			}
			fmt.Printf("Worker %d processing job %d\n", id, job)
			time.Sleep(100 * time.Millisecond)
			results <- job * 2
		case <-ctx.Done():
			fmt.Printf("Worker %d cancelled\n", id)
			return
		}
	}
}

func main() {
	fmt.Println("Go Programming Example")

	// Create a person
	person := Person{Name: "Alice", Age: 30}
	fmt.Println(person.Greet())

	// JSON marshaling/unmarshaling
	jsonData, err := json.Marshal(person)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("JSON: %s\n", jsonData)

	var decodedPerson Person
	if err := json.Unmarshal(jsonData, &decodedPerson); err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Decoded: %+v\n", decodedPerson)

	// Generic function usage
	numbers := []int{1, 2, 3, 4, 5}
	doubled := Map(numbers, func(n int) int { return n * 2 })
	fmt.Printf("Original: %v, Doubled: %v\n", numbers, doubled)

	// Goroutines and channels
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	jobs := make(chan int, 10)
	results := make(chan int, 10)
	var wg sync.WaitGroup

	// Start workers
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go worker(ctx, i, jobs, results, &wg)
	}

	// Send jobs
	go func() {
		for i := 1; i <= 5; i++ {
			jobs <- i
		}
		close(jobs)
	}()

	// Collect results
	go func() {
		wg.Wait()
		close(results)
	}()

	// Print results
	for result := range results {
		fmt.Printf("Result: %d\n", result)
	}

	fmt.Println("Program completed")
} 