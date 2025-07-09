-- Sample Haskell program
module Main where

import Data.List (sort, group)
import Data.Maybe (fromMaybe)

-- Data types
data Person = Person 
    { name :: String
    , age :: Int
    } deriving (Show, Eq)

-- Type synonyms
type People = [Person]
type Age = Int

-- Function definitions
greet :: Person -> String
greet (Person n a) = "Hello, " ++ n ++ "! You are " ++ show a ++ " years old."

-- Higher-order functions
filterAdults :: People -> People
filterAdults = filter (\p -> age p >= 18)

-- List comprehension
squares :: [Int] -> [Int]
squares xs = [x * x | x <- xs]

-- Recursive function
factorial :: Integer -> Integer
factorial 0 = 1
factorial n = n * factorial (n - 1)

-- Fibonacci with pattern matching
fibonacci :: Integer -> Integer
fibonacci 0 = 0
fibonacci 1 = 1
fibonacci n = fibonacci (n - 1) + fibonacci (n - 2)

-- Maybe type usage
findPerson :: String -> People -> Maybe Person
findPerson searchName people = 
    case filter (\p -> name p == searchName) people of
        [] -> Nothing
        (x:_) -> Just x

-- Fold examples
sumAges :: People -> Int
sumAges = foldr (\p acc -> age p + acc) 0

-- Custom data type with constructor
data Shape = Circle Float | Rectangle Float Float
    deriving (Show)

area :: Shape -> Float
area (Circle r) = pi * r * r
area (Rectangle w h) = w * h

-- IO and main function
main :: IO ()
main = do
    putStrLn "Haskell Programming Example"
    
    let people = [ Person "Alice" 30
                 , Person "Bob" 17
                 , Person "Charlie" 35
                 , Person "Diana" 25
                 ]
    
    putStrLn "All people:"
    mapM_ (putStrLn . greet) people
    
    putStrLn "\nAdults only:"
    mapM_ (putStrLn . greet) (filterAdults people)
    
    let numbers = [1, 2, 3, 4, 5]
    putStrLn $ "\nSquares of " ++ show numbers ++ ": " ++ show (squares numbers)
    
    putStrLn $ "Factorial of 5: " ++ show (factorial 5)
    putStrLn $ "Fibonacci of 10: " ++ show (fibonacci 10)
    
    let foundPerson = findPerson "Alice" people
    putStrLn $ "Found Alice: " ++ show foundPerson
    
    putStrLn $ "Sum of ages: " ++ show (sumAges people)
    
    let shapes = [Circle 5.0, Rectangle 3.0 4.0]
    putStrLn "Areas:"
    mapM_ (\s -> putStrLn $ show s ++ " has area " ++ show (area s)) shapes 