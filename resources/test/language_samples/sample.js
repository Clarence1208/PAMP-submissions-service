// Sample JavaScript with modern ES6+ features

// Class definition
class Person {
    #id; // Private field
    
    constructor(name, age, email) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.#id = Math.random().toString(36).substr(2, 9);
    }
    
    greet() {
        return `Hello, ${this.name}! You are ${this.age} years old.`;
    }
    
    get id() {
        return this.#id;
    }
    
    get isAdult() {
        return this.age >= 18;
    }
    
    // Static method
    static fromObject(obj) {
        return new Person(obj.name, obj.age, obj.email);
    }
}

// Async function
async function fetchUserData(userId) {
    try {
        // Simulated API call
        await new Promise(resolve => setTimeout(resolve, 100));
        return {
            id: userId,
            name: `User ${userId}`,
            age: Math.floor(Math.random() * 50) + 18
        };
    } catch (error) {
        console.error('Failed to fetch user data:', error);
        throw error;
    }
}

// Arrow functions and array methods
const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

const processNumbers = (nums) => {
    const doubled = nums.map(n => n * 2);
    const evenNumbers = nums.filter(n => n % 2 === 0);
    const sum = nums.reduce((acc, n) => acc + n, 0);
    
    return { doubled, evenNumbers, sum };
};

// Destructuring and spread operator
const people = [
    new Person('Alice', 30, 'alice@example.com'),
    new Person('Bob', 17, 'bob@example.com'),
    new Person('Charlie', 35, 'charlie@example.com'),
    new Person('Diana', 25, 'diana@example.com')
];

// Object destructuring
const [firstPerson, secondPerson, ...otherPeople] = people;

// Template literals and tagged templates
function highlight(strings, ...values) {
    return strings.reduce((result, string, i) => {
        const value = values[i] ? `<mark>${values[i]}</mark>` : '';
        return result + string + value;
    }, '');
}

// Set and Map
const uniqueAges = new Set(people.map(p => p.age));
const personMap = new Map(people.map(p => [p.id, p]));

// Symbol
const SECRET_KEY = Symbol('secret');
const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000,
    [SECRET_KEY]: 'super-secret-value'
};

// Proxy
const observableObject = new Proxy({}, {
    set(target, property, value) {
        console.log(`Setting ${property} to ${value}`);
        target[property] = value;
        return true;
    },
    get(target, property) {
        console.log(`Getting ${property}`);
        return target[property];
    }
});

// Generator function
function* fibonacci() {
    let [a, b] = [0, 1];
    while (true) {
        yield a;
        [a, b] = [b, a + b];
    }
}

// Main execution
async function main() {
    console.log('JavaScript Programming Example');
    
    // Basic array operations
    console.log('\nNumber processing:');
    const results = processNumbers(numbers);
    console.log('Doubled:', results.doubled);
    console.log('Even numbers:', results.evenNumbers);
    console.log('Sum:', results.sum);
    
    // People operations
    console.log('\nPeople:');
    people.forEach(person => console.log(person.greet()));
    
    // Filter adults
    const adults = people.filter(person => person.isAdult);
    console.log('\nAdults:', adults.map(p => p.name));
    
    // Destructuring example
    console.log('\nFirst person:', firstPerson.name);
    console.log('Other people:', otherPeople.map(p => p.name));
    
    // Template literal
    const message = highlight`Welcome ${firstPerson.name}, you are ${firstPerson.age} years old!`;
    console.log('\nHighlighted message:', message);
    
    // Set and Map operations
    console.log('\nUnique ages:', Array.from(uniqueAges).sort((a, b) => a - b));
    console.log('Person map size:', personMap.size);
    
    // Async operations
    console.log('\nFetching user data...');
    try {
        const userData = await fetchUserData(123);
        console.log('Fetched:', userData);
    } catch (error) {
        console.error('Error:', error.message);
    }
    
    // Generator usage
    console.log('\nFirst 10 Fibonacci numbers:');
    const fib = fibonacci();
    const fibNumbers = Array.from({ length: 10 }, () => fib.next().value);
    console.log(fibNumbers);
    
    // Proxy example
    console.log('\nProxy example:');
    observableObject.name = 'Test';
    console.log('Retrieved:', observableObject.name);
    
    // Optional chaining and nullish coalescing
    const user = {
        profile: {
            preferences: {
                theme: 'dark'
            }
        }
    };
    
    const theme = user?.profile?.preferences?.theme ?? 'light';
    console.log('\nUser theme:', theme);
    
    // Promise.all example
    const userIds = [1, 2, 3];
    try {
        const users = await Promise.all(
            userIds.map(id => fetchUserData(id))
        );
        console.log('\nAll users:', users);
    } catch (error) {
        console.error('Failed to fetch all users:', error);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Person, processNumbers, fibonacci };
} else {
    // Browser environment
    main().catch(console.error);
} 