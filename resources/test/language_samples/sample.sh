#!/bin/bash

# Sample Bash script
set -e

# Variables
name="World"
count=5

# Function definition
greet() {
    local person=$1
    echo "Hello, $person!"
}

# Main logic
echo "Bash Script Example"
greet "$name"

# Loop example
for i in $(seq 1 $count); do
    echo "Count: $i"
done

# Conditional example
if [ "$count" -gt 3 ]; then
    echo "Count is greater than 3"
else
    echo "Count is 3 or less"
fi

# Array example
fruits=("apple" "banana" "orange")
for fruit in "${fruits[@]}"; do
    echo "Fruit: $fruit"
done 