# Sample R program

# Load libraries
library(ggplot2)
suppressWarnings(library(dplyr))

# Define functions
greet_person <- function(name, age) {
  sprintf("Hello, %s! You are %d years old.", name, age)
}

is_adult <- function(age) {
  age >= 18
}

calculate_stats <- function(data) {
  list(
    mean = mean(data),
    median = median(data),
    sd = sd(data),
    min = min(data),
    max = max(data),
    iqr = IQR(data)
  )
}

# Main execution
main <- function() {
  cat("R Programming Example\n\n")
  
  # Create data frame
  people <- data.frame(
    name = c("Alice", "Bob", "Charlie", "Diana"),
    age = c(30, 17, 35, 25),
    email = c("alice@example.com", "bob@example.com", 
              "charlie@example.com", "diana@example.com"),
    stringsAsFactors = FALSE
  )
  
  cat("People data:\n")
  print(people)
  
  # Apply functions
  cat("\nGreetings:\n")
  for(i in 1:nrow(people)) {
    cat(greet_person(people$name[i], people$age[i]), "\n")
  }
  
  # Filter adults using vectorized operations
  adults <- people[is_adult(people$age), ]
  cat("\nAdults:\n")
  print(adults[c("name", "age")])
  
  # Vector operations
  numbers <- 1:10
  squares <- numbers^2
  even_numbers <- numbers[numbers %% 2 == 0]
  
  cat("\nNumbers:", numbers, "\n")
  cat("Squares:", squares, "\n")
  cat("Even numbers:", even_numbers, "\n")
  
  # Statistics
  stats <- calculate_stats(people$age)
  cat("\nAge statistics:\n")
  for(name in names(stats)) {
    cat(sprintf("  %s: %.2f\n", name, stats[[name]]))
  }
  
  # Using dplyr for data manipulation
  cat("\nUsing dplyr:\n")
  summary_stats <- people %>%
    filter(age >= 25) %>%
    summarise(
      count = n(),
      avg_age = mean(age),
      min_age = min(age),
      max_age = max(age)
    )
  print(summary_stats)
  
  # Create sample data for plotting
  set.seed(42)
  plot_data <- data.frame(
    x = rnorm(100, mean = 0, sd = 1),
    y = rnorm(100, mean = 0, sd = 1),
    group = sample(c("A", "B", "C"), 100, replace = TRUE)
  )
  
  # Basic plot
  cat("\nCreating plots...\n")
  
  # Histogram
  hist(plot_data$x, main = "Histogram of X", xlab = "X values", col = "lightblue")
  
  # Scatter plot with ggplot2
  p1 <- ggplot(plot_data, aes(x = x, y = y, color = group)) +
    geom_point() +
    geom_smooth(method = "lm", se = FALSE) +
    labs(title = "Scatter Plot by Group", x = "X values", y = "Y values") +
    theme_minimal()
  
  print(p1)
  
  # Box plot
  p2 <- ggplot(plot_data, aes(x = group, y = x, fill = group)) +
    geom_boxplot() +
    labs(title = "Box Plot by Group", x = "Group", y = "X values") +
    theme_minimal()
  
  print(p2)
  
  # Matrix operations
  cat("\nMatrix operations:\n")
  mat_a <- matrix(1:9, nrow = 3, ncol = 3)
  mat_b <- matrix(c(2, 0, 1, 1, 2, 0, 0, 1, 2), nrow = 3, ncol = 3)
  
  cat("Matrix A:\n")
  print(mat_a)
  cat("Matrix B:\n")
  print(mat_b)
  
  mat_mult <- mat_a %*% mat_b
  cat("A * B:\n")
  print(mat_mult)
  
  # Apply functions
  col_sums <- apply(mat_a, 2, sum)
  row_means <- apply(mat_a, 1, mean)
  
  cat("Column sums of A:", col_sums, "\n")
  cat("Row means of A:", row_means, "\n")
  
  # List operations
  my_list <- list(
    numbers = 1:5,
    characters = c("a", "b", "c"),
    logical = c(TRUE, FALSE, TRUE),
    matrix = matrix(1:6, nrow = 2)
  )
  
  cat("\nList structure:\n")
  str(my_list)
  
  # lapply example
  squared_numbers <- lapply(my_list$numbers, function(x) x^2)
  cat("Squared numbers:", unlist(squared_numbers), "\n")
  
  # String operations
  text <- "Hello R World"
  cat("\nString operations:\n")
  cat("Original:", text, "\n")
  cat("Uppercase:", toupper(text), "\n")
  cat("Lowercase:", tolower(text), "\n")
  cat("Length:", nchar(text), "\n")
  cat("Substring:", substr(text, 1, 5), "\n")
  
  # Factor operations
  grades <- factor(c("A", "B", "C", "A", "B", "A", "C", "B"))
  cat("\nFactor operations:\n")
  cat("Grades:", as.character(grades), "\n")
  cat("Levels:", levels(grades), "\n")
  cat("Table:\n")
  print(table(grades))
  
  cat("\nProgram completed successfully!\n")
}

# Run main function
main() 