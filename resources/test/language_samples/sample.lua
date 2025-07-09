-- Sample Lua program

-- Table-based "class" definition
local Person = {}
Person.__index = Person

function Person:new(name, age, email)
    local obj = {
        name = name or "",
        age = age or 0,
        email = email or ""
    }
    setmetatable(obj, self)
    return obj
end

function Person:greet()
    return string.format("Hello, %s! You are %d years old.", self.name, self.age)
end

function Person:isAdult()
    return self.age >= 18
end

-- Table for utility functions
local Utils = {}

function Utils.map(tbl, func)
    local result = {}
    for i, v in ipairs(tbl) do
        result[i] = func(v)
    end
    return result
end

function Utils.filter(tbl, predicate)
    local result = {}
    for i, v in ipairs(tbl) do
        if predicate(v) then
            table.insert(result, v)
        end
    end
    return result
end

function Utils.reduce(tbl, func, initial)
    local result = initial
    for i, v in ipairs(tbl) do
        result = func(result, v)
    end
    return result
end

function Utils.forEach(tbl, func)
    for i, v in ipairs(tbl) do
        func(v, i)
    end
end

-- Closure example
function createCounter(initial)
    local count = initial or 0
    return function(increment)
        count = count + (increment or 1)
        return count
    end
end

-- Coroutine example
function fibonacci()
    local a, b = 0, 1
    return coroutine.create(function()
        while true do
            coroutine.yield(a)
            a, b = b, a + b
        end
    end)
end

-- Metatables example
local Vector = {}
Vector.__index = Vector

function Vector:new(x, y)
    return setmetatable({x = x or 0, y = y or 0}, self)
end

function Vector.__add(v1, v2)
    return Vector:new(v1.x + v2.x, v1.y + v2.y)
end

function Vector.__mul(v, scalar)
    if type(v) == "number" then
        return Vector:new(scalar.x * v, scalar.y * v)
    else
        return Vector:new(v.x * scalar, v.y * scalar)
    end
end

function Vector:__tostring()
    return string.format("Vector(%.2f, %.2f)", self.x, self.y)
end

function Vector:magnitude()
    return math.sqrt(self.x^2 + self.y^2)
end

-- String processing functions
function string.split(str, delimiter)
    local result = {}
    local pattern = "(.-)" .. delimiter
    local lastEnd = 1
    local s, e, cap = str:find(pattern, 1)
    
    while s do
        if s ~= 1 or cap ~= "" then
            table.insert(result, cap)
        end
        lastEnd = e + 1
        s, e, cap = str:find(pattern, lastEnd)
    end
    
    if lastEnd <= #str then
        cap = str:sub(lastEnd)
        table.insert(result, cap)
    end
    
    return result
end

function string.trim(str)
    return str:match("^%s*(.-)%s*$")
end

-- Table serialization
function serializeTable(tbl, indent)
    indent = indent or 0
    local spacing = string.rep("  ", indent)
    local result = "{\n"
    
    for k, v in pairs(tbl) do
        result = result .. spacing .. "  "
        
        if type(k) == "string" then
            result = result .. string.format('"%s"', k)
        else
            result = result .. tostring(k)
        end
        
        result = result .. " = "
        
        if type(v) == "table" then
            result = result .. serializeTable(v, indent + 1)
        elseif type(v) == "string" then
            result = result .. string.format('"%s"', v)
        else
            result = result .. tostring(v)
        end
        
        result = result .. ",\n"
    end
    
    result = result .. spacing .. "}"
    return result
end

-- Main execution
function main()
    print("Lua Programming Example")
    
    -- Create people
    local people = {
        Person:new("Alice", 30, "alice@example.com"),
        Person:new("Bob", 17, "bob@example.com"),
        Person:new("Charlie", 35, "charlie@example.com"),
        Person:new("Diana", 25, "diana@example.com")
    }
    
    print("\nAll people:")
    Utils.forEach(people, function(person)
        print(person:greet())
    end)
    
    -- Filter adults
    local adults = Utils.filter(people, function(person)
        return person:isAdult()
    end)
    
    print("\nAdults:")
    Utils.forEach(adults, function(person)
        print("- " .. person.name)
    end)
    
    -- Map to names
    local names = Utils.map(people, function(person)
        return person.name
    end)
    
    print("\nNames: " .. table.concat(names, ", "))
    
    -- Reduce to total age
    local totalAge = Utils.reduce(people, function(sum, person)
        return sum + person.age
    end, 0)
    
    print(string.format("Total age: %d", totalAge))
    print(string.format("Average age: %.1f", totalAge / #people))
    
    -- Counter closure example
    print("\nCounter example:")
    local counter = createCounter(10)
    print("Counter: " .. counter())
    print("Counter: " .. counter(5))
    print("Counter: " .. counter())
    
    -- Coroutine example
    print("\nFibonacci sequence (first 10):")
    local fib = fibonacci()
    local fibNumbers = {}
    
    for i = 1, 10 do
        local success, value = coroutine.resume(fib)
        if success then
            table.insert(fibNumbers, value)
        end
    end
    
    print(table.concat(fibNumbers, ", "))
    
    -- Vector operations
    print("\nVector operations:")
    local v1 = Vector:new(3, 4)
    local v2 = Vector:new(1, 2)
    local v3 = v1 + v2
    local v4 = v1 * 2
    
    print("v1: " .. tostring(v1))
    print("v2: " .. tostring(v2))
    print("v1 + v2: " .. tostring(v3))
    print("v1 * 2: " .. tostring(v4))
    print("v1 magnitude: " .. string.format("%.2f", v1:magnitude()))
    
    -- String operations
    print("\nString operations:")
    local text = "  Hello, Lua World!  "
    local trimmed = text:trim()
    local words = trimmed:split(" ")
    
    print("Original: '" .. text .. "'")
    print("Trimmed: '" .. trimmed .. "'")
    print("Words: " .. table.concat(words, " | "))
    
    -- Table serialization
    print("\nTable serialization:")
    local data = {
        name = "Sample Data",
        numbers = {1, 2, 3, 4, 5},
        person = {
            name = "John",
            age = 30,
            active = true
        }
    }
    
    print(serializeTable(data))
    
    -- Table as associative array
    local scores = {}
    scores["Alice"] = 95
    scores["Bob"] = 87
    scores["Charlie"] = 92
    
    print("\nScores:")
    for name, score in pairs(scores) do
        print(string.format("%s: %d", name, score))
    end
end

-- Run main function
main() 