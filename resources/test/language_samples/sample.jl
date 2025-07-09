# Sample Julia program

# Define a struct
struct Person
    name::String
    age::Int
    email::String
end

# Constructor method
function Person(name::String, age::Int)
    Person(name, age, "")
end

# Define a method for the struct
function greet(person::Person)
    return "Hello, $(person.name)! You are $(person.age) years old."
end

# Multiple dispatch example
function process(x::Int)
    return x^2
end

function process(x::Float64)
    return sqrt(x)
end

function process(x::String)
    return uppercase(x)
end

# Generic function
function mymap(f, arr::Vector{T}) where T
    result = T[]
    for item in arr
        push!(result, f(item))
    end
    return result
end

# Macro definition
macro time_it(expr)
    quote
        start_time = time()
        result = $(esc(expr))
        elapsed = time() - start_time
        println("Execution time: $(elapsed) seconds")
        result
    end
end

# Fibonacci with memoization
const fib_cache = Dict{Int, Int}()

function fibonacci(n::Int)
    if n in keys(fib_cache)
        return fib_cache[n]
    end
    
    if n ≤ 2
        result = 1
    else
        result = fibonacci(n-1) + fibonacci(n-2)
    end
    
    fib_cache[n] = result
    return result
end

# Matrix operations
function matrix_operations()
    # Create matrices
    A = [1 2 3; 4 5 6; 7 8 9]
    B = rand(3, 3)
    
    println("Matrix A:")
    display(A)
    
    println("\nMatrix B (random):")
    display(B)
    
    # Matrix operations
    C = A * B
    println("\nA * B:")
    display(C)
    
    # Element-wise operations
    D = A .+ B
    println("\nA .+ B (element-wise):")
    display(D)
    
    return A, B, C, D
end

# Type-stable function
function sum_of_squares(arr::Vector{T})::T where T<:Number
    total = zero(T)
    for x in arr
        total += x^2
    end
    return total
end

# Main execution
function main()
    println("Julia Programming Example")
    
    # Create people
    people = [
        Person("Alice", 30, "alice@example.com"),
        Person("Bob", 25),
        Person("Charlie", 35, "charlie@example.com"),
        Person("Diana", 28, "diana@example.com")
    ]
    
    println("\nPeople:")
    for person in people
        println(greet(person))
    end
    
    # Multiple dispatch examples
    println("\nMultiple dispatch:")
    println("process(5) = $(process(5))")
    println("process(16.0) = $(process(16.0))")
    println("process(\"hello\") = $(process("hello"))")
    
    # Array comprehensions
    numbers = [1, 2, 3, 4, 5]
    squares = [x^2 for x in numbers]
    even_squares = [x^2 for x in numbers if x % 2 == 0]
    
    println("\nArray comprehensions:")
    println("Numbers: $numbers")
    println("Squares: $squares")
    println("Even squares: $even_squares")
    
    # Generic function usage
    doubled = mymap(x -> x * 2, numbers)
    println("Doubled: $doubled")
    
    # String processing
    names = [person.name for person in people]
    uppercase_names = mymap(uppercase, names)
    println("Uppercase names: $uppercase_names")
    
    # Fibonacci sequence
    println("\nFibonacci sequence:")
    fib_numbers = [fibonacci(i) for i in 1:10]
    println("First 10 Fibonacci numbers: $fib_numbers")
    
    # Matrix operations
    println("\nMatrix operations:")
    @time_it matrix_operations()
    
    # Type-stable function
    float_array = [1.0, 2.0, 3.0, 4.0, 5.0]
    int_array = [1, 2, 3, 4, 5]
    
    println("\nSum of squares:")
    println("Float array: $(sum_of_squares(float_array))")
    println("Int array: $(sum_of_squares(int_array))")
    
    # Broadcasting
    println("\nBroadcasting:")
    matrix = [1 2 3; 4 5 6]
    result = matrix .+ 10
    println("Matrix + 10:")
    display(result)
    
    # Filter and map
    adults = filter(p -> p.age >= 25, people)
    adult_names = map(p -> p.name, adults)
    println("\nAdults: $adult_names")
end

# Run main if this is the main file
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end 