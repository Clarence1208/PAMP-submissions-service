// Sample Groovy script

@groovy.transform.Immutable
class Person {
    String name
    int age
    
    String greet() {
        return "Hello, ${name}! You are ${age} years old."
    }
}

// Closure examples
def numbers = [1, 2, 3, 4, 5]
def doubled = numbers.collect { it * 2 }
def evenNumbers = numbers.findAll { it % 2 == 0 }

println "Groovy Programming Example"
println "Original numbers: ${numbers}"
println "Doubled: ${doubled}"
println "Even numbers: ${evenNumbers}"

// Create people
def people = [
    new Person('Alice', 30),
    new Person('Bob', 25),
    new Person('Charlie', 35)
]

// Groovy each and closures
println "\nPeople:"
people.each { person ->
    println person.greet()
}

// Find adults
def adults = people.findAll { it.age >= 30 }
println "\nAdults:"
adults.each { println "- ${it.name}" }

// Map example
def nameAgeMap = [:]
people.each { person ->
    nameAgeMap[person.name] = person.age
}
println "\nName-Age mapping: ${nameAgeMap}"

// String interpolation and multiline strings
def template = """
    <person>
        <name>${people[0].name}</name>
        <age>${people[0].age}</age>
    </person>
"""
println "\nXML Template:${template}"

// Range and spread operator
def range = 1..5
def squares = range.collect { it ** 2 }
println "Squares of 1-5: ${squares}"

// Elvis operator and safe navigation
def nullableName = null
def displayName = nullableName ?: "Unknown"
println "Display name: ${displayName}"

// Method with default parameters
def greetWithDefault(name = "World", enthusiasm = "!") {
    return "Hello, ${name}${enthusiasm}"
}

println greetWithDefault()
println greetWithDefault("Groovy")
println greetWithDefault("Groovy", "!!!")

// Builder pattern example
def builder = new groovy.xml.MarkupBuilder(new StringWriter())
def xml = builder.people {
    people.each { person ->
        person(id: person.name.toLowerCase()) {
            name(person.name)
            age(person.age)
        }
    }
}

println "\nBuilt XML structure" 