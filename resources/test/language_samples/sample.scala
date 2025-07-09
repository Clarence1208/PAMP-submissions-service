// Scala Sample Program - Demonstrating functional and object-oriented programming
// This program showcases various Scala language features including:
// - Object-oriented programming with classes and traits
// - Functional programming with higher-order functions
// - Pattern matching and case classes
// - Collections and immutable data structures
// - Concurrent programming with Futures

import scala.concurrent.{Future, ExecutionContext}
import scala.util.{Try, Success, Failure, Random}
import scala.collection.mutable
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

// Implicit execution context for Future operations
implicit val ec: ExecutionContext = ExecutionContext.global

// Sealed trait for algebraic data types
sealed trait Shape {
  def area: Double
  def perimeter: Double
}

// Case classes for different shapes
case class Circle(radius: Double) extends Shape {
  def area: Double = math.Pi * radius * radius
  def perimeter: Double = 2 * math.Pi * radius
  
  override def toString: String = s"Circle(radius=$radius)"
}

case class Rectangle(width: Double, height: Double) extends Shape {
  def area: Double = width * height
  def perimeter: Double = 2 * (width + height)
  
  override def toString: String = s"Rectangle(width=$width, height=$height)"
}

case class Triangle(base: Double, height: Double, side1: Double, side2: Double) extends Shape {
  def area: Double = 0.5 * base * height
  def perimeter: Double = base + side1 + side2
  
  override def toString: String = s"Triangle(base=$base, height=$height)"
}

// Trait for objects that can be measured
trait Measurable {
  def dimensions: Map[String, Double]
}

// Abstract class demonstrating inheritance
abstract class Animal(val name: String, val species: String) {
  def makeSound: String
  def description: String = s"$name is a $species"
  
  // Abstract method to be implemented by subclasses
  def habitat: String
}

// Concrete implementations
class Dog(name: String, val breed: String) extends Animal(name, "Canis lupus") {
  def makeSound: String = "Woof! Woof!"
  def habitat: String = "Domestic environment"
  
  def fetch(item: String): String = s"$name is fetching the $item!"
  
  override def description: String = s"${super.description} of breed $breed"
}

class Cat(name: String, val isIndoor: Boolean) extends Animal(name, "Felis catus") {
  def makeSound: String = "Meow! Purr..."
  def habitat: String = if (isIndoor) "Indoor" else "Indoor/Outdoor"
  
  def purr(): String = s"$name is purring contentedly..."
}

// Case class for immutable data
case class Person(firstName: String, lastName: String, age: Int, email: String) {
  def fullName: String = s"$firstName $lastName"
  def isAdult: Boolean = age >= 18
  
  // Copy method is automatically generated for case classes
  def withAge(newAge: Int): Person = this.copy(age = newAge)
}

// Companion object with factory methods
object Person {
  def apply(fullName: String, age: Int, email: String): Person = {
    val parts = fullName.split(" ", 2)
    Person(parts(0), parts.lift(1).getOrElse(""), age, email)
  }
  
  def fromEmail(email: String, age: Int): Person = {
    val username = email.split("@")(0)
    val parts = username.split("[._]")
    Person(parts(0).capitalize, parts.lift(1).map(_.capitalize).getOrElse(""), age, email)
  }
}

// Generic class demonstrating type parameters
class GenericContainer[T](private var value: T) {
  def get: T = value
  def set(newValue: T): Unit = value = newValue
  def transform[U](f: T => U): GenericContainer[U] = new GenericContainer(f(value))
  
  override def toString: String = s"Container($value)"
}

// Object with utility functions
object MathUtils {
  def fibonacci(n: Int): BigInt = {
    @annotation.tailrec
    def fibHelper(n: Int, prev: BigInt, curr: BigInt): BigInt = {
      if (n <= 0) prev
      else fibHelper(n - 1, curr, prev + curr)
    }
    fibHelper(n, 0, 1)
  }
  
  def factorial(n: Int): BigInt = {
    if (n <= 1) 1
    else (2 to n).map(BigInt(_)).product
  }
  
  def isPrime(n: Int): Boolean = {
    if (n <= 1) false
    else if (n <= 3) true
    else if (n % 2 == 0 || n % 3 == 0) false
    else {
      val sqrt = math.sqrt(n).toInt
      (5 to sqrt by 6).forall(i => n % i != 0 && n % (i + 2) != 0)
    }
  }
}

// Option and error handling
object FileProcessor {
  def readFile(filename: String): Option[String] = {
    Try {
      scala.io.Source.fromFile(filename).getLines().mkString("\n")
    }.toOption
  }
  
  def processContent(content: String): Either[String, List[String]] = {
    if (content.trim.isEmpty) {
      Left("Content is empty")
    } else {
      Right(content.split("\\n").toList.filter(_.nonEmpty))
    }
  }
}

// Future-based asynchronous operations
object AsyncOperations {
  def simulateNetworkCall(delay: Int): Future[String] = {
    Future {
      Thread.sleep(delay)
      s"Network response after ${delay}ms"
    }
  }
  
  def processDataAsync(data: List[Int]): Future[List[Int]] = {
    Future {
      data.map(_ * 2).filter(_ > 10)
    }
  }
}

// Pattern matching examples
object PatternMatchingExamples {
  def describeValue(value: Any): String = value match {
    case s: String if s.length > 10 => s"Long string: ${s.take(10)}..."
    case s: String => s"String: $s"
    case i: Int if i > 0 => s"Positive integer: $i"
    case i: Int if i < 0 => s"Negative integer: $i"
    case 0 => "Zero"
    case list: List[_] if list.isEmpty => "Empty list"
    case list: List[_] => s"List with ${list.length} elements"
    case Some(value) => s"Option with value: $value"
    case None => "Empty option"
    case _ => "Unknown type"
  }
  
  def processShape(shape: Shape): String = shape match {
    case Circle(r) if r > 10 => s"Large circle with area ${shape.area:.2f}"
    case Circle(r) => s"Small circle with area ${shape.area:.2f}"
    case Rectangle(w, h) if w == h => s"Square with area ${shape.area:.2f}"
    case Rectangle(w, h) => s"Rectangle ${w}x${h} with area ${shape.area:.2f}"
    case Triangle(b, h, _, _) => s"Triangle with base $b, height $h, area ${shape.area:.2f}"
  }
}

// Main application object
object ScalaSampleApp extends App {
  println("=== Scala Sample Program ===")
  println()
  
  // Object-oriented programming
  println("--- Object-Oriented Programming ---")
  val dog = new Dog("Buddy", "Golden Retriever")
  val cat = new Cat("Whiskers", true)
  
  println(dog.description)
  println(s"Dog says: ${dog.makeSound}")
  println(dog.fetch("ball"))
  println()
  
  println(cat.description)
  println(s"Cat says: ${cat.makeSound}")
  println(cat.purr())
  println()
  
  // Case classes and immutable data
  println("--- Case Classes and Immutable Data ---")
  val person1 = Person("John", "Doe", 30, "john.doe@example.com")
  val person2 = Person.fromEmail("jane.smith@example.com", 25)
  
  println(s"Person 1: ${person1.fullName}, Age: ${person1.age}, Adult: ${person1.isAdult}")
  println(s"Person 2: ${person2.fullName}, Age: ${person2.age}, Adult: ${person2.isAdult}")
  
  val olderPerson1 = person1.withAge(31)
  println(s"Person 1 after birthday: ${olderPerson1.fullName}, Age: ${olderPerson1.age}")
  println()
  
  // Collections and functional programming
  println("--- Collections and Functional Programming ---")
  val numbers = List(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
  
  val evenNumbers = numbers.filter(_ % 2 == 0)
  val squaredNumbers = numbers.map(x => x * x)
  val sum = numbers.reduce(_ + _)
  val product = numbers.filter(_ <= 5).product
  
  println(s"Original numbers: $numbers")
  println(s"Even numbers: $evenNumbers")
  println(s"Squared numbers: $squaredNumbers")
  println(s"Sum: $sum")
  println(s"Product of numbers <= 5: $product")
  
  // Higher-order functions
  val names = List("alice", "bob", "charlie", "diana")
  val capitalizedNames = names.map(_.capitalize)
  val longNames = names.filter(_.length > 4)
  val namesByLength = names.groupBy(_.length)
  
  println(s"Capitalized names: $capitalizedNames")
  println(s"Long names: $longNames")
  println(s"Names by length: $namesByLength")
  println()
  
  // Pattern matching
  println("--- Pattern Matching ---")
  val shapes = List(
    Circle(5.0),
    Rectangle(4.0, 6.0),
    Rectangle(5.0, 5.0),
    Triangle(3.0, 4.0, 5.0, 4.0)
  )
  
  shapes.foreach { shape =>
    println(PatternMatchingExamples.processShape(shape))
  }
  println()
  
  val values: List[Any] = List("Hello", 42, -5, 0, List(1, 2, 3), List(), Some("test"), None)
  values.foreach { value =>
    println(PatternMatchingExamples.describeValue(value))
  }
  println()
  
  // Math utilities
  println("--- Mathematical Operations ---")
  println(s"Fibonacci(10): ${MathUtils.fibonacci(10)}")
  println(s"Factorial(8): ${MathUtils.factorial(8)}")
  println(s"Prime numbers from 1 to 20: ${(1 to 20).filter(MathUtils.isPrime)}")
  println()
  
  // Generic containers
  println("--- Generic Programming ---")
  val intContainer = new GenericContainer(42)
  val stringContainer = intContainer.transform(_.toString)
  val doubleContainer = intContainer.transform(_.toDouble)
  
  println(s"Int container: $intContainer")
  println(s"String container: $stringContainer")
  println(s"Double container: $doubleContainer")
  println()
  
  // Option and Either examples
  println("--- Option and Either ---")
  val optionalValue: Option[String] = Some("Hello, Scala!")
  val emptyOption: Option[String] = None
  
  println(s"Optional value: ${optionalValue.getOrElse("Default")}")
  println(s"Empty option: ${emptyOption.getOrElse("Default")}")
  
  val result: Either[String, Int] = Try(42 / 2).map(Right(_)).getOrElse(Left("Division error"))
  result match {
    case Right(value) => println(s"Success: $value")
    case Left(error) => println(s"Error: $error")
  }
  println()
  
  // For comprehensions
  println("--- For Comprehensions ---")
  val pairs = for {
    x <- 1 to 3
    y <- 1 to 3
    if x != y
  } yield (x, y)
  
  println(s"Pairs where x != y: $pairs")
  
  val nestedList = List(List(1, 2), List(3, 4), List(5, 6))
  val flattened = for {
    sublist <- nestedList
    element <- sublist
  } yield element * 2
  
  println(s"Flattened and doubled: $flattened")
  println()
  
  // Async operations (simplified for demo)
  println("--- Asynchronous Operations ---")
  val futureResult = AsyncOperations.processDataAsync(List(1, 2, 5, 8, 12, 15))
  
  futureResult.onComplete {
    case Success(result) => println(s"Async processing result: $result")
    case Failure(exception) => println(s"Async processing failed: ${exception.getMessage}")
  }
  
  // Wait a bit for async operation to complete
  Thread.sleep(100)
  
  println()
  println("Program completed successfully!")
} 