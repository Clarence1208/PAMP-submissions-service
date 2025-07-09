#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <string>

// Class with modern C++ features
class Person {
private:
    std::string name_;
    int age_;

public:
    Person(std::string name, int age) : name_(std::move(name)), age_(age) {}
    
    // Const member function
    const std::string& getName() const { return name_; }
    int getAge() const { return age_; }
    
    // Member function
    void greet() const {
        std::cout << "Hello, " << name_ << "! You are " << age_ << " years old.\n";
    }
};

// Template function
template<typename T>
void printVector(const std::vector<T>& vec) {
    std::cout << "Vector contents: ";
    for (const auto& item : vec) {
        std::cout << item << " ";
    }
    std::cout << "\n";
}

int main() {
    std::cout << "C++ Programming Example\n";
    
    // Smart pointers
    auto person1 = std::make_unique<Person>("Alice", 30);
    auto person2 = std::make_shared<Person>("Bob", 25);
    
    person1->greet();
    person2->greet();
    
    // STL containers and algorithms
    std::vector<int> numbers = {5, 2, 8, 1, 9};
    printVector(numbers);
    
    std::sort(numbers.begin(), numbers.end());
    std::cout << "Sorted: ";
    printVector(numbers);
    
    // Lambda expression
    auto isEven = [](int n) { return n % 2 == 0; };
    auto evenCount = std::count_if(numbers.begin(), numbers.end(), isEven);
    std::cout << "Even numbers count: " << evenCount << "\n";
    
    return 0;
} 