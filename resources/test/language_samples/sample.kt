// Sample Kotlin program

import kotlinx.coroutines.*
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

// Data class
data class Person(
    val name: String,
    val age: Int,
    val email: String? = null
) {
    fun greet(): String = "Hello, $name! You are $age years old."
    
    val isAdult: Boolean
        get() = age >= 18
    
    companion object {
        fun fromMap(map: Map<String, Any>): Person {
            return Person(
                name = map["name"] as String,
                age = map["age"] as Int,
                email = map["email"] as? String
            )
        }
    }
}

// Sealed class for representing different states
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Throwable) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// Interface with default implementation
interface Greetable {
    fun greet(): String
    
    fun formalGreet(): String = "Good day! ${greet()}"
}

// Extension functions
fun String.toCamelCase(): String {
    return this.split(" ")
        .mapIndexed { index, word ->
            if (index == 0) word.lowercase()
            else word.lowercase().replaceFirstChar { it.uppercase() }
        }
        .joinToString("")
}

fun List<Person>.adults(): List<Person> = this.filter { it.isAdult }

fun <T> List<T>.second(): T? = if (size >= 2) this[1] else null

// Generic class
class Repository<T> {
    private val items = mutableListOf<T>()
    
    fun add(item: T) {
        items.add(item)
    }
    
    fun getAll(): List<T> = items.toList()
    
    fun find(predicate: (T) -> Boolean): T? = items.find(predicate)
    
    fun count(): Int = items.size
}

// Enum class with properties
enum class Priority(val level: Int, val description: String) {
    LOW(1, "Can be done later"),
    MEDIUM(2, "Should be done soon"),
    HIGH(3, "Important task"),
    URGENT(4, "Drop everything and do this!");
    
    fun isHigherThan(other: Priority): Boolean = this.level > other.level
    
    companion object {
        fun fromLevel(level: Int): Priority? = values().find { it.level == level }
    }
}

// Object (singleton)
object Utils {
    fun formatDateTime(dateTime: LocalDateTime): String {
        return dateTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
    }
    
    fun <T> List<T>.chunked(size: Int): List<List<T>> {
        return this.windowed(size, size, true)
    }
}

// Suspend function for coroutines
suspend fun fetchUserData(userId: Int): Result<Person> {
    delay(100) // Simulate network delay
    
    return try {
        val userData = mapOf(
            "name" to "User $userId",
            "age" to (18..65).random(),
            "email" to "user$userId@example.com"
        )
        Result.Success(Person.fromMap(userData))
    } catch (e: Exception) {
        Result.Error(e)
    }
}

// Higher-order functions
fun <T, R> List<T>.mapNotNull(transform: (T) -> R?): List<R> {
    val result = mutableListOf<R>()
    for (item in this) {
        transform(item)?.let { result.add(it) }
    }
    return result
}

// Main function with coroutines
fun main() = runBlocking {
    println("Kotlin Programming Example")
    
    // Create people
    val people = listOf(
        Person("Alice", 30, "alice@example.com"),
        Person("Bob", 17),
        Person("Charlie", 35, "charlie@example.com"),
        Person("Diana", 25, "diana@example.com")
    )
    
    println("\nAll people:")
    people.forEach { println(it.greet()) }
    
    // Extension function usage
    val adults = people.adults()
    println("\nAdults:")
    adults.forEach { println("- ${it.name}") }
    
    // Safe calls and elvis operator
    val secondPerson = people.second()
    val secondEmail = secondPerson?.email ?: "No email provided"
    println("\nSecond person email: $secondEmail")
    
    // String extension
    val camelCase = "hello world kotlin".toCamelCase()
    println("Camel case: $camelCase")
    
    // Repository usage
    val personRepo = Repository<Person>()
    people.forEach { personRepo.add(it) }
    
    val foundPerson = personRepo.find { it.name == "Alice" }
    println("\nFound person: ${foundPerson?.name}")
    
    // Enum usage
    val priorities = Priority.values()
    println("\nPriorities:")
    priorities.forEach { priority ->
        println("${priority.name}: ${priority.description} (level ${priority.level})")
    }
    
    // When expression with sealed class
    suspend fun handleResult(result: Result<Person>) {
        when (result) {
            is Result.Success -> {
                println("Successfully fetched: ${result.data.name}")
            }
            is Result.Error -> {
                println("Error occurred: ${result.exception.message}")
            }
            is Result.Loading -> {
                println("Loading...")
            }
        }
    }
    
    // Coroutines and async operations
    println("\nFetching user data asynchronously:")
    val userIds = listOf(1, 2, 3)
    
    val deferredResults = userIds.map { userId ->
        async { fetchUserData(userId) }
    }
    
    val results = deferredResults.awaitAll()
    results.forEach { result ->
        handleResult(result)
    }
    
    // Collections and functional programming
    val numbers = (1..10).toList()
    val evenSquares = numbers
        .filter { it % 2 == 0 }
        .map { it * it }
    
    println("\nEven squares: $evenSquares")
    
    // Destructuring
    val (name, age) = people.first()
    println("\nDestructured first person: $name, $age")
    
    // Scope functions
    val personInfo = people.first().let { person ->
        buildString {
            append("Name: ${person.name}\n")
            append("Age: ${person.age}\n")
            append("Email: ${person.email ?: "Not provided"}\n")
            append("Adult: ${person.isAdult}")
        }
    }
    
    println("\nPerson info:")
    println(personInfo)
    
    // Utils object usage
    val currentTime = LocalDateTime.now()
    val formattedTime = Utils.formatDateTime(currentTime)
    println("\nCurrent time: $formattedTime")
} 