#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Structure definition
typedef struct {
    char name[50];
    int age;
} Person;

// Function prototypes
void greet(const Person *person);
int factorial(int n);

int main() {
    printf("C Programming Example\n");
    
    // Create a person
    Person person = {"Alice", 30};
    greet(&person);
    
    // Calculate factorial
    int n = 5;
    int result = factorial(n);
    printf("Factorial of %d is %d\n", n, result);
    
    // Dynamic memory allocation
    int *numbers = malloc(3 * sizeof(int));
    if (numbers != NULL) {
        numbers[0] = 1;
        numbers[1] = 2;
        numbers[2] = 3;
        
        printf("Numbers: ");
        for (int i = 0; i < 3; i++) {
            printf("%d ", numbers[i]);
        }
        printf("\n");
        
        free(numbers);
    }
    
    return 0;
}

void greet(const Person *person) {
    printf("Hello, %s! You are %d years old.\n", person->name, person->age);
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
} 